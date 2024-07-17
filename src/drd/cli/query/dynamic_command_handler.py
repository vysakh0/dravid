import traceback
import click
from ...api.main import call_dravid_api
from ...utils import print_error, print_success, print_info, print_step, print_debug
from ...metadata.common_utils import generate_file_description
from ...prompts.error_resolution_prompt import get_error_resolution_prompt


def execute_commands(commands, executor, metadata_manager, is_fix=False, debug=False):
    all_outputs = []
    total_steps = len(commands)

    for i, cmd in enumerate(commands, 1):
        step_description = "fix" if is_fix else "command"
        print_step(i, total_steps,
                   f"Processing {cmd['type']} {step_description}...")

        if cmd['type'] == 'explanation':
            print_info(f"Explanation: {cmd['content']}")
            all_outputs.append(
                f"Step {i}/{total_steps}: Explanation - {cmd['content']}")
            continue

        try:
            if cmd['type'] == 'shell':
                output = handle_shell_command(cmd, executor)
                all_outputs.append(
                    f"Step {i}/{total_steps}: Shell command - {cmd['command']}\nOutput: {output}")
            elif cmd['type'] == 'file':
                output = handle_file_operation(cmd, executor, metadata_manager)
                all_outputs.append(
                    f"Step {i}/{total_steps}: File operation - {cmd['operation']} - {cmd['filename']} - {output}")
            elif cmd['type'] == 'metadata':
                print(cmd, "---")
                output = handle_metadata_operation(cmd, metadata_manager)
                all_outputs.append(
                    f"Step {i}/{total_steps}: Metadata operation - {cmd['operation']} - {output}")

            if debug:
                print_debug(f"Completed step {i}/{total_steps}")

        except Exception as e:
            error_message = f"Step {i}/{total_steps}: Error executing {step_description}: {cmd}\nError details: {str(e)}"
            print_error(error_message)
            all_outputs.append(error_message)
            return False, i, str(e), "\n".join(all_outputs)

    return True, total_steps, None, "\n".join(all_outputs)


def handle_shell_command(cmd, executor):
    print_info(f"Executing shell command: {cmd['command']}")
    output = executor.execute_shell_command(cmd['command'])
    if output is None:
        raise Exception(f"Command failed: {cmd['command']}")
    print_success(f"Successfully executed: {cmd['command']}")
    if output:
        click.echo(f"Command output:\n{output}")
    return output


def handle_file_operation(cmd, executor, metadata_manager):
    print_info(
        f"Performing file operation: {cmd['operation']} on {cmd['filename']}")
    operation_performed = executor.perform_file_operation(
        cmd['operation'],
        cmd['filename'],
        cmd.get('content'),
        force=True
    )
    if operation_performed:
        print_success(
            f"Successfully performed {cmd['operation']} on file: {cmd['filename']}")
        if cmd['operation'] in ['CREATE', 'UPDATE']:
            update_file_metadata(cmd, metadata_manager, executor)
        return "Success"
    else:
        raise Exception(
            f"File operation failed: {cmd['operation']} on {cmd['filename']}")


def handle_metadata_operation(cmd, metadata_manager):
    if cmd['operation'] == 'UPDATE_FILE':
        if metadata_manager.update_metadata_from_file():
            print_success(f"Updated metadata for file: {cmd['filename']}")
            return f"Updated metadata for {cmd['filename']}"
        else:
            raise Exception(
                f"Failed to update metadata for file: {cmd['filename']}")
    else:
        raise Exception(f"Unknown operation: {cmd['operation']}")


def update_file_metadata(cmd, metadata_manager, executor):
    project_context = metadata_manager.get_project_context()
    folder_structure = executor.get_folder_structure()
    file_type, description, exports = generate_file_description(
        cmd['filename'],
        cmd.get('content', ''),
        project_context,
        folder_structure
    )
    metadata_manager.update_file_metadata(
        cmd['filename'],
        file_type,
        cmd.get('content', ''),
        description,
        exports
    )


def handle_error_with_dravid(error, cmd, executor, metadata_manager, depth=0, previous_context="", debug=False):
    if depth > 3:
        print_error(
            "Max error handling depth reached. Unable to resolve the issue.")
        return False

    print_error(f"Error executing command: {error}")

    error_message = str(error)
    error_type = type(error).__name__
    error_trace = ''.join(traceback.format_exception(
        type(error), error, error.__traceback__))

    project_context = metadata_manager.get_project_context()
    error_query = get_error_resolution_prompt(
        previous_context, cmd, error_type, error_message, error_trace, project_context
    )

    print_info("Sending error information to dravid for analysis...")
    print_info("LLM calls to be made: 1")

    try:
        fix_commands = call_dravid_api(
            error_query, include_context=True)
    except ValueError as e:
        print_error(f"Error parsing dravid's response: {str(e)}")
        return False

    print_info("dravid's suggested fix:")
    print_info("Applying dravid's suggested fix...")

    fix_applied, step_completed, error_message, all_outputs = execute_commands(
        fix_commands, executor, metadata_manager, is_fix=True, debug=debug
    )

    if fix_applied:
        print_success("All fix steps successfully applied.")
        print_info("Fix application details:")
        click.echo(all_outputs)
        return True
    else:
        print_error(f"Failed to apply the fix at step {step_completed}.")
        print_error(f"Error message: {error_message}")
        print_info("Fix application details:")
        click.echo(all_outputs)

        return handle_error_with_dravid(
            Exception(error_message),
            {"type": "fix", "command": f"apply fix step {step_completed}"},
            executor,
            metadata_manager,
            depth + 1,
            all_outputs,
            debug
        )

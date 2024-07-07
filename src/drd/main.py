import click
import os
from dotenv import load_dotenv
from .claude_api import call_claude_api, generate_description
from .claude_parser import parse_claude_response, pretty_print_commands
from .executor import Executor
from .project_metadata import ProjectMetadataManager
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()


def print_step(step_number, total_steps, message):
    click.echo(
        f"{Fore.CYAN}[{step_number}/{total_steps}] {message}{Style.RESET_ALL}")


def print_success(message):
    click.echo(f"{Fore.GREEN}✔ {message}{Style.RESET_ALL}")


def print_error(message):
    click.echo(f"{Fore.RED}✘ {message}{Style.RESET_ALL}")


def print_info(message):
    click.echo(f"{Fore.YELLOW}ℹ {message}{Style.RESET_ALL}")


def get_file_content(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.read()
    return None


def create_drd_json_if_needed(directory):
    drd_json_path = os.path.join(directory, 'drd.json')
    if not os.path.exists(drd_json_path):
        if click.confirm("No drd.json found. Do you want to create one?"):
            metadata_manager = ProjectMetadataManager(directory)
            metadata_manager.save_metadata({
                "project_name": os.path.basename(directory),
                "last_updated": "",
                "files": []
            })
            print_success(f"Created drd.json in {directory}")
            return metadata_manager
    return ProjectMetadataManager(directory)


def apply_fix_commands(fix_commands, executor):
    all_outputs = []
    total_steps = len(fix_commands)

    for i, fix_cmd in enumerate(fix_commands, 1):
        print(fix_cmd, "----")
        if fix_cmd['type'] == 'explanation':
            print_info(
                f"Step {i}/{total_steps}: Explanation: {fix_cmd['content']}")
            all_outputs.append(
                f"Step {i}/{total_steps}: Explanation - {fix_cmd['content']}")
        elif fix_cmd['type'] == 'shell':
            print_info(
                f"Step {i}/{total_steps}: Running the fix: {fix_cmd['command']}")
            try:
                output = executor.execute_shell_command(fix_cmd['command'])
                print_success(
                    f"Step {i}/{total_steps}: Successfully executed: {fix_cmd['command']}")
                if output:
                    click.echo(
                        f"{Fore.MAGENTA}Command output:{Style.RESET_ALL}\n{output}")
                all_outputs.append(
                    f"Step {i}/{total_steps}: Shell command - {fix_cmd['command']}\nOutput: {output}")
            except Exception as e:
                error_message = f"Step {i}/{total_steps}: Error executing fix command: {fix_cmd['command']}\nError details: {str(e)}"
                print_error(error_message)
                all_outputs.append(error_message)
                return False, i, str(e), "\n".join(all_outputs)
        elif fix_cmd['type'] == 'file':
            print_info(
                f"Step {i}/{total_steps}: Updating file: {fix_cmd['filename']}")
            try:
                operation_performed = executor.perform_file_operation(
                    'UPDATE',
                    fix_cmd['filename'],
                    fix_cmd.get('content'),
                    force=True
                )
                if operation_performed:
                    print_success(
                        f"Step {i}/{total_steps}: Successfully updated file: {fix_cmd['filename']}")
                    all_outputs.append(
                        f"Step {i}/{total_steps}: File update - {fix_cmd['filename']} - Success")
                else:
                    error_message = f"Step {i}/{total_steps}: Failed to update file: {fix_cmd['filename']}"
                    print_error(error_message)
                    all_outputs.append(error_message)
                    return False, i, "File operation failed", "\n".join(all_outputs)
            except Exception as e:
                error_message = f"Step {i}/{total_steps}: Error updating file: {fix_cmd['filename']}\nError details: {str(e)}"
                print_error(error_message)
                all_outputs.append(error_message)
                return False, i, str(e), "\n".join(all_outputs)
    return True, total_steps, None, "\n".join(all_outputs)


def handle_error_with_claude(error, cmd, executor, depth=0, previous_context=""):
    if depth > 3:  # Limit recursion depth
        print_error(
            "Max error handling depth reached. Unable to resolve the issue.")
        return False

    print_error(f"Error executing command: {error}")
    error_trace = traceback.format_exc()

    error_query = get_error_analysis_prompt(
        cmd, error, error_trace, previous_context)

    print_info("Sending error information to Claude for analysis...")
    response = call_claude_api(error_query)
    fix_commands = parse_claude_response(response)

    print_info("Claude's suggested fix:")
    print_info("Applying Claude's suggested fix...")
    print(fix_commands, "----")
    fix_applied, step_completed, error_message, all_outputs = apply_fix_commands(
        fix_commands, executor)

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

        # Prepare a new error query with the failed fix attempt information
        new_error_query = get_error_analysis_prompt(
            {"type": "fix", "command": f"apply fix step {step_completed}"},
            Exception(error_message),
            all_outputs,
            previous_context + "\n\n" + error_query
        )

        # Recursively try to fix the error in applying the fix
        return handle_error_with_claude(Exception(new_error_query),
                                        {"type": "fix",
                                            "command": f"apply fix step {step_completed}"},
                                        executor, depth + 1, new_error_query)


def create_drd_json(directory):
    metadata_manager = ProjectMetadataManager(directory)
    metadata_manager.save_metadata({
        "project_name": os.path.basename(directory),
        "last_updated": "",
        "files": []
    })
    print_success(f"Created drd.json in {directory}")


@click.command()
@click.option('--query', prompt='Your query for Claude', help='The query to send to Claude API')
@click.option('--debug', is_flag=True, help='Print debug information')
def claude_cli(query, debug):
    print_info("Starting Claude CLI tool...")

    current_dir = os.getcwd()
    executor = Executor()
    metadata_manager = ProjectMetadataManager(current_dir)

    print_info("Sending query to Claude API...")
    project_context = metadata_manager.get_project_context()
    response = call_claude_api(
        f"{project_context}\n\nUser query: {query}", include_context=True)
    if debug:
        print_info("Raw response from Claude API:")
        print(response)
    print_success("Received response from Claude API.")

    commands = parse_claude_response(response)
    if not commands:
        print_error(
            "Failed to parse Claude's response. No commands to execute.")
        return

    if debug:
        print_info("Parsed commands:")
        pretty_print_commands(commands)
    print_info(f"Parsed {len(commands)} commands from Claude's response.")

    for i, cmd in enumerate(commands):
        if cmd['type'] == 'explanation':
            print_info(f"Explanation: {cmd['content']}")
            continue

        print_step(i+1, len(commands), f"Processing {cmd['type']} command...")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if cmd['type'] == 'shell':
                    output = executor.execute_shell_command(cmd['command'])
                    print_success(f"Executed shell command: {cmd['command']}")
                    if output:
                        click.echo(
                            f"{Fore.MAGENTA}Command output:{Style.RESET_ALL}\n{output}")
                elif cmd['type'] == 'file':
                    operation_performed = executor.perform_file_operation(
                        cmd['operation'],
                        cmd['filename'],
                        cmd.get('content'),
                        force=True
                    )

                    if operation_performed:
                        description = generate_description(
                            cmd['filename'], cmd.get('content', ''))
                        metadata_manager.update_file_metadata(
                            cmd['filename'],
                            cmd['filename'].split('.')[-1],
                            cmd.get('content', ''),
                            description
                        )
                        print_success(
                            f"Performed {cmd['operation']} operation on file: {cmd['filename']}")
                        print_info(f"Generated description: {description}")
                    else:
                        print_info(
                            f"File operation skipped for: {cmd['filename']}")
                break  # If successful, break the retry loop
            except Exception as e:
                print_info(
                    f"Error occurred (Attempt {attempt+1}/{max_retries}). Attempting to fix with Claude's assistance.")
                if handle_error_with_claude(e, cmd, executor, metadata_manager):
                    print_info(
                        "Fix applied successfully. Retrying the original command.")
                else:
                    print_error(
                        f"Unable to fix the error after attempt {attempt+1}.")
                    if attempt == max_retries - 1:
                        print_info(
                            "Max retries reached. Skipping this command.")
                        break
        else:
            print_error(
                f"Failed to execute command after {max_retries} attempts. Skipping and moving to the next command.")

    print_success("Claude CLI tool execution completed.")


def handle_error_with_claude(error, cmd, executor, metadata_manager, depth=0, previous_context=""):
    if depth > 3:  # Limit recursion depth
        print_error(
            "Max error handling depth reached. Unable to resolve the issue.")
        return False

    print_error(f"Error executing command: {error}")
    error_trace = traceback.format_exc()

    project_context = metadata_manager.get_project_context()
    error_query = f"""
    Project context:
    {project_context}

    Previous context:
    {previous_context}

    An error occurred while executing the following command:
    {cmd['type']}: {cmd.get('command') or cmd.get('filename')}
    
    Error details:
    {error_trace}
    
    Please analyze this error and provide a JSON response with the following structure:
    {{
        "explanation": "Brief explanation of the error and proposed fix",
        "steps": [
            {{
                "type": "shell" or "file",
                "command" or "filename": "command to execute or file to modify",
                "content": "file content if type is file"
            }}
        ]
    }}
    Ensure the steps are executable and will resolve the issue. Strictly only respond with json, no extra words before or after.
    """

    print_info("Sending error information to Claude for analysis...")
    response = call_claude_api(error_query, include_context=True)
    fix_commands = parse_claude_response(response)

    print_info("Claude's suggested fix:")
    print_info("Applying Claude's suggested fix...")
    fix_applied, step_completed, error_message, all_outputs = apply_fix_commands(
        fix_commands, executor, metadata_manager)

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

        # Recursively try to fix the error in applying the fix
        return handle_error_with_claude(Exception(error_message),
                                        {"type": "fix",
                                            "command": f"apply fix step {step_completed}"},
                                        executor, metadata_manager, depth + 1, all_outputs)


def apply_fix_commands(fix_commands, executor, metadata_manager):
    # ... [keep the existing implementation, but update file metadata after each successful file operation]
    # Example:
    if cmd['type'] == 'file' and operation_performed:
        description = generate_description(
            cmd['filename'], cmd.get('content', ''))
        metadata_manager.update_file_metadata(
            cmd['filename'],
            cmd['filename'].split('.')[-1],
            cmd.get('content', ''),
            description
        )
    # ...


if __name__ == '__main__':
    claude_cli()

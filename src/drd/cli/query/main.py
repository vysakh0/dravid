import click
from ...api.dravid_api import call_dravid_api
from ...api.dravid_parser import parse_dravid_response, pretty_print_commands
from ...utils.step_executor import Executor
from ...metadata.project_metadata import ProjectMetadataManager
from ...prompts.error_handling import handle_error_with_dravid
from ...utils import print_error, print_success, print_info, print_step, generate_description, fetch_project_guidelines
from .file_operations import get_files_to_modify, get_file_content
from .image_handler import handle_image_query


def execute_dravid_command(query, image_path, debug, instruction_prompt):
    print_info("Starting Dravid CLI tool...")

    executor = Executor()
    metadata_manager = ProjectMetadataManager(executor.current_dir)

    try:
        project_context = metadata_manager.get_project_context()

        if project_context:
            files_to_modify = get_files_to_modify(query, project_context)

            if debug:
                print_info("Files to be modified:")
                for file in files_to_modify:
                    print(file)

            file_contents = {}
            for file in files_to_modify:
                content = get_file_content(file)
                if content:
                    file_contents[file] = content

            project_guidelines = fetch_project_guidelines(executor.current_dir)
            file_context = "\n".join(
                [f"Current content of {file}:\n{content}" for file, content in file_contents.items()])
            full_query = f"{project_context}\n\nProject Guidelines:\n{project_guidelines}\n\nCurrent file contents:\n{file_context}\n\nUser query: {query}"
        else:
            print_info(
                """No current project context found. Will create a new project in the current directory.
                Please exit with ctrl+c if you have not created a fresh directory
                """)
            full_query = f"User query: {query}"

        if image_path:
            response = handle_image_query(
                full_query, image_path, instruction_prompt)
        else:
            response = call_dravid_api(
                full_query, include_context=True, instruction_prompt=instruction_prompt)

        if debug:
            print_info("Raw response from Dravid API:")
            print(response)
        print_success("Received response from Dravid API.")

        commands = parse_dravid_response(response)
        if not commands:
            print_error(
                "Failed to parse dravid's response or no commands to execute.")
            if debug:
                print_info("dravid's raw response:")
                print(response)
            return

        if debug:
            print_info("Parsed commands:")
            pretty_print_commands(commands)
        print_info(f"Parsed {len(commands)} commands from dravid's response.")

        for i, cmd in enumerate(commands):
            if cmd['type'] == 'explanation':
                print_info(f"Explanation: {cmd['content']}")
                continue

            print_step(i+1, len(commands),
                       f"Processing {cmd['type']} command...")

            max_retries = 3
            for attempt in range(max_retries):
                if cmd['type'] == 'metadata':
                    if cmd['operation'] == 'UPDATE_DEV_SERVER':
                        metadata_manager.update_dev_server_info(
                            cmd['start_command'],
                            cmd['framework'],
                            cmd['language']
                        )
                        print_success(
                            "Updated dev server info in project metadata.")
                        break
                    elif cmd['operation'] == 'UPDATE_FILE':
                        if metadata_manager.update_metadata_from_file(cmd['filename']):
                            print_success(
                                f"Updated metadata for file: {cmd['filename']}")
                        else:
                            print_error(
                                f"Failed to update metadata for file: {cmd['filename']}")
                        break
                else:
                    result = handle_command(cmd, executor, metadata_manager)
                    if isinstance(result, tuple) and not result[0]:
                        error = result[1]
                        print_info(
                            f"Error occurred (Attempt {attempt+1}/{max_retries}). Attempting to fix with dravid's assistance.")
                        if handle_error_with_dravid(error, cmd, executor, metadata_manager):
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
                        break  # Command executed successfully
            else:
                print_error(
                    f"Failed to execute command after {max_retries} attempts. Skipping and moving to the next command.")

        print_success("Dravid CLI tool execution completed.")
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        if debug:
            import traceback
            traceback.print_exc()


def handle_command(cmd, executor, metadata_manager):
    try:
        if cmd['type'] == 'shell':
            output = executor.execute_shell_command(cmd['command'])
            if output is not None:
                print_success(f"Executed shell command: {cmd['command']}")
                if output:
                    click.echo(f"Command output:\n{output}")
            else:
                raise Exception(
                    f"Shell command execution failed: {cmd['command']}")
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
                raise Exception(
                    f"File operation failed: {cmd['operation']} on {cmd['filename']}")
        return True
    except Exception as e:
        print_error(f"Error in handle_command: {str(e)}")
        return False, e

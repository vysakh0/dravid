import click
import os
import traceback
from dotenv import load_dotenv
from .claude_api import call_claude_api, generate_description
from .claude_parser import parse_claude_response, pretty_print_commands
from .executor import Executor
from .project_metadata import ProjectMetadataManager
from .prompts.error_handling import handle_error_with_claude
from .utils import print_error, print_success, print_info, print_step
from colorama import init

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()


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


@click.command()
@click.option('--query', prompt='I\'m your coding assistant, what do you want me to generate or execute',
              help='Coding assistant will execute your instruction to generate and run code')
@click.option('--debug', is_flag=True, help='Print more information on how this coding assistant executes your instruction')
def claude_cli(query, debug):
    print_info("Starting Claude CLI tool...")

    executor = Executor()
    metadata_manager = ProjectMetadataManager(executor.current_dir)

    try:
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
                "Failed to parse Claude's response or no commands to execute.")
            if debug:
                print_info("Claude's raw response:")
                print(response)
            return

        if debug:
            print_info("Parsed commands:")
            pretty_print_commands(commands)
        print_info(f"Parsed {len(commands)} commands from Claude's response.")

        for i, cmd in enumerate(commands):
            if cmd['type'] == 'explanation':
                print_info(f"Explanation: {cmd['content']}")
                continue

            print_step(i+1, len(commands),
                       f"Processing {cmd['type']} command...")

            max_retries = 3
            for attempt in range(max_retries):
                result = handle_command(cmd, executor, metadata_manager)
                if isinstance(result, tuple) and not result[0]:
                    error = result[1]
                    print_info(
                        f"Error occurred (Attempt {attempt+1}/{max_retries}). Attempting to fix with Claude's assistance.")
                    if handle_error_with_claude(error, cmd, executor, metadata_manager):
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

        print_success("Claude CLI tool execution completed.")
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        if debug:
            traceback.print_exc()


if __name__ == '__main__':
    claude_cli()

import click
import os
import traceback
from dotenv import load_dotenv
from typing import List, Dict, Any  # Add this line
from .claude_api import call_claude_api, generate_description
from .claude_parser import parse_claude_response, pretty_print_commands, extract_and_parse_xml
from .executor import Executor
from .project_metadata import ProjectMetadataManager
from .prompts.error_handling import handle_error_with_claude
from .utils import print_error, print_success, print_info, print_step
from colorama import init
import xml.etree.ElementTree as ET

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()


def get_file_content(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.read()
    return None


def parse_file_list_response(response: str) -> List[str]:
    try:
        root = extract_and_parse_xml(response)
        files = root.findall('.//file')
        return [file.text.strip() for file in files if file.text]
    except Exception as e:
        print_error(f"Error parsing file list response: {e}")
        print("Original response:")
        print(response)
        return []


def get_files_to_modify(query, project_context):
    file_query = f"""
{project_context}

User query: {query}

Based on the user's query and the project context, which files will need to be modified?
Please respond with a list of filenames in the following XML format:

<response>
  <files>
    <file>path/to/file1.ext</file>
    <file>path/to/file2.ext</file>
  </files>
</response>

Only include files that will need to be modified to fulfill the user's request.
"""
    response = call_claude_api(file_query, include_context=True)
    return parse_file_list_response(response)


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

        if project_context:
            # Step 1: Ask Claude which files need to be modified
            files_to_modify = get_files_to_modify(query, project_context)

            if debug:
                print_info("Files to be modified:")
                for file in files_to_modify:
                    print(file)

            # Step 2: Fetch current content of files to be modified
            file_contents = {}
            for file in files_to_modify:
                content = get_file_content(file)
                if content:
                    file_contents[file] = content

            # Step 3: Include file contents in the query to Claude
            file_context = "\n".join(
                [f"Current content of {file}:\n{content}" for file, content in file_contents.items()])
            full_query = f"{project_context}\n\nCurrent file contents:\n{file_context}\n\nUser query: {query}"
        else:
            print_info(
                """No current project context found. Will create a new project in the current directory.
                Please exit with ctrl+c if you have not created a fresh directory
                """)
            full_query = f"User query: {query}"

        response = call_claude_api(full_query, include_context=True)
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

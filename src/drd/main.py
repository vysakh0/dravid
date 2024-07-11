import click
from datetime import datetime
import json
import os
import traceback
from dotenv import load_dotenv
from typing import List, Dict, Any
from .dravid_api import call_dravid_api, call_dravid_vision_api, generate_description
from .dravid_parser import parse_dravid_response, pretty_print_commands, extract_and_parse_xml
from .executor import Executor
from .project_metadata import ProjectMetadataManager
from .metadata_updater import update_metadata_with_dravid
from .metadata_initializer import initialize_project_metadata
from .prompts.error_handling import handle_error_with_dravid
from .utils import print_error, print_success, print_info, print_step
from .monitor import run_dev_server_with_monitoring
from colorama import init
import xml.etree.ElementTree as ET
import re


# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()


def parse_file_list_response(response: str) -> List[str]:
    try:
        root = extract_and_parse_xml(response)
        files = root.findall('.//file')
        return [file.text.strip() for file in files if file.text]
    except Exception as e:
        print_error(f"Error parsing file list response: {e}")
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
    response = call_dravid_api(file_query, include_context=True)
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


def execute_dravid_command(query, image_path, debug):
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

            file_context = "\n".join(
                [f"Current content of {file}:\n{content}" for file, content in file_contents.items()])
            full_query = f"{project_context}\n\nCurrent file contents:\n{file_context}\n\nUser query: {query}"
        else:
            print_info(
                """No current project context found. Will create a new project in the current directory.
                Please exit with ctrl+c if you have not created a fresh directory
                """)
            full_query = f"User query: {query}"

        if image_path:
            response = call_dravid_vision_api(
                full_query, image_path, include_context=True)
        else:
            response = call_dravid_api(full_query, include_context=True)

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
            traceback.print_exc()


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
    response = call_dravid_api(file_query, include_context=True)
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


def monitoring_handle_error_with_dravid(error, line, monitor):
    print_error(f"Error detected: {error}")

    error_message = str(error)
    error_type = type(error).__name__
    error_trace = ''.join(traceback.format_exception(
        type(error), error, error.__traceback__))

    project_context = monitor.metadata_manager.get_project_context()

    print("error_trace", error_trace)
    print("error_message", error_message)

    # First, ask Dravid which files it needs to examine
    files_to_examine = get_relevant_files_from_dravid(
        error_message, error_type, project_context, monitor.project_dir)

    # Gather the content of the files Dravid requested
    additional_context = gather_file_contents(
        files_to_examine, monitor.project_dir)

    error_query = f"""
# Error Context
An error occurred while running the dev server:

Error type: {error_type}
Error message: {error_message}

Error trace:
{error_trace}

Relevant output line:
{line}

Project context:
{project_context}

Additional context:
{additional_context}

# Instructions for dravid: Error Resolution Assistant
Analyze the error above and provide steps to fix it.
This is being run in a monitoring thread, so don't suggest server starting commands like npm run dev.
If there is a module not found error, don't immediately try to install that module alone. See the larger context,
it could be that it is a dependency of a larger dependency or main library which in itself wouldn't have been installed.
Identify the pattern, nobody would use a certain dependency if not for the main project, so don't suggest installing direct dependencies in such
a situation, you can assume the user deleted or didnt install the parent library. Of course there could be situation where
the specific library itself is the fix. Use the information about the project, the framework, library etc to come to a fix.
Think in step by step like what framework what project, what error, look at all available context.
Remember human error of deleting, typo, is very common.
Don't just fix the given error, fix any relevant and related mistakes or errors. Even importing modules or need to install new packages.
Just because you see contents in drd.json doesn't mean the file has to exist, probably the user could have deleted it as well.

Based on the additional context provided, suggest a comprehensive fix that addresses the root cause of the issue.
If you need more information to provide an accurate fix, specify what additional files or information you need to examine.

Your response should be in strictly XML format with no other extra messages. Use the following format:
<response>
<explanation>A brief explanation of the steps, if necessary</explanation>
<steps>
    <step>
    <type>shell</type>
    <command>command to execute</command>
    </step>
    <step>
    <type>file</type>
    <operation>CREATE</operation>
    <filename>path/to/file.ext</filename>
    <content>
        <![CDATA[
        file content here
        ]]>
    </content>
    </step>
    <step>
    <type>file</type>
    <operation>UPDATE</operation>
    <filename>path/to/existing/file.ext</filename>
    <content>
        <![CDATA[
        content to append or replace
        ]]>
    </content>
    </step>
    <step>
    <type>file</type>
    <operation>DELETE</operation>
    <filename>path/to/file/to/delete.ext</filename>
    </step>
</steps>
</response>
"""

    print_info("Sending error information to Dravid for analysis...")
    response = call_dravid_api(error_query, include_context=True)

    try:
        fix_commands = parse_dravid_response(response)
    except ValueError as e:
        print_error(f"Error parsing dravid's response: {str(e)}")
        return False

    print_info("dravid's suggested fix:")
    pretty_print_commands(fix_commands)

    if click.confirm("Do you want to apply this fix?"):
        print_info("Applying dravid's suggested fix...")
        executor = Executor()
        for cmd in fix_commands:
            if cmd['type'] == 'shell':
                print_info(f"Executing: {cmd['command']}")
                executor.execute_shell_command(cmd['command'])
            elif cmd['type'] == 'file':
                print_info(
                    f"Performing file operation: {cmd['operation']} on {cmd['filename']}")
                executor.perform_file_operation(
                    cmd['operation'], cmd['filename'], cmd.get('content'))
        print_success("Fix applied. Restarting server...")
        monitor.restart()
        return True
    else:
        print_info("Fix not applied. Continuing with current state.")
        return False


def get_relevant_files_from_dravid(error_message, error_type, project_context, project_dir):
    query = f"""
Given the following error and project context, what files should I examine to diagnose and fix the issue?

Error type: {error_type}
Error message: {error_message}

Project context:
{project_context}

Please list the files you think are most relevant to this error, in order of importance.
Respond with an XML structure containing the file paths:

<response>
  <files>
    <file>path/to/file1.ext</file>
    <file>path/to/file2.ext</file>
    <!-- Add more file elements as needed -->
  </files>
</response>
"""

    response = call_dravid_api(query, include_context=True)

    try:
        root = extract_and_parse_xml(response)
        files = root.findall('.//file')
        return [file.text.strip() for file in files if file.text]
    except Exception as e:
        print_error(
            f"Error parsing dravid's response for relevant files: {str(e)}")
        return []


def gather_file_contents(files_to_examine, project_dir):
    context = []

    for file_path in files_to_examine:
        full_path = os.path.join(project_dir, file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                content = f.read()
            context.append(f"Contents of {file_path}:")
            context.append(content)
        else:
            context.append(f"File not found: {file_path}")

    return "\n\n".join(context)


def find_file_with_dravid(filename, project_context, max_retries=2, current_retry=0):
    print("filename", filename)
    if os.path.exists(filename):
        print("filename exists", filename)
        return filename

    if current_retry >= max_retries:
        print_error(f"File not found after {max_retries} retries: {filename}")
        return None

    query = f"""
{project_context}

The file "{filename}" was not found. Based on the project context and the filename, can you suggest the correct path or an alternative file that might contain the updated content?

Respond with an XML structure containing the suggested file path:

<response>
  <file>suggested/path/to/file.ext</file>
</response>

If you can't suggest an alternative, respond with an empty <file> tag.
"""

    response = call_dravid_api(query, include_context=True)

    try:
        root = extract_and_parse_xml(response)
        suggested_file = root.find('.//file').text.strip()
        if suggested_file:
            print_info(
                f"Dravid suggested an alternative file: {suggested_file}")
            return find_file_with_dravid(suggested_file, project_context, max_retries, current_retry + 1)
        else:
            print_error("Dravid couldn't suggest an alternative file.")
            return None
    except Exception as e:
        print_error(f"Error parsing dravid's response: {str(e)}")
        return None


@click.command()
@click.argument('query', required=False)
@click.option('--image', type=click.Path(exists=True), help='Path to an image file to include with the query')
@click.option('--debug', is_flag=True, help='Print more information on how this coding assistant executes your instruction')
@click.option('--monitor-fix', is_flag=True, help='Start the dev server monitor to automatically fix errors')
@click.option('--meta-add', help='Update metadata based on the provided description')
@click.option('--meta-init', is_flag=True, help='Initialize project metadata')
def dravid_cli(query, image, debug, monitor_fix, meta_add, meta_init):
    if monitor_fix:
        run_dev_server_with_monitoring()
    elif meta_add:
        update_metadata_with_dravid(meta_add, os.getcwd())
    elif meta_init:
        initialize_project_metadata(os.getcwd())
    elif query:
        execute_dravid_command(query, image, debug)
    else:
        click.echo(
            "Please provide a query, use --meta-add to update metadata, or use --meta-init to initialize project metadata.")


if __name__ == '__main__':
    dravid_cli()

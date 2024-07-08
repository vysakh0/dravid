import click
import os
import traceback
from dotenv import load_dotenv
from typing import List, Dict, Any
from .claude_api import call_claude_api, generate_description
from .claude_parser import parse_claude_response, pretty_print_commands, extract_and_parse_xml
from .executor import Executor
from .project_metadata import ProjectMetadataManager
from .prompts.error_handling import handle_error_with_claude
from .utils import print_error, print_success, print_info, print_step, handle_module_not_found, handle_syntax_error
from colorama import init
import xml.etree.ElementTree as ET
import threading
from queue import Queue, Empty
import subprocess
import re

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()


class DevServerMonitor:
    def __init__(self, project_dir: str, error_handlers: dict):
        self.project_dir = project_dir
        self.metadata_manager = ProjectMetadataManager(project_dir)
        self.error_handlers = error_handlers
        self.process = None
        self.output_queue = Queue()
        self.should_stop = threading.Event()

    def start(self):
        dev_server_info = self.metadata_manager.get_dev_server_info()
        start_command = dev_server_info.get('start_command')

        if not start_command:
            raise ValueError("Dev server start command not found in drd.json")

        click.echo(
            f"Starting dev server with command: {' '.join(start_command)}")
        self.process = subprocess.Popen(
            start_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=self.project_dir
        )

        threading.Thread(target=self._enqueue_output, args=(
            self.process.stdout, self.output_queue), daemon=True).start()
        threading.Thread(target=self._monitor_output, daemon=True).start()

    def _enqueue_output(self, out, queue):
        for line in iter(out.readline, ''):
            queue.put(line)
        out.close()

    def _monitor_output(self):
        while not self.should_stop.is_set():
            try:
                line = self.output_queue.get(timeout=0.1)
                click.echo(line, nl=False)  # Print server output in real-time

                for error_pattern, handler in self.error_handlers.items():
                    if re.search(error_pattern, line):
                        handler(line)

            except Empty:
                continue

    def stop(self):
        self.should_stop.set()
        if self.process:
            self.process.terminate()
            self.process.wait()


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


def execute_claude_command(query, debug):
    print_info("Starting Claude CLI tool...")

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


def update_metadata(files_to_update):
    print_info("Updating metadata for specified files...")
    executor = Executor()
    metadata_manager = ProjectMetadataManager(executor.current_dir)

    for file in files_to_update:
        if metadata_manager.update_metadata_from_file(file):
            print_success(f"Updated metadata for file: {file}")
        else:
            print_error(f"Failed to update metadata for file: {file}")


def update_metadata_with_claude(meta_description):
    print_info("Updating metadata based on the provided description...")
    executor = Executor()
    metadata_manager = ProjectMetadataManager(executor.current_dir)
    project_context = metadata_manager.get_project_context()

    # Step 1: Identify files to update
    files_query = f"""
{project_context}

User update description: {meta_description}

Based on the user's description and the project context, please identify which files need to have their metadata updated.
Respond with an XML structure containing the files to update:

<response>
  <files>
    <file>path/to/file1.ext</file>
    <file>path/to/file2.ext</file>
    <!-- Add more file elements as needed -->
  </files>
</response>

Only include files that need to be updated based on the user's description.
"""

    files_response = call_claude_api(files_query, include_context=True)

    try:
        root = extract_and_parse_xml(files_response)
        files_to_update = [file.text.strip()
                           for file in root.findall('.//file')]

        if not files_to_update:
            print_info("No files identified for metadata update.")
            return

        print_info(
            f"Files identified for update: {', '.join(files_to_update)}")

        # Step 2: Read file contents and generate metadata
        for filename in files_to_update:
            if not os.path.exists(filename):
                print_error(f"File not found: {filename}")
                continue

            with open(filename, 'r') as f:
                content = f.read()

            metadata_query = f"""
{project_context}

File: {filename}
Content:
{content}

Based on the file content and the project context, please generate appropriate metadata for this file.
Respond with an XML structure containing the metadata:

<response>
  <metadata>
    <type>file_type</type>
    <description>Description of the file's contents or purpose</description>
  </metadata>
</response>
"""

            metadata_response = call_claude_api(
                metadata_query, include_context=True)

            try:
                metadata_root = extract_and_parse_xml(metadata_response)
                file_type = metadata_root.find('.//type').text.strip()
                description = metadata_root.find('.//description').text.strip()

                metadata_manager.update_file_metadata(
                    filename,
                    file_type,
                    content,
                    description
                )
                print_success(f"Updated metadata for file: {filename}")
            except Exception as e:
                print_error(f"Error parsing metadata for {filename}: {str(e)}")

        print_success("Metadata update completed.")
    except Exception as e:
        print_error(f"Error parsing Claude's response: {str(e)}")


@click.command()
@click.option('--query', help='Coding assistant will execute your instruction to generate and run code')
@click.option('--debug', is_flag=True, help='Print more information on how this coding assistant executes your instruction')
@click.option('--monitor-fix', is_flag=True, help='Start the dev server monitor to automatically fix errors')
@click.option('--meta-add', help='Update metadata based on the provided description')
def claude_cli(query, debug, monitor_fix, meta_add):
    if monitor_fix:
        run_dev_server_with_monitoring()
    elif meta_add:
        update_metadata_with_claude(meta_add)
    elif query:
        execute_claude_command(query, debug)
    else:
        click.echo("Please provide a query or use --meta-add to update metadata.")


def run_dev_server_with_monitoring():
    print_info("Starting dev server monitor...")

    error_handlers = {
        r"Cannot find module": handle_module_not_found,
        r"SyntaxError": handle_syntax_error,
        # Add more error patterns and handlers as needed
    }

    current_dir = os.getcwd()
    monitor = DevServerMonitor(current_dir, error_handlers)

    try:
        monitor.start()
        click.echo("Dev server monitor started. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        click.echo("Stopping development server...")
    finally:
        monitor.stop()


if __name__ == '__main__':
    claude_cli()

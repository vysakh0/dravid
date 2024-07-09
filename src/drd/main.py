import click
from datetime import datetime  # Add this import
import time
import json
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


def get_folder_structure(start_path):
    ignore_dirs = {'node_modules', 'dist',
                   'build', 'venv', '.git', '__pycache__'}
    structure = []

    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * level
        structure.append(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            structure.append(f"{sub_indent}{file}")

    return '\n'.join(structure)


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


def find_file_with_claude(filename, project_context, max_retries=2, current_retry=0):
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

    response = call_claude_api(query, include_context=True)

    try:
        root = extract_and_parse_xml(response)
        suggested_file = root.find('.//file').text.strip()
        if suggested_file:
            print_info(
                f"Claude suggested an alternative file: {suggested_file}")
            return find_file_with_claude(suggested_file, project_context, max_retries, current_retry + 1)
        else:
            print_error("Claude couldn't suggest an alternative file.")
            return None
    except Exception as e:
        print_error(f"Error parsing Claude's response: {str(e)}")
        return None


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
        print("files to update", files_to_update)
        for filename in files_to_update:
            found_filename = find_file_with_claude(filename, project_context)
            if not found_filename:
                continue

            with open(found_filename, 'r') as f:
                content = f.read()

            metadata_query = f"""
{project_context}

File: {found_filename}
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
                    found_filename,
                    file_type,
                    content,
                    description
                )
                print_success(f"Updated metadata for file: {found_filename}")
            except Exception as e:
                print_error(
                    f"Error parsing metadata for {found_filename}: {str(e)}")

        print_success("Metadata update completed.")
    except Exception as e:
        print_error(f"Error parsing Claude's response: {str(e)}")


def parse_gitignore(gitignore_path):
    ignore_patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Convert .gitignore pattern to regex
                    pattern = line.replace('.', r'\.')  # Escape dots
                    pattern = pattern.replace('*', '.*')  # Convert * to .*
                    pattern = pattern.replace('?', '.')   # Convert ? to .
                    if pattern.startswith('/'):
                        # Anchor at start if begins with /
                        pattern = '^' + pattern[1:]
                    elif pattern.endswith('/'):
                        pattern += '.*'  # Match any file in directory if ends with /
                    else:
                        pattern = '.*' + pattern  # Otherwise, match anywhere in path
                    ignore_patterns.append(re.compile(pattern))
    return ignore_patterns


def should_ignore(path, ignore_patterns):
    for pattern in ignore_patterns:
        if pattern.search(path):
            return True
    return False


def get_folder_structure(start_path, ignore_patterns):
    structure = []

    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * level
        folder_name = os.path.basename(root)

        rel_path = os.path.relpath(root, start_path)
        if rel_path == '.':
            rel_path = ''

        if not should_ignore(rel_path, ignore_patterns):
            structure.append(f"{indent}{folder_name}/")

            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                file_path = os.path.join(rel_path, file)
                if not should_ignore(file_path, ignore_patterns):
                    structure.append(f"{sub_indent}{file}")

        # Modify dirs in-place to exclude ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(
            os.path.join(rel_path, d), ignore_patterns)]

    return '\n'.join(structure)


def initialize_project_metadata():
    print_info("Initializing project metadata...")
    executor = Executor()
    current_dir = executor.current_dir

    # Parse .gitignore or use default ignore patterns
    gitignore_path = os.path.join(current_dir, '.gitignore')
    if os.path.exists(gitignore_path):
        ignore_patterns = parse_gitignore(gitignore_path)
        print_info("Using .gitignore patterns for file exclusion.")
    else:
        # Convert default patterns to regex
        default_patterns = ['node_modules', 'dist',
                            'build', 'venv', '.git', '__pycache__']
        ignore_patterns = [re.compile(f'.*{pattern}.*')
                           for pattern in default_patterns]
        print_info("No .gitignore found. Using default ignore patterns.")

    folder_structure = get_folder_structure(current_dir, ignore_patterns)
    print(folder_structure, "--")

    query = f"""
Current folder structure:
{folder_structure}

Based on the folder structure, please analyze the project and provide the following information:
1. Project name
2. Main programming language(s) used
3. Framework(s) used (if any)
4. Recommended dev server start command (if applicable)
5. A brief description of the project

Respond with an XML structure containing this information:

<response>
  <project_info>
  <project_name>project</project_name>
  <last_updated>2024-07-09T11:08:35.368477</last_updated>
  <files>
    <file>
      <filename>src/app/page.tsx</filename>
      <type>tsx</type>
      <last_modified>2024-07-09T11:08:35.363820</last_modified>
      <content_preview>import React from 'react';</content_preview>
      <description>React component for a minimal homepage displaying a centered</description>
    </file>
    <file>
      <filename>drd.json</filename>
      <type>json</type>
      <last_modified>2024-07-09T11:08:35.368514</last_modified>
      <content_preview></content_preview>
      <description></description>
    </file>
  </files>
  <dev_server>
    <start_command>npm run dev</start_command>
    <framework>Next.js</framework>
    <language>TypeScript</language>
  </dev_server>
  </project_info>
</response>
"""
    try:
        response = call_claude_api(query, include_context=True)
        root = extract_and_parse_xml(response)
        project_info = root.find('.//project_info')

        if project_info is None:
            raise ValueError(
                "Failed to extract project information from Claude's response")

        metadata = {
            "project_name": project_info.find('project_name').text.strip(),
            "last_updated": datetime.now().isoformat(),
            "files": [],
            "dev_server": {
                "start_command": project_info.find('.//dev_server/start_command').text.strip().split(),
                "framework": project_info.find('.//dev_server/framework').text.strip(),
                "language": project_info.find('.//dev_server/language').text.strip()
            }
        }

        # Gather file information
        for root, dirs, files in os.walk(current_dir):
            # Modify dirs in-place to exclude ignored directories
            dirs[:] = [d for d in dirs if not should_ignore(
                os.path.join(root, d), ignore_patterns)]

            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, current_dir)

                if should_ignore(relative_path, ignore_patterns):
                    continue  # Skip this file if it matches an ignore pattern

                # Get file extension without dot
                file_type = os.path.splitext(file)[1][1:] or 'unknown'

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # Read first 100 characters for preview
                        content = f.read(100)
                except Exception as e:
                    content = f"Error reading file: {str(e)}"

                file_metadata = {
                    "filename": relative_path,
                    "type": file_type,
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    "content_preview": content.replace('\n', ' '),
                    "description": generate_description(relative_path, content)
                }
                metadata["files"].append(file_metadata)

        metadata_manager = ProjectMetadataManager(current_dir)
        metadata_manager.metadata = metadata
        metadata_manager.save_metadata()

        print_success("Project metadata initialized successfully.")
        print_info("Generated metadata:")
        print(json.dumps(metadata, indent=2))

    except Exception as e:
        print_error(f"Error initializing project metadata: {str(e)}")
        print_error("Stack trace:")
        traceback.print_exc()


@click.command()
@click.option('--query', help='Coding assistant will execute your instruction to generate and run code')
@click.option('--debug', is_flag=True, help='Print more information on how this coding assistant executes your instruction')
@click.option('--monitor-fix', is_flag=True, help='Start the dev server monitor to automatically fix errors')
@click.option('--meta-add', help='Update metadata based on the provided description')
@click.option('--meta-init', is_flag=True, help='Initialize project metadata')
def claude_cli(query, debug, monitor_fix, meta_add, meta_init):
    if monitor_fix:
        run_dev_server_with_monitoring()
    elif meta_add:
        update_metadata_with_claude(meta_add)
    elif meta_init:
        initialize_project_metadata()
    elif query:
        execute_claude_command(query, debug)
    else:
        click.echo(
            "Please provide a query, use --meta-add to update metadata, or use --meta-init to initialize project metadata.")


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

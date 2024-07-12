import subprocess
import os
import json
import click
from colorama import Fore, Style
import time
from .utils import print_error, print_success, print_info


class Executor:
    def __init__(self):
        self.current_dir = os.getcwd()

    def execute_shell_command(self, command, timeout=300):  # 5 minutes timeout
        click.echo(
            f"{Fore.YELLOW}Executing shell command: {command}{Style.RESET_ALL}")
        env = os.environ.copy()
        # This might help with some commands that behave differently in CI environments
        env['CI'] = 'true'

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )

            start_time = time.time()
            output = []
            while True:
                return_code = process.poll()
                if return_code is not None:
                    break
                if time.time() - start_time > timeout:
                    process.terminate()
                    error_message = f"Command timed out after {timeout} seconds: {command}"
                    print_error(error_message)
                    raise Exception(error_message)

                # Print and capture output in real-time
                line = process.stdout.readline()
                if line:
                    print(line.strip())
                    output.append(line)

                time.sleep(0.1)  # Small delay to prevent CPU hogging

            stdout, stderr = process.communicate()
            output.append(stdout)

            if return_code != 0:
                error_message = f"Command failed with return code {return_code}\nError output: {stderr}"
                print_error(error_message)
                raise Exception(error_message)

            print_success("Command executed successfully.")
            return ''.join(output)

        except Exception as e:
            error_message = f"Error executing command '{command}': {str(e)}"
            print_error(error_message)
            raise Exception(error_message)

    def perform_file_operation(self, operation, filename, content=None, force=False):
        full_path = os.path.join(self.current_dir, filename)

        print_info(f"{filename}")
        print_info(content)
        if operation == 'CREATE':
            if os.path.exists(full_path) and not force:
                print_error(f"File already exists: {filename}")
                return False
            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
                print_success(f"File created successfully: {filename}")
                return True
            except Exception as e:
                print_error(f"Error creating file: {str(e)}")
                return False

        elif operation == 'UPDATE':
            if not os.path.exists(full_path):
                print_error(f"File does not exist: {filename}")
                return False
            try:
                with open(full_path, 'w') as f:
                    f.write(content)
                print_success(f"File updated successfully: {filename}")
                return True
            except Exception as e:
                print_error(f"Error updating file: {str(e)}")
                return False

        elif operation == 'DELETE':
            if not os.path.exists(full_path):
                print_error(f"File does not exist: {filename}")
                return False
            try:
                os.remove(full_path)
                print_success(f"File deleted successfully: {filename}")
                return True
            except Exception as e:
                print_error(f"Error deleting file: {str(e)}")
                return False

        else:
            print_error(f"Unknown file operation: {operation}")
            return False

    def parse_json(self, json_string):
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print_error(f"JSON parsing error: {str(e)}")
            return None

    def merge_json(self, existing_content, new_content):
        try:
            existing_json = json.loads(existing_content)
            new_json = json.loads(new_content)
            merged_json = {**existing_json, **new_json}
            return json.dumps(merged_json, indent=2)
        except json.JSONDecodeError as e:
            print_error(f"Error merging JSON content: {str(e)}")
            return None

import subprocess
import os
import click
from colorama import Fore, Style


class Executor:
    def __init__(self):
        self.initial_dir = os.getcwd()
        self.current_dir = self.initial_dir

    def execute_shell_command(self, command):
        click.echo(
            f"{Fore.YELLOW}Executing shell command: {command}{Style.RESET_ALL}")

        # Handle cd command separately
        if command.strip().startswith('cd '):
            new_dir = command.split(maxsplit=1)[1]
            new_dir = os.path.join(self.current_dir, new_dir)
            if os.path.isdir(new_dir):
                self.current_dir = new_dir
                click.echo(
                    f"{Fore.GREEN}Changed directory to: {self.current_dir}{Style.RESET_ALL}")
                return ""
            else:
                raise Exception(f"Directory not found: {new_dir}")

        # Set environment variable to force non-interactive mode for npm
        env = os.environ.copy()
        env['CI'] = 'true'

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=self.current_dir
            )

            # Read output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    click.echo(output.strip())

            return_code = process.poll()

            if return_code != 0:
                error_output = process.stderr.read()
                raise Exception(
                    f"Command failed with return code {return_code}. Error: {error_output}")

            return process.stdout.read()
        except Exception as e:
            raise Exception(f"Error executing command: {e}")

    def perform_file_operation(self, operation, filename, content=None, force=False):
        # Always use absolute path based on the initial directory
        full_path = os.path.join(self.initial_dir, filename)

        click.echo(
            f"{Fore.YELLOW}Performing {operation} operation on file: {full_path}{Style.RESET_ALL}")

        if operation.lower() == 'create':
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            click.echo(
                f"{Fore.GREEN}File created successfully.{Style.RESET_ALL}")
            return True
        elif operation.lower() == 'update':
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    existing_content = f.read()
                click.echo(
                    f"{Fore.CYAN}Existing content:{Style.RESET_ALL}\n{existing_content}\n")
                click.echo(
                    f"{Fore.CYAN}New content:{Style.RESET_ALL}\n{content}\n")
                if force or click.confirm("Do you want to replace the entire file content?"):
                    with open(full_path, 'w') as f:
                        f.write(content)
                    click.echo(
                        f"{Fore.GREEN}File updated successfully.{Style.RESET_ALL}")
                    return True
                else:
                    click.echo(
                        f"{Fore.YELLOW}File update skipped.{Style.RESET_ALL}")
                    return False
            else:
                click.echo(
                    f"{Fore.YELLOW}File does not exist. Creating new file.{Style.RESET_ALL}")
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
                click.echo(
                    f"{Fore.GREEN}File created successfully.{Style.RESET_ALL}")
                return True
        elif operation.lower() == 'delete':
            if os.path.exists(full_path):
                if force or click.confirm(f"Are you sure you want to delete {full_path}?"):
                    os.remove(full_path)
                    click.echo(
                        f"{Fore.GREEN}File deleted successfully.{Style.RESET_ALL}")
                    return True
                else:
                    click.echo(
                        f"{Fore.YELLOW}File deletion skipped.{Style.RESET_ALL}")
                    return False
            else:
                click.echo(
                    f"{Fore.YELLOW}File not found: {full_path}. Deletion skipped.{Style.RESET_ALL}")
                return False
        else:
            raise ValueError(f"Unknown file operation: {operation}")

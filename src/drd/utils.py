import subprocess
import click
from colorama import Fore, Style
import json
import os
import re

METADATA_FILE = 'drd.json'


def get_project_context():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
        return json.dumps(metadata, indent=2)
    return "{}"


def print_error(message):
    click.echo(f"{Fore.RED}✘ {message}{Style.RESET_ALL}")


def print_success(message):
    click.echo(f"{Fore.GREEN}✔ {message}{Style.RESET_ALL}")


def print_info(message):
    click.echo(f"{Fore.YELLOW}ℹ {message}{Style.RESET_ALL}")


def print_step(step_number, total_steps, message):
    click.echo(
        f"{Fore.CYAN}[{step_number}/{total_steps}] {message}{Style.RESET_ALL}")


def handle_module_not_found(error_line: str):
    match = re.search(r"Cannot find module '(.+?)'", error_line)
    if match:
        module_name = match.group(1)
        if click.confirm(f"Module '{module_name}' not found. Do you want to install it?"):
            try:
                subprocess.run(['npm', 'install', module_name], check=True)
                click.echo(f"Successfully installed {module_name}")
                return True
            except subprocess.CalledProcessError:
                click.echo(f"Failed to install {module_name}")
    return False


def handle_syntax_error(error_line: str):
    match = re.search(r"SyntaxError: (.+?) in (.+?) at line (\d+)", error_line)
    if match:
        error_msg, file_path, line_number = match.groups()
        click.echo(
            f"Syntax error in {file_path} at line {line_number}: {error_msg}")
        if click.confirm("Do you want to try to fix this error?"):
            # Here you could call Claude API to suggest a fix
            click.echo("Calling Claude API to suggest a fix...")
            return True
    return False

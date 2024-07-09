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


def handle_module_not_found(line, monitor):
    match = re.search(
        r"(?:Cannot find module|Module not found|ImportError|No module named).*['\"](.*?)['\"]", line, re.IGNORECASE)
    if match:
        module_name = match.group(1)
        click.echo(f"Error: Module '{module_name}' not found.")
        click.echo(
            "Please install the missing module manually and restart the server.")
        # You could potentially add auto-installation logic here if desired


def handle_syntax_error(line, monitor):
    click.echo("Syntax error detected. Please check your code and fix the error.")
    # You could add more sophisticated error reporting here


def handle_port_in_use(line, monitor):
    match = re.search(
        r"(?:EADDRINUSE|address already in use).*:(\d+)", line, re.IGNORECASE)
    if match:
        port = match.group(1)
        click.echo(
            f"Error: Port {port} is already in use. Please free up this port or use a different one.")

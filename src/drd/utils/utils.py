import click
from colorama import Fore, Style, Back
import json
import os

METADATA_FILE = 'drd.json'


def print_error(message):
    click.echo(f"{Fore.RED}✘ {message}{Style.RESET_ALL}")


def print_success(message):
    click.echo(f"{Fore.GREEN}✔ {message}{Style.RESET_ALL}")


def print_info(message):
    click.echo(f"{Fore.YELLOW}ℹ {message}{Style.RESET_ALL}")


def print_warning(message):
    click.echo(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_debug(message):
    click.echo(click.style(f"DEBUG: {message}", fg="cyan"))


def print_step(step_number, total_steps, message):
    click.echo(
        f"{Fore.CYAN}[{step_number}/{total_steps}] {message}{Style.RESET_ALL}")


def create_confirmation_box(message, action):
    box_width = len(message) + 4
    box_top = f"╔{'═' * box_width}╗"
    box_bottom = f"╚{'═' * box_width}╝"
    box_content = f"║  {message}  ║"

    confirmation_box = f"""
{Fore.YELLOW}{box_top}
║  {Back.RED}{Fore.WHITE}CONFIRMATION REQUIRED{Style.RESET_ALL}{Fore.YELLOW}  ║
{box_content}
╠{'═' * box_width}╣
║  Do you want to {action}?  ║
{box_bottom}{Style.RESET_ALL}
"""
    return confirmation_box


def print_command_details(commands):
    for index, cmd in enumerate(commands, start=1):
        cmd_type = cmd.get('type', 'Unknown')
        print_info(f"Command {index} - Type: {cmd_type}")

        if cmd_type == 'shell':
            print_info(f"  Command: {cmd.get('command', 'N/A')}")

        elif cmd_type == 'explanation':
            print_info(f"  Explanation: {cmd.get('content', 'N/A')}")

        elif cmd_type == 'file':
            operation = cmd.get('operation', 'N/A')
            filename = cmd.get('filename', 'N/A')
            content_preview = cmd.get('content', 'N/A')
            if len(content_preview) > 50:
                content_preview = content_preview[:50] + "..."
            print_info(f"  Operation: {operation}")
            print_info(f"  Filename: {filename}")
            print_info(f"  Content: {content_preview}")

        elif cmd_type == 'metadata':
            operation = cmd.get('operation', 'N/A')
            print_info(f"  Operation: {operation}")
            if operation == 'UPDATE_DEV_SERVER':
                print_info(
                    f"  Start Command: {cmd.get('start_command', 'N/A')}")
                print_info(f"  Framework: {cmd.get('framework', 'N/A')}")
                print_info(f"  Language: {cmd.get('language', 'N/A')}")
            elif operation in ['UPDATE_FILE', 'UPDATE']:
                print_info(f"  Filename: {cmd.get('filename', 'N/A')}")
                print_info(f"  Language: {cmd.get('language', 'N/A')}")
                print_info(f"  Description: {cmd.get('description', 'N/A')}")

        else:
            print_warning(f"  Unknown command type: {cmd_type}")

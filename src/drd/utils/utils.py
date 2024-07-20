import click
from colorama import Fore, Style, Back
import shutil


def print_error(message):
    click.echo(f"{Fore.RED}✘ {message}{Style.RESET_ALL}")


def print_prompt(message, indent=0):
    click.echo(f"{' ' * indent}{Fore.MAGENTA}{message}{Style.RESET_ALL}")


def print_success(message):
    click.echo(f"{Fore.GREEN}✔ {message}{Style.RESET_ALL}")


def print_info(message, indent=0):
    click.echo(f"{' ' * indent}{Fore.BLUE} {message}{Style.RESET_ALL}")


def print_warning(message):
    click.echo(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_debug(message):
    click.echo(click.style(f"DEBUG: {message}", fg="cyan"))


def print_step(step_number, total_steps, message):
    click.echo(
        f"{Fore.CYAN}[{step_number}/{total_steps}] {message}{Style.RESET_ALL}")


def create_confirmation_box(command, action):
    terminal_width = shutil.get_terminal_size().columns
    # Max width of 60 or terminal width - 4
    box_width = min(terminal_width - 4, 60)

    # Center the title
    title = "Confirmation"
    title_line = f"| {title.center(box_width - 2)} |"

    command_line = f"| {command.center(box_width - 2)} |"
    action_line = f"| {action.center(box_width - 2)} |"

    confirmation_box = f"""
{Fore.CYAN}{' ' * ((terminal_width - box_width) // 2)}┌{'─' * box_width}┐
{' ' * ((terminal_width - box_width) // 2)}{title_line}
{' ' * ((terminal_width - box_width) // 2)}|{' ' * box_width}|
{' ' * ((terminal_width - box_width) // 2)}{command_line}
{' ' * ((terminal_width - box_width) // 2)}{action_line}
{' ' * ((terminal_width - box_width) // 2)}└{'─' * box_width}┘{Style.RESET_ALL}
"""

    return confirmation_box


def print_command_details(commands):
    for index, cmd in enumerate(commands, start=1):
        cmd_type = cmd.get('type', 'Unknown')
        print_info(f"Command {index} - Type: {cmd_type}")

        if cmd_type == 'shell':
            print_info(f"  Command: {cmd.get('command', 'N/A')}", indent=2)

        elif cmd_type == 'explanation':
            print_info(f"  Explanation: {cmd.get('content', 'N/A')}", indent=2)

        elif cmd_type == 'file':
            operation = cmd.get('operation', 'N/A')
            filename = cmd.get('filename', 'N/A')
            content_preview = cmd.get('content', 'N/A')
            if len(content_preview) > 50:
                content_preview = content_preview[:50] + "..."
            print_info(f"  Operation: {operation}", indent=2)
            print_info(f"  Filename: {filename}", indent=2)
            print_info(f"  Content: {content_preview}", indent=2)

        elif cmd_type == 'metadata':
            operation = cmd.get('operation', 'N/A')
            print_info(f"  Operation: {operation}", indent=2)
            if operation == 'UPDATE_DEV_SERVER':
                print_info(
                    f"  Start Command: {cmd.get('start_command', 'N/A')}", indent=2)
                print_info(
                    f"  Framework: {cmd.get('framework', 'N/A')}", indent=2)
                print_info(
                    f"  Language: {cmd.get('language', 'N/A')}", indent=2)
            elif operation in ['UPDATE_FILE', 'UPDATE']:
                print_info(
                    f"  Filename: {cmd.get('filename', 'N/A')}", indent=2)
                print_info(
                    f"  Language: {cmd.get('language', 'N/A')}", indent=2)
                print_info(
                    f"  Description: {cmd.get('description', 'N/A')}", indent=2)

        else:
            print_warning(f"  Unknown command type: {cmd_type}")


def print_header(message):
    click.echo(f"\n🎾 {Fore.CYAN}{message}{Style.RESET_ALL}\n")

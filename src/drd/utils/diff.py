import difflib
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


def generate_colored_diff(original_content, new_content, context_lines=3):
    original_lines = original_content.splitlines()
    new_lines = new_content.splitlines()

    differ = difflib.unified_diff(
        original_lines, new_lines, lineterm='', n=context_lines)

    colored_diff = []
    for line in differ:
        if line.startswith('+'):
            colored_diff.append(f"{Fore.GREEN}{line}{Style.RESET_ALL}")
        elif line.startswith('-'):
            colored_diff.append(f"{Fore.RED}{line}{Style.RESET_ALL}")
        elif line.startswith('^'):
            colored_diff.append(f"{Fore.BLUE}{line}{Style.RESET_ALL}")
        else:
            colored_diff.append(line)

    return '\n'.join(colored_diff)


def preview_file_changes(operation, filename, new_content=None, original_content=None):
    preview = [f"{Fore.CYAN}{Style.BRIGHT}File: {filename}{Style.RESET_ALL}"]

    if operation == 'CREATE':
        preview.append(
            f"{Fore.GREEN}{Style.BRIGHT}Operation: CREATE{Style.RESET_ALL}")
        preview.append(f"{Fore.GREEN}New content:{Style.RESET_ALL}")
        preview.append(f"{Fore.GREEN}{new_content}{Style.RESET_ALL}")
    elif operation == 'UPDATE':
        preview.append(
            f"{Fore.YELLOW}{Style.BRIGHT}Operation: UPDATE{Style.RESET_ALL}")
        if original_content:
            preview.append(generate_colored_diff(
                original_content, new_content))
        else:
            preview.append(
                f"{Fore.RED}Error: Missing original content or changes for UPDATE operation{Style.RESET_ALL}")
    elif operation == 'DELETE':
        preview.append(
            f"{Fore.RED}{Style.BRIGHT}Operation: DELETE{Style.RESET_ALL}")
        preview.append(
            f"{Fore.RED}The file '{filename}' will be deleted.{Style.RESET_ALL}")
    else:
        preview.append(
            f"{Fore.RED}Unknown operation: {operation}{Style.RESET_ALL}")

    return '\n'.join(preview)

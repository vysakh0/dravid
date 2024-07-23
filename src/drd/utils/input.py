import click
from colorama import Fore, Style


def confirm_with_user(msg):
    return click.confirm(f"{Fore.YELLOW} {msg} {Style.RESET_ALL}", default=False)

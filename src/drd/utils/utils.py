import click
from colorama import Fore, Style
import json
import os
import time
import threading

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


def fetch_project_guidelines(project_dir):
    guidelines_path = os.path.join(project_dir, 'project_guidelines.txt')
    project_guidelines = ""
    if os.path.exists(guidelines_path):
        with open(guidelines_path, 'r') as guidelines_file:
            project_guidelines = guidelines_file.read()
        print_info("Project guidelines found and included in the context.")
    return project_guidelines


class Loader:
    def __init__(self, message="Processing"):
        self.message = message
        self.is_running = False
        self.animation = "|/-\\"
        self.idx = 0
        self.thread = None

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
        click.echo('\r' + ' ' * (len(self.message) + 10), nl=False)
        click.echo('\r', nl=False)

    def _animate(self):
        while self.is_running:
            click.echo(f'\r{self.message} {self.animation[self.idx % len(self.animation)]}', nl=False)
            self.idx += 1
            time.sleep(0.1)

def run_with_loader(func, message="Processing"):
    loader = Loader(message)
    loader.start()
    try:
        result = func()
    finally:
        loader.stop()
    return result
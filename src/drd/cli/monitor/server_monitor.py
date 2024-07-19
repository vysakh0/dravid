import click
import time
import re
import glob
import os
from typing import Dict, Callable
from ...metadata.project_metadata import ProjectMetadataManager
from queue import Queue
import threading
import subprocess
import select
import sys
from .error_handlers import handle_module_not_found, handle_syntax_error, handle_general_error
from ...prompts.instructions import get_instruction_prompt
from ...utils.utils import print_info, print_success, print_error
from ..query.main import execute_dravid_command


class DevServerMonitor:
    def __init__(self, project_dir: str, error_handlers: dict, command: str):
        self.project_dir = project_dir
        self.metadata_manager = ProjectMetadataManager(project_dir)
        self.error_handlers = error_handlers
        self.command = command
        self.process = None
        self.output_queue = Queue()
        self.should_stop = threading.Event()
        self.monitor_thread = None
        self.restart_requested = threading.Event()
        self.user_input_queue = Queue()
        self.last_output_time = time.time()
        self.processing_input = threading.Event()

    def start(self):
        self.should_stop.clear()
        self.restart_requested.clear()

        click.echo(f"Starting server with command: {self.command}")
        self._start_process(self.command)

        self.monitor_thread = threading.Thread(
            target=self._monitor_output, daemon=True)
        self.monitor_thread.start()

    def _start_process(self, command):
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            shell=True,
            cwd=self.project_dir
        )

    def _monitor_output(self):
        error_buffer = []
        idle_prompt_shown = False
        while not self.should_stop.is_set():
            if self.process.poll() is not None and not self.processing_input.is_set():
                if not self.restart_requested.is_set():
                    print_info(
                        "Server process ended unexpectedly. Restarting...")
                    self._perform_restart()
                continue

            ready, _, _ = select.select(
                [self.process.stdout, sys.stdin], [], [], 0.1)

            if self.process.stdout in ready:
                line = self.process.stdout.readline()
                if line:
                    click.echo(line, nl=False)
                    error_buffer.append(line)
                    if len(error_buffer) > 10:
                        error_buffer.pop(0)
                    self.last_output_time = time.time()
                    idle_prompt_shown = False

                    if not self.processing_input.is_set():
                        for error_pattern, handler in self.error_handlers.items():
                            if re.search(error_pattern, line, re.IGNORECASE):
                                full_error = ''.join(error_buffer)
                                handler(full_error, self)
                                error_buffer.clear()
                                break
            elif sys.stdin in ready:
                user_input = sys.stdin.readline().strip()
                self._handle_user_input(user_input)
                idle_prompt_shown = False  # Reset the idle prompt flag
            else:
                # Check if server has been idle for more than 5 seconds
                if time.time() - self.last_output_time > 5 and not idle_prompt_shown and not self.processing_input.is_set():
                    print_info(
                        "\n No more tasks to auto-process. What can I do next?")
                    self._show_options()
                    idle_prompt_shown = True

            if self.restart_requested.is_set() and not self.processing_input.is_set():
                self._perform_restart()
                self.restart_requested.clear()

    def _handle_vision_input(self):
        print_info("Enter the path to the image file (use Tab for autocomplete):")
        image_path = self._get_input_with_autocomplete()

        if not os.path.exists(image_path):
            print_error(f"Image file not found: {image_path}")
            return

        print_info("Enter your instructions for the image:")
        instructions = input("> ").strip()

        self.processing_input.set()
        try:
            print_info(f"Processing image: {image_path}")
            print_info(f"With instructions: {instructions}")
            instruction_prompt = get_instruction_prompt()
            execute_dravid_command(
                instructions, image_path, False, instruction_prompt, warn=False)
        except Exception as e:
            print_error(f"Error processing image input: {str(e)}")
        finally:
            self.processing_input.clear()
            print_info(
                "\nImage processing completed. Returning to server monitoring...")
            self.last_output_time = time.time()  # Reset the idle timer

    def _get_input_with_autocomplete(self):
        current_input = ""
        while True:
            char = click.getchar()
            if char == '\r':  # Enter key
                print()  # Move to next line
                return current_input
            elif char == '\t':  # Tab key
                completions = self._autocomplete(current_input)
                if len(completions) == 1:
                    current_input = completions[0]
                    click.echo("\r> " + current_input, nl=False)
                elif len(completions) > 1:
                    click.echo("\nPossible completions:")
                    for comp in completions:
                        click.echo(comp)
                    click.echo("> " + current_input, nl=False)
            elif char.isprintable():
                current_input += char
                click.echo(char, nl=False)
            elif char == '\x7f':  # Backspace
                if current_input:
                    current_input = current_input[:-1]
                    click.echo("\b \b", nl=False)

    def _autocomplete(self, text):
        path = os.path.expanduser(text)
        if os.path.isdir(path):
            path = os.path.join(path, '*')
        else:
            path = path + '*'

        completions = glob.glob(path)
        if len(completions) == 1 and os.path.isdir(completions[0]):
            return [completions[0] + os.path.sep]
        return completions

    def _handle_user_input(self, user_input):
        if user_input.lower() == 'exit':
            print_info("Exiting server monitor...")
            self.stop()
            return

        if user_input.lower() == 'vision':
            self._handle_vision_input()
            return

        if user_input:
            self.processing_input.set()
            try:
                print_info(f"Processing input: {user_input}")
                instruction_prompt = get_instruction_prompt()
                execute_dravid_command(
                    user_input, None, False, instruction_prompt, warn=False)
            except Exception as e:
                print_error(f"Error processing input: {str(e)}")
            finally:
                self.processing_input.clear()
                print_info(
                    "\nCommand execution completed. Returning to server monitoring...")
                self.last_output_time = time.time()  # Reset the idle timer
        else:
            self._show_options()

    def _show_options(self):
        print_info("\nAvailable actions:")
        print_info("1. Ask a question or give an instruction")
        print_info("2. Process an image (type 'vision')")
        print_info("3. Exit monitoring mode (type 'exit')")
        print_info("\nType your choice or command:")
        print("> ", end="", flush=True)

    def stop(self):
        self.should_stop.set()
        if self.process:
            self.process.terminate()
            self.process.wait()

    def request_restart(self):
        self.restart_requested.set()

    def _perform_restart(self):
        print_info("Restarting server...")
        if self.process:
            self.process.terminate()
            self.process.wait()
        time.sleep(2)  # Give some time for the old process to fully terminate
        print_info("Server stopped. Starting again...")
        self._start_process(self.command)

        self.restart_requested.clear()
        print_success("Server restarted successfully.")
        print_info("Waiting for server output...")


def run_dev_server_with_monitoring(command: str):
    print_info("Starting server monitor...")
    error_handlers = {
        r"(?:Cannot find module|Module not found|ImportError|No module named)": handle_module_not_found,
        r"(?:SyntaxError|Expected|Unexpected token)": handle_syntax_error,
        r"(?:Error:|Failed to compile)": handle_general_error,
    }
    current_dir = os.getcwd()
    monitor = DevServerMonitor(current_dir, error_handlers, command)
    try:
        monitor.start()
        print_info("Server monitor started. Press Ctrl+C to stop.")
        while not monitor.should_stop.is_set():
            time.sleep(1)  # Keep the main thread alive
        print_info("Server monitor has ended.")
    except KeyboardInterrupt:
        print_info("Stopping server...")
    finally:
        monitor.stop()

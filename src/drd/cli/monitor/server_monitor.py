import click
import time
import re
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
    def __init__(self, project_dir: str, error_handlers: dict, custom_command: str = None):
        self.project_dir = project_dir
        self.metadata_manager = ProjectMetadataManager(project_dir)
        self.error_handlers = error_handlers
        self.custom_command = custom_command
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

        if self.custom_command:
            start_command = self.custom_command
        else:
            dev_server_info = self.metadata_manager.get_dev_server_info()
            start_command = dev_server_info.get('start_command')
            if not start_command:
                raise ValueError("Server start command not found in metadata")

        click.echo(f"Starting server with command: {start_command}")
        self._start_process(start_command)

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
                        "\n No more tasks to auto-process. What can I do next?:")
                    idle_prompt_shown = True

            if self.restart_requested.is_set() and not self.processing_input.is_set():
                self._perform_restart()
                self.restart_requested.clear()

    def _handle_user_input(self, user_input):
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
            # Reset the last output time when user presses Enter without input
            self.last_output_time = time.time()

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
        if self.custom_command:
            self._start_process(self.custom_command)
        else:
            dev_server_info = self.metadata_manager.get_dev_server_info()
            start_command = dev_server_info.get('start_command')
            if not start_command:
                raise ValueError("Server start command not found in metadata")
            self._start_process(start_command)

        self.restart_requested.clear()
        print_success("Server restarted successfully.")
        print_info("Waiting for server output...")


def run_dev_server_with_monitoring(custom_command: str = None):
    print_info("Starting server monitor...")
    error_handlers = {
        r"(?:Cannot find module|Module not found|ImportError|No module named)": handle_module_not_found,
        r"(?:SyntaxError|Expected|Unexpected token)": handle_syntax_error,
        r"(?:Error:|Failed to compile)": handle_general_error,
    }
    current_dir = os.getcwd()
    monitor = DevServerMonitor(current_dir, error_handlers, custom_command)
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

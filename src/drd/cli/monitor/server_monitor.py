import threading
import subprocess
from queue import Queue
from .input_handler import InputHandler
from .output_monitor import OutputMonitor
from ...utils import print_info, print_success, print_error, print_header, print_prompt

MAX_RETRIES = 3


class DevServerMonitor:
    def __init__(self, project_dir: str, error_handlers: dict, command: str):
        self.project_dir = project_dir
        self.error_handlers = error_handlers
        self.command = command
        self.process = None
        self.output_queue = Queue()
        self.should_stop = threading.Event()
        self.restart_requested = threading.Event()
        self.user_input_queue = Queue()
        self.processing_input = threading.Event()
        self.input_handler = InputHandler(self)
        self.output_monitor = OutputMonitor(self)
        self.retry_count = 0

    def start(self):
        self.should_stop.clear()
        self.restart_requested.clear()
        print_header(
            f"Starting Dravid AI along with your process/server: {self.command}")
        try:
            self.process = start_process(self.command, self.project_dir)
            self.output_monitor.start()
            self.input_handler.start()
        except Exception as e:
            print_error(f"Failed to start server process: {str(e)}")
            self.stop()

    def request_restart(self):
        self.restart_requested.set()

    def perform_restart(self):
        print_info("Restarting server...")
        if self.process:
            self.process.terminate()
            self.process.wait()

        try:
            self.process = start_process(self.command, self.project_dir)
            self.retry_count = 0
            self.restart_requested.clear()
            print_success("Server restarted successfully.")
            print_info("Waiting for server output...")
        except Exception as e:
            print_error(f"Failed to restart server process: {str(e)}")
            self.retry_count += 1
            if self.retry_count >= MAX_RETRIES:
                print_error(
                    f"Server failed to start after {MAX_RETRIES} attempts. Exiting.")
                self.stop()
            else:
                print_info(
                    f"Retrying... (Attempt {self.retry_count + 1}/{MAX_RETRIES})")
                self.request_restart()

    def _start_process(self, command):
        try:
            return subprocess.Popen(
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
        except Exception as e:
            print_error(f"Failed to start server process: {str(e)}")
            self.stop()
            return None

    def stop(self):
        # Instead of directly calling graceful_shutdown, set a flag
        self.should_stop.set()
        # If we're not in the input handler thread, perform the shutdown
        if threading.current_thread() != self.input_handler.thread:
            self.graceful_shutdown()

    def graceful_shutdown(self):
        print_info("Initiating graceful shutdown...")

        # Stop input handler
        if self.input_handler.thread and self.input_handler.thread.is_alive():
            if threading.current_thread() != self.input_handler.thread:
                self.input_handler.thread.join(timeout=5)
            else:
                print_info(
                    "Skipping input handler thread join from within itself")

        # Stop output monitor
        if self.output_monitor.thread and self.output_monitor.thread.is_alive():
            self.output_monitor.thread.join(timeout=5)

        # Terminate the process
        if self.process:
            print_info("Terminating server process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print_prompt("Process did not terminate in time, forcing...")
                self.process.kill()

        print_success("Shutdown complete.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __enter__(self):
        self.start()
        return self


def start_process(command, cwd):
    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
        shell=True,
        cwd=cwd
    )

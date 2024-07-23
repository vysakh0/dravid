import time
import threading
import subprocess
from queue import Queue
from .input_handler import InputHandler
from .output_monitor import OutputMonitor
from ...utils import print_info, print_success, print_error, print_header, print_prompt
from ...metadata.project_metadata import ProjectMetadataManager


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
        self.metadata_manager = ProjectMetadataManager(project_dir)

    def start(self):
        self.should_stop.clear()
        self.restart_requested.clear()
        print_header(
            f"Starting Dravid AI along with your process/server: {self.command}")
        try:
            self.process = start_process(self.command, self.project_dir)
            self.output_monitor.start()
            self._main_loop()
        except Exception as e:
            print_error(f"Failed to start server process: {str(e)}")
            self.stop()

    def _main_loop(self):
        try:
            while not self.should_stop.is_set():
                if self.output_monitor.idle_detected.is_set():
                    self.input_handler.handle_input()
                    self.output_monitor.idle_detected.clear()
                time.sleep(0.1)  # Small sleep to prevent busy-waiting
        except KeyboardInterrupt:
            print_info("Stopping server...")
        finally:
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

    def stop(self):
        self.should_stop.set()
        if self.process:
            self.process.terminate()
            self.process.wait()
        if self.output_monitor.thread:
            self.output_monitor.thread.join()


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

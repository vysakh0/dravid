import threading
import subprocess
from queue import Queue
from .input_handler import InputHandler
from .output_monitor import OutputMonitor
from ...utils import print_info, print_success


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

    def start(self):
        self.should_stop.clear()
        self.restart_requested.clear()

        print_info(f"Starting server with command: {self.command}")
        self.process = start_process(self.command, self.project_dir)

        self.output_monitor.start()
        self.input_handler.start()

    def stop(self):
        self.should_stop.set()
        if self.process:
            self.process.terminate()
            self.process.wait()

    def request_restart(self):
        self.restart_requested.set()

    def perform_restart(self):
        print_info("Restarting server...")
        if self.process:
            self.process.terminate()
            self.process.wait()
        self.process = start_process(self.command, self.project_dir)
        self.restart_requested.clear()
        print_success("Server restarted successfully.")
        print_info("Waiting for server output...")


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

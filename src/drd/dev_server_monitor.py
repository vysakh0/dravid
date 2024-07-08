import subprocess
import re
import time
import threading
from queue import Queue, Empty
from typing import List, Dict, Callable
import click
import json
import os


class ProjectMetadataManager:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.metadata_file = os.path.join(self.project_dir, 'drd.json')
        self.metadata = self.load_metadata()

    def load_metadata(self):
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            "project_name": os.path.basename(self.project_dir),
            "last_updated": "",
            "files": [],
            "dev_server": {
                "start_command": [],
                "framework": "",
                "language": ""
            }
        }

    def get_dev_server_info(self):
        return self.metadata.get('dev_server', {})


class DevServerMonitor:
    def __init__(self, project_dir: str, error_handlers: Dict[str, Callable]):
        self.project_dir = project_dir
        self.metadata_manager = ProjectMetadataManager(project_dir)
        self.error_handlers = error_handlers
        self.process = None
        self.output_queue = Queue()
        self.should_stop = threading.Event()

    def start(self):
        dev_server_info = self.metadata_manager.get_dev_server_info()
        start_command = dev_server_info.get('start_command')

        if not start_command:
            raise ValueError("Dev server start command not found in drd.json")

        click.echo(
            f"Starting dev server with command: {' '.join(start_command)}")
        self.process = subprocess.Popen(
            start_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=self.project_dir
        )

        threading.Thread(target=self._enqueue_output, args=(
            self.process.stdout, self.output_queue), daemon=True).start()
        threading.Thread(target=self._monitor_output, daemon=True).start()

    def _enqueue_output(self, out, queue):
        for line in iter(out.readline, ''):
            queue.put(line)
        out.close()

    def _monitor_output(self):
        while not self.should_stop.is_set():
            try:
                line = self.output_queue.get(timeout=0.1)
                click.echo(line, nl=False)  # Print server output in real-time

                for error_pattern, handler in self.error_handlers.items():
                    if re.search(error_pattern, line):
                        handler(line)

            except Empty:
                continue

    def stop(self):
        self.should_stop.set()
        if self.process:
            self.process.terminate()
            self.process.wait()

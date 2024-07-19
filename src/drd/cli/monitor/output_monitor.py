import threading
import time
import re
import select
import sys
from ...utils import print_info


class OutputMonitor:
    def __init__(self, monitor):
        self.monitor = monitor
        self.thread = None
        self.last_output_time = time.time()
        self.idle_prompt_shown = False

    def start(self):
        self.thread = threading.Thread(
            target=self._monitor_output, daemon=True)
        self.thread.start()

    def _check_for_errors(self, line, error_buffer):
        for error_pattern, handler in self.monitor.error_handlers.items():
            if re.search(error_pattern, line, re.IGNORECASE):
                full_error = ''.join(error_buffer)
                handler(full_error, self.monitor)
                error_buffer.clear()
                break

    def _monitor_output(self):
        error_buffer = []
        iteration = 0
        self.last_output_time = time.time()  # Initialize last_output_time here
        while not self.monitor.should_stop.is_set():
            iteration += 1

            if self.monitor.process.poll() is not None and not self.monitor.processing_input.is_set():
                if not self.monitor.restart_requested.is_set():
                    print_info(
                        "Server process ended unexpectedly. Restarting...")
                    self.monitor.perform_restart()
                continue

            ready, _, _ = select.select(
                [self.monitor.process.stdout], [], [], 0.1)

            if self.monitor.process.stdout in ready:
                line = self.monitor.process.stdout.readline()
                if line:
                    print(line, end='', flush=True)
                    error_buffer.append(line)
                    if len(error_buffer) > 10:
                        error_buffer.pop(0)
                    self.last_output_time = time.time()
                    self.idle_prompt_shown = False

                    if not self.monitor.processing_input.is_set():
                        self._check_for_errors(line, error_buffer)
                else:
                    self._check_idle_state()
            else:
                self._check_idle_state()

            if self.monitor.restart_requested.is_set() and not self.monitor.processing_input.is_set():
                self.monitor.perform_restart()

    def _check_idle_state(self):
        current_time = time.time()
        time_since_last_output = current_time - self.last_output_time
        if (time_since_last_output > 5 and
            not self.idle_prompt_shown and
                not self.monitor.processing_input.is_set()):
            print_info("\nNo more tasks to auto-process. What can I do next?")
            self._show_options()
            self.idle_prompt_shown = True

    def _show_options(self):
        print_info("\nAvailable actions:")
        print_info("1. Ask a question or give an instruction")
        print_info("2. Process an image (type 'vision')")
        print_info("3. Exit monitoring mode (type 'exit')")
        print_info("\nType your choice or command:")
        print("> ", end="", flush=True)

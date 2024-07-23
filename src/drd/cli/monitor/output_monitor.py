import re
import time
import select
import threading

from ...utils import print_info, print_error


class OutputMonitor:
    def __init__(self, monitor):
        self.monitor = monitor
        self.thread = None
        self.last_output_time = None
        self.idle_detected = threading.Event()

    def start(self):
        self.thread = threading.Thread(
            target=self._monitor_output, daemon=True)
        self.thread.start()

    def _monitor_output(self):
        error_buffer = []
        self.last_output_time = time.time()
        while not self.monitor.should_stop.is_set():
            if self.monitor.process.poll() is not None and not self.monitor.processing_input.is_set():
                if not self.monitor.restart_requested.is_set():
                    print_info("Server process ended unexpectedly.")
                    if self.monitor.retry_count < self.monitor.MAX_RETRIES:
                        self.monitor.retry_count += 1
                        print_info(
                            f"Restarting... (Attempt {self.monitor.retry_count}/{self.monitor.MAX_RETRIES})")
                        self.monitor.perform_restart()
                        return  # Exit the method after attempting restart
                    else:
                        print_error(
                            f"Server failed to start after {self.monitor.MAX_RETRIES} attempts. Exiting.")
                        self.monitor.stop()
                        break
                else:
                    break  # Exit the loop if restart is already requested

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
                    self.monitor.retry_count = 0  # Reset retry count on successful output
                    if not self.monitor.processing_input.is_set():
                        self._check_for_errors(line, error_buffer)
                else:
                    self._check_idle_state()
            else:
                self._check_idle_state()

            if self.monitor.restart_requested.is_set() and not self.monitor.processing_input.is_set():
                self.monitor.perform_restart()
                return

    def _check_for_errors(self, line, error_buffer):
        for error_pattern, handler in self.monitor.error_handlers.items():
            if re.search(error_pattern, line, re.IGNORECASE):
                full_error = ''.join(error_buffer)
                handler(full_error, self.monitor)
                error_buffer.clear()
                break

    def _check_idle_state(self):
        current_time = time.time()
        if (current_time - self.last_output_time > 5 and
                not self.monitor.processing_input.is_set()):
            self.idle_detected.set()

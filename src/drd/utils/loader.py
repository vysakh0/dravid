import click
import time
import threading


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
            click.echo(
                f'\r{self.message} {self.animation[self.idx % len(self.animation)]}', nl=False)
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

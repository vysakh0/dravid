import threading
from typing import Callable, Union
import click
from colorama import Fore, Style


class UniversalInputHandler:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(
                        UniversalInputHandler, cls).__new__(cls)
                    cls._instance.error_resolution_in_progress = threading.Event()
                    cls._instance.custom_input_function = None
        return cls._instance

    def set_custom_input_function(self, func: Callable[[str], str]):
        self.custom_input_function = func

    def get_user_input(self, prompt: str, input_type: str = 'text') -> Union[str, bool]:
        with self._lock:
            try:
                if self.custom_input_function:
                    return self.custom_input_function(prompt)

                if input_type == 'confirm':
                    return click.confirm(f"\n{Fore.YELLOW}{prompt}{Style.RESET_ALL}", default=False)
                elif input_type == 'choice':
                    return click.prompt(f"\n{Fore.YELLOW}{prompt}{Style.RESET_ALL}", type=str).strip().lower()
                else:  # text input
                    return click.prompt(f"{Fore.YELLOW}{prompt}{Style.RESET_ALL}", type=str)
            except click.Abort:
                print("\nInput aborted by user.")
                return ''
            except EOFError:
                print("\nEOF detected. Exiting.")
                return 'exit'

    def is_error_resolution_in_progress(self):
        return self.error_resolution_in_progress.is_set()

    def set_error_resolution_in_progress(self, value: bool):
        if value:
            self.error_resolution_in_progress.set()
        else:
            self.error_resolution_in_progress.clear()

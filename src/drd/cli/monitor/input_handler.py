import threading
import click
import os
import glob
from .input_parser import InputParser
from ...utils import print_info, print_error
from ...prompts.instructions import get_instruction_prompt
from ...utils.file_utils import clean_path
from ..query.main import execute_dravid_command


class InputHandler:
    def __init__(self, monitor):
        self.monitor = monitor
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._handle_input, daemon=True)
        self.thread.start()

    def _handle_input(self):
        while not self.monitor.should_stop.is_set():
            user_input = input("> ").strip()
            if user_input.lower() == 'exit':
                print_info("Exiting server monitor...")
                self.monitor.stop()
                break
            self._process_input(user_input)

    def _process_input(self, user_input):
        if user_input.lower() == 'p':
            self._handle_vision_input()
            return
        if user_input:
            self.monitor.processing_input.set()
            try:
                self._handle_general_input(user_input)
            finally:
                self.monitor.processing_input.clear()

    def _handle_vision_input(self):
        print_info(
            "Enter the image path and instructions (use Tab for autocomplete):")
        user_input = self._get_input_with_autocomplete()
        self.monitor.processing_input.set()
        try:
            self._handle_general_input(user_input)
        finally:
            self.monitor.processing_input.clear()

    def _handle_general_input(self, user_input):
        instruction_prompt = get_instruction_prompt()
        input_parser = InputParser()
        image_path, instructions, reference_files = input_parser.parse_input(
            user_input)

        if image_path is None and not instructions and not reference_files:
            print_error(
                "Failed to parse input. Please check your input and try again.")
            return

        if image_path:
            print_info(f"Processing image: {image_path}")
            if not os.path.exists(image_path):
                print_error("Image path not found. Please check and try again")
                return

        if reference_files:
            print_info(f"Reference files: {', '.join(reference_files)}")
        print_info(f"Instructions: {instructions}")

        if not instructions and not image_path and not reference_files:
            print_error(
                "No valid input detected. Please provide instructions, file paths, or an image path.")
            return

        execute_dravid_command(
            instructions, image_path, debug=False, instruction_prompt=instruction_prompt, warn=False, reference_files=reference_files)

    def _handle_vision_input(self):
        print_info(
            "Enter the image path and instructions (use Tab for autocomplete):")
        user_input = self._get_input_with_autocomplete()
        self.monitor.processing_input.set()
        try:
            self._handle_general_input(user_input)
        finally:
            self.monitor.processing_input.clear()

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

import threading
import click
import os
import glob
from ...utils import print_info, print_error
from ...prompts.instructions import get_instruction_prompt
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
            self._process_input(user_input)

    def _process_input(self, user_input):
        if user_input.lower() == 'exit':
            print_info("Exiting server monitor...")
            self.monitor.stop()
            return

        if user_input.lower() == 'vision':
            self._handle_vision_input()
            return

        if user_input:
            self.monitor.processing_input.set()
            try:
                print_info(f"Processing input: {user_input}")
                instruction_prompt = get_instruction_prompt()
                execute_dravid_command(
                    user_input, None, False, instruction_prompt, warn=False)
            except Exception as e:
                print_error(f"Error processing input: {str(e)}")
            finally:
                self.monitor.processing_input.clear()
                print_info(
                    "\nCommand execution completed. Returning to server monitoring...")

    def _handle_vision_input(self):
        print_info("Enter the path to the image file (use Tab for autocomplete):")
        image_path = self._get_input_with_autocomplete()

        if not os.path.exists(image_path):
            print_error(f"Image file not found: {image_path}")
            return

        print_info("Enter your instructions for the image:")
        instructions = input("> ").strip()

        self.monitor.processing_input.set()
        try:
            print_info(f"Processing image: {image_path}")
            print_info(f"With instructions: {instructions}")
            instruction_prompt = get_instruction_prompt()
            execute_dravid_command(
                instructions, image_path, False, instruction_prompt, warn=False)
        except Exception as e:
            print_error(f"Error processing image input: {str(e)}")
        finally:
            self.monitor.processing_input.clear()
            print_info(
                "\nImage processing completed. Returning to server monitoring...")

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

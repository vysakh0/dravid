import re
import os
from ...utils.file_utils import clean_path
from ...utils import print_error, print_debug


class InputParser:
    def __init__(self):
        self.image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        self.file_pattern = r'(?<![\w\'\"])([a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*|(?:/(?:[^\s/\\]+|\\\ )+)+)(?:\.[a-zA-Z0-9]+)?(?![\w\'\"])'

    def parse_input(self, user_input):
        print_debug(f"Parsing input: {user_input}")
        print_debug(f"File pattern: {self.file_pattern}")
        try:
            # Find all file path matches
            file_matches = list(re.finditer(self.file_pattern, user_input))
            print_debug(f"File matches: {file_matches}")

            # Extract and validate all file paths
            valid_file_paths = []
            for match in file_matches:
                path = self.unescape_path(match.group(0))
                cleaned_path = clean_path(path)
                if cleaned_path and os.path.exists(cleaned_path):
                    valid_file_paths.append(cleaned_path)
                else:
                    print_error(f"File not found: {cleaned_path}")

            print_debug(f"Valid file paths: {valid_file_paths}")

            # Separate image path and other file paths
            image_path = next((path for path in valid_file_paths if path.lower().endswith(
                self.image_extensions)), None)
            file_paths = [
                path for path in valid_file_paths if path != image_path]

            print_debug(f"Extracted image path: {image_path}")
            print_debug(f"Extracted file paths: {file_paths}")

            # Remove all matched paths from the input to get the instructions
            instructions = user_input
            for match in file_matches:
                instructions = instructions.replace(match.group(0), "")

            # Clean up instructions
            instructions = " ".join(instructions.split())
            print_debug(f"Extracted instructions: {instructions}")

            return image_path, instructions, file_paths

        except Exception as e:
            print_error(f"Error in parse_input: {str(e)}")
            return None, user_input, []

    @staticmethod
    def unescape_path(path):
        return path.replace('\\ ', ' ')

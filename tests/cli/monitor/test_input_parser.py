import unittest
import tempfile
import os
from drd.cli.monitor.input_parser import InputParser


class TestInputParser(unittest.TestCase):
    def setUp(self):
        self.parser = InputParser()
        self.temp_dir = tempfile.mkdtemp()
        print(f"Created temp directory: {self.temp_dir}")

    def tearDown(self):
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
        print(f"Removed temp directory: {self.temp_dir}")

    def create_temp_file(self, filename):
        path = os.path.join(self.temp_dir, filename)
        with open(path, 'w') as f:
            f.write('test')
        print(f"Created temp file: {path}")
        return path

    def escape_path(self, path):
        return path.replace(' ', '\\ ')

    def test_image_path_with_spaces(self):
        image_path = self.create_temp_file('test image.jpg')
        escaped_path = self.escape_path(image_path)
        user_input = f"This is a test {escaped_path} with some text"
        print(f"User input: {user_input}")
        image, instructions, files = self.parser.parse_input(user_input)
        print(f"Parsed image: {image}")
        print(f"Parsed instructions: {instructions}")
        print(f"Parsed files: {files}")
        self.assertEqual(image, image_path)
        self.assertEqual(instructions, "This is a test with some text")
        self.assertEqual(files, [])

    def test_image_path_with_spaces_beginning(self):
        image_path = self.create_temp_file('test image.jpg')
        escaped_path = self.escape_path(image_path)
        user_input = f"{escaped_path} with some text"
        print(f"User input: {user_input}")
        image, instructions, files = self.parser.parse_input(user_input)
        print(f"Parsed image: {image}")
        print(f"Parsed instructions: {instructions}")
        print(f"Parsed files: {files}")
        self.assertEqual(image, image_path)
        self.assertEqual(instructions, "with some text")
        self.assertEqual(files, [])

    def test_simple_image_and_text(self):
        image_path = self.create_temp_file('testimage.jpg')
        escaped_path = self.escape_path(image_path)
        user_input = f"This is a test {escaped_path} with some text"
        print(f"User input: {user_input}")
        image, instructions, files = self.parser.parse_input(user_input)
        print(f"Parsed image: {image}")
        print(f"Parsed instructions: {instructions}")
        print(f"Parsed files: {files}")
        self.assertEqual(image, image_path)
        self.assertEqual(instructions, "This is a test with some text")
        self.assertEqual(files, [])

    def test_simple_file(self):
        file_path = self.create_temp_file('testfile.txt')
        escaped_path = self.escape_path(file_path)
        user_input = f"This is a test {escaped_path} with some text"
        print(f"User input: {user_input}")
        image, instructions, files = self.parser.parse_input(user_input)
        print(f"Parsed image: {image}")
        print(f"Parsed instructions: {instructions}")
        print(f"Parsed files: {files}")
        self.assertIsNone(image)
        self.assertEqual(instructions, "This is a test with some text")
        self.assertEqual(files, [file_path])

    def test_file_with_spaces(self):
        file_path = self.create_temp_file('test file.txt')
        escaped_path = self.escape_path(file_path)
        user_input = f"This is a test {escaped_path} with some text"
        print(f"User input: {user_input}")
        image, instructions, files = self.parser.parse_input(user_input)
        print(f"Parsed image: {image}")
        print(f"Parsed instructions: {instructions}")
        print(f"Parsed files: {files}")
        self.assertIsNone(image)
        self.assertEqual(instructions, "This is a test with some text")
        self.assertEqual(files, [file_path])

    def test_image_and_file(self):
        image_path = self.create_temp_file('testimage.jpg')
        file_path = self.create_temp_file('testfile.txt')
        escaped_image_path = self.escape_path(image_path)
        escaped_file_path = self.escape_path(file_path)
        user_input = f"This is a test {escaped_image_path} and a file {escaped_file_path} with some text"
        image, instructions, files = self.parser.parse_input(user_input)
        self.assertEqual(image, image_path)
        self.assertEqual(
            instructions, "This is a test and a file with some text")
        self.assertEqual(files, [file_path])

    def test_multiple_files_no_image(self):
        file_path1 = self.create_temp_file('test_file1.txt')
        file_path2 = self.create_temp_file('test_file2.txt')
        escaped_path1 = self.escape_path(file_path1)
        escaped_path2 = self.escape_path(file_path2)
        user_input = f"Process these files: {escaped_path1} and {escaped_path2}"
        image, instructions, files = self.parser.parse_input(user_input)
        self.assertIsNone(image)
        self.assertEqual(instructions, "Process these files: and")
        self.assertEqual(set(files), {file_path1, file_path2})

    def test_no_image_or_file_path(self):
        user_input = "This is a simple text without any file paths."
        image, instructions, files = self.parser.parse_input(user_input)
        self.assertIsNone(image)
        self.assertEqual(instructions, user_input)
        self.assertEqual(files, [])

    def test_non_existent_file_path(self):
        non_existent_path = os.path.join(
            self.temp_dir, "non_existent_file.txt")
        escaped_path = self.escape_path(non_existent_path)
        user_input = f"Try to process this non-existent file: {escaped_path}"
        image, instructions, files = self.parser.parse_input(user_input)
        self.assertIsNone(image)
        res = "Try to process this non-existent file:"
        self.assertEqual(instructions, res)
        self.assertEqual(files, [])

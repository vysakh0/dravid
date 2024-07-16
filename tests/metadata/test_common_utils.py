import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import re
import xml.etree.ElementTree as ET

from drd.metadata.common_utils import (
    parse_gitignore,
    should_ignore,
    get_folder_structure,
    get_ignore_patterns,
    generate_file_description,
    find_file_with_dravid
)


class TestCommonUtils(unittest.TestCase):

    def setUp(self):
        self.gitignore_content = """
# Comment
*.pyc
/node_modules/
build/
"""
        self.folder_structure = """
project/
    src/
        main.py
        utils.py
    tests/
        test_main.py
    .gitignore
    README.md
"""

    @patch('os.path.exists')
    def test_parse_gitignore(self, path_exists):
        with patch('builtins.open', mock_open(read_data=self.gitignore_content)):
            patterns = parse_gitignore('fake/.gitignore')
            print("patterns", patterns)

        print(f"Parsed patterns: {patterns}")  # Debug print

        self.assertEqual(len(patterns), 3,
                         f"Expected 3 patterns, got {len(patterns)}")

        # Test each pattern individually
        self.assertTrue(any(pattern.search('file.pyc')
                        for pattern in patterns), "*.pyc pattern not found")
        self.assertTrue(any(pattern.search('node_modules/file.js')
                        for pattern in patterns), "/node_modules/ pattern not found")
        self.assertTrue(any(pattern.search('build/output.txt')
                        for pattern in patterns), "build/ pattern not found")

        # Print out each compiled pattern
        for i, pattern in enumerate(patterns):
            print(f"Pattern {i + 1}: {pattern.pattern}")

    def test_should_ignore(self):
        patterns = [
            re.compile(r'.*\.pyc'),
            re.compile(r'^node_modules/.*'),
            re.compile(r'.*build/.*')
        ]

        self.assertTrue(should_ignore('file.pyc', patterns))
        self.assertTrue(should_ignore('node_modules/file.js', patterns))
        self.assertTrue(should_ignore('path/to/build/output.txt', patterns))
        self.assertFalse(should_ignore('src/main.py', patterns))

    @patch('os.walk')
    def test_get_folder_structure(self, mock_walk):
        mock_walk.return_value = [
            ('/project', ['src', 'tests'], ['.gitignore', 'README.md']),
            ('/project/src', [], ['main.py', 'utils.py']),
            ('/project/tests', [], ['test_main.py'])
        ]

        ignore_patterns = [re.compile(r'.*\.gitignore')]
        structure = get_folder_structure('/project', ignore_patterns)

        self.assertIn('project/', structure)
        self.assertIn('    src/', structure)
        self.assertIn('        main.py', structure)
        self.assertIn('    tests/', structure)
        self.assertIn('    README.md', structure)
        self.assertNotIn('.gitignore', structure)

    @patch('os.path.exists')
    def test_get_ignore_patterns(self, mock_exists):
        mock_exists.return_value = True
        with patch('builtins.open', mock_open(read_data=self.gitignore_content)):
            patterns, message = get_ignore_patterns('/fake/path')

        self.assertEqual(len(patterns), 4)  # 3 from .gitignore + 1 for .git
        self.assertIn("Using .gitignore patterns for file exclusion.", message)

        mock_exists.return_value = False
        patterns, message = get_ignore_patterns('/fake/path')

        self.assertEqual(len(patterns), 6)  # Default patterns
        self.assertIn(
            "No .gitignore found. Using default ignore patterns.", message)

    @patch('drd.metadata.common_utils.call_dravid_api_with_pagination')
    @patch('drd.metadata.common_utils.extract_and_parse_xml')
    def test_generate_file_description(self, mock_extract_xml, mock_call_api):
        mock_call_api.return_value = "<response><metadata><type>python</type><description>A test file</description><exports>test_function</exports></metadata></response>"
        mock_root = ET.fromstring(mock_call_api.return_value)
        mock_extract_xml.return_value = mock_root

        file_type, description, exports = generate_file_description(
            "test.py", "print('Hello')", "Test project", self.folder_structure)

        self.assertEqual(file_type, "python")
        self.assertEqual(description, "A test file")
        self.assertEqual(exports, "test_function")

    @patch('os.path.exists')
    @patch('drd.metadata.common_utils.call_dravid_api_with_pagination')
    @patch('drd.metadata.common_utils.extract_and_parse_xml')
    def test_find_file_with_dravid(self, mock_extract_xml, mock_call_api, mock_exists):
        mock_exists.side_effect = [False, True]
        mock_call_api.return_value = "<response><file>src/main.py</file></response>"
        mock_root = ET.fromstring(mock_call_api.return_value)
        mock_extract_xml.return_value = mock_root

        result = find_file_with_dravid(
            "main.py", "Test project", self.folder_structure)

        self.assertEqual(result, "src/main.py")

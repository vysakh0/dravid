import unittest
from unittest.mock import patch, mock_open
import os
from drd.utils.file_utils import (
    get_file_content,
    fetch_project_guidelines
)


class TestFileOperations(unittest.TestCase):
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="file content\nsecond line")
    def test_get_file_content_existing_file(self, mock_file, mock_exists):
        mock_exists.return_value = True
        result = get_file_content("test.txt")
        expected_result = "1: file content\n2: second line"
        self.assertEqual(result, expected_result)

    @patch('os.path.exists')
    def test_get_file_content_non_existing_file(self, mock_exists):
        mock_exists.return_value = False
        result = get_file_content("non_existing.txt")
        self.assertIsNone(result)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="Project guidelines content\nSecond guideline")
    @patch('drd.utils.file_utils.print_info')
    def test_fetch_project_guidelines_existing_file(self, mock_print_info, mock_file, mock_exists):
        mock_exists.return_value = True
        result = fetch_project_guidelines("/fake/project/dir")
        expected_result = "Project guidelines content\nSecond guideline"
        self.assertEqual(result, expected_result)
        mock_print_info.assert_called_once_with(
            "Project guidelines found and included in the context.")

    @patch('os.path.exists')
    def test_fetch_project_guidelines_non_existing_file(self, mock_exists):
        mock_exists.return_value = False
        result = fetch_project_guidelines("/fake/project/dir")
        self.assertEqual(result, "")

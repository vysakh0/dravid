from src.drd.cli.query.file_operations import get_files_to_modify, get_file_content, find_file_with_dravid
import unittest
from unittest.mock import patch, mock_open
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..')))

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..')))


class TestFileOperations(unittest.TestCase):

    @patch('src.drd.cli.query.file_operations.call_dravid_api')
    def test_get_files_to_modify(self, mock_call_dravid_api):
        mock_call_dravid_api.return_value = """
        <response>
          <files>
            <file>path/to/file1.ext</file>
            <file>path/to/file2.ext</file>
          </files>
        </response>
        """
        result = get_files_to_modify("Test query", "Test project context")
        self.assertEqual(result, ['path/to/file1.ext', 'path/to/file2.ext'])

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='file content')
    def test_get_file_content_existing_file(self, mock_file, mock_exists):
        mock_exists.return_value = True
        content = get_file_content('existing_file.txt')
        self.assertEqual(content, 'file content')
        mock_file.assert_called_once_with('existing_file.txt', 'r')

    @patch('os.path.exists')
    def test_get_file_content_non_existing_file(self, mock_exists):
        mock_exists.return_value = False
        content = get_file_content('non_existing_file.txt')
        self.assertIsNone(content)

    @patch('os.path.exists')
    @patch('src.drd.cli.query.file_operations.call_dravid_api')
    def test_find_file_with_dravid_existing_file(self, mock_call_dravid_api, mock_exists):
        mock_exists.return_value = True
        result = find_file_with_dravid(
            'existing_file.txt', 'Test project context')
        self.assertEqual(result, 'existing_file.txt')

    @patch('os.path.exists')
    @patch('src.drd.cli.query.file_operations.call_dravid_api')
    def test_find_file_with_dravid_non_existing_file(self, mock_call_dravid_api, mock_exists):
        mock_exists.side_effect = [False, True]
        mock_call_dravid_api.return_value = """
        <response>
          <file>suggested/path/to/file.txt</file>
        </response>
        """
        result = find_file_with_dravid(
            'non_existing_file.txt', 'Test project context')
        self.assertEqual(result, 'suggested/path/to/file.txt')

    @patch('os.path.exists')
    @patch('src.drd.cli.query.file_operations.call_dravid_api')
    def test_find_file_with_dravid_max_retries(self, mock_call_dravid_api, mock_exists):
        mock_exists.return_value = False
        mock_call_dravid_api.return_value = """
        <response>
          <file></file>
        </response>
        """
        result = find_file_with_dravid(
            'non_existing_file.txt', 'Test project context')
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

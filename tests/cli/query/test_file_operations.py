import unittest
from unittest.mock import patch, MagicMock
import os

from drd.cli.query.file_operations import get_files_to_modify, find_file_with_dravid


class TestFileOperations(unittest.TestCase):

    def setUp(self):
        self.project_context = "This is a sample project context"

    @patch('drd.cli.query.file_operations.call_dravid_api_with_pagination')
    @patch('drd.cli.query.file_operations.parse_file_list_response')
    def test_get_files_to_modify(self, mock_parse_response, mock_call_api):
        query = "Update the main function"
        mock_call_api.return_value = "<response><files><file>main.py</file><file>utils.py</file></files></response>"
        mock_parse_response.return_value = ['main.py', 'utils.py']

        result = get_files_to_modify(query, self.project_context)

        mock_call_api.assert_called_once()
        mock_parse_response.assert_called_once_with(mock_call_api.return_value)
        self.assertEqual(result, ['main.py', 'utils.py'])

    @patch('os.path.exists')
    @patch('drd.cli.query.file_operations.ProjectMetadataManager')
    @patch('drd.cli.query.file_operations.call_dravid_api_with_pagination')
    @patch('drd.cli.query.file_operations.parse_find_file_response')
    @patch('drd.cli.query.file_operations.print_info')
    @patch('drd.cli.query.file_operations.print_error')
    def test_find_file_with_dravid_existing_file(self, mock_print_error, mock_print_info,
                                                 mock_parse_response, mock_call_api,
                                                 mock_metadata_manager, mock_exists):
        mock_exists.return_value = True
        filename = 'existing_file.py'

        result = find_file_with_dravid(filename, self.project_context)

        self.assertEqual(result, filename)
        mock_call_api.assert_not_called()

    @patch('os.path.exists')
    @patch('drd.cli.query.file_operations.ProjectMetadataManager')
    @patch('drd.cli.query.file_operations.call_dravid_api_with_pagination')
    @patch('drd.cli.query.file_operations.parse_find_file_response')
    @patch('drd.cli.query.file_operations.print_info')
    @patch('drd.cli.query.file_operations.print_error')
    def test_find_file_with_dravid_suggested_file(self, mock_print_error, mock_print_info,
                                                  mock_parse_response, mock_call_api,
                                                  mock_metadata_manager, mock_exists):
        mock_exists.side_effect = [False, True]
        mock_metadata_manager.return_value.get_project_context.return_value = "Project metadata"
        mock_call_api.return_value = "<response><file>suggested_file.py</file></response>"
        mock_parse_response.return_value = "suggested_file.py"

        result = find_file_with_dravid(
            'non_existing_file.py', self.project_context)

        self.assertEqual(result, 'suggested_file.py')
        mock_call_api.assert_called_once()
        mock_print_info.assert_called_once_with(
            "Dravid suggested an alternative file: suggested_file.py")

    @patch('os.path.exists')
    @patch('drd.cli.query.file_operations.ProjectMetadataManager')
    @patch('drd.cli.query.file_operations.call_dravid_api_with_pagination')
    @patch('drd.cli.query.file_operations.parse_find_file_response')
    @patch('drd.cli.query.file_operations.print_info')
    @patch('drd.cli.query.file_operations.print_error')
    def test_find_file_with_dravid_no_suggestion(self, mock_print_error, mock_print_info,
                                                 mock_parse_response, mock_call_api,
                                                 mock_metadata_manager, mock_exists):
        mock_exists.return_value = False
        mock_metadata_manager.return_value.get_project_context.return_value = "Project metadata"
        mock_call_api.return_value = "<response></response>"
        mock_parse_response.return_value = None

        result = find_file_with_dravid(
            'non_existing_file.py', self.project_context)

        self.assertIsNone(result)
        mock_call_api.assert_called_once()
        mock_print_error.assert_called_with(
            "Dravid couldn't suggest an alternative file.")

import unittest
from unittest.mock import patch, MagicMock
from drd.cli.monitor.error_resolver import monitoring_handle_error_with_dravid


class TestErrorResolver(unittest.TestCase):
    def setUp(self):
        self.error = Exception("Test error")
        self.line = "Error line from server output"
        self.monitor = MagicMock()
        self.monitor.metadata_manager.get_project_context.return_value = "Test project context"

    @patch('drd.cli.monitor.error_resolver.call_dravid_api')
    @patch('drd.cli.monitor.error_resolver.Executor')
    @patch('drd.cli.monitor.error_resolver.get_files_to_modify')
    @patch('drd.cli.monitor.error_resolver.get_file_content')
    def test_monitoring_handle_error_with_dravid_apply_fix(self, mock_get_file_content, mock_get_files_to_modify, mock_executor, mock_call_api):
        # Setup mocks
        mock_get_files_to_modify.return_value = ['test_file.py']
        mock_get_file_content.return_value = "Test file content"
        mock_call_api.return_value = [
            {'type': 'shell', 'command': 'echo "Fix applied"'},
            {'type': 'file', 'operation': 'CREATE',
                'filename': 'test.txt', 'content': 'Test content'}
        ]
        self.monitor.get_user_input.return_value = 'y'

        # Call the function
        result = monitoring_handle_error_with_dravid(
            self.error, self.line, self.monitor)

        # Assertions
        self.assertTrue(result)
        mock_call_api.assert_called_once()
        mock_executor.return_value.execute_shell_command.assert_called_once_with(
            'echo "Fix applied"')
        mock_executor.return_value.perform_file_operation.assert_called_once_with(
            'CREATE', 'test.txt', 'Test content')
        self.monitor.request_restart.assert_called_once()

    @patch('drd.cli.monitor.error_resolver.call_dravid_api')
    @patch('drd.cli.monitor.error_resolver.get_files_to_modify')
    @patch('drd.cli.monitor.error_resolver.get_file_content')
    def test_monitoring_handle_error_with_dravid_no_apply_fix(self, mock_get_file_content, mock_get_files_to_modify, mock_call_api):
        # Setup mocks
        mock_get_files_to_modify.return_value = ['test_file.py']
        mock_get_file_content.return_value = "Test file content"
        mock_call_api.return_value = [
            {'type': 'shell', 'command': 'echo "Fix not applied"'}]
        self.monitor.get_user_input.return_value = 'n'

        # Call the function
        result = monitoring_handle_error_with_dravid(
            self.error, self.line, self.monitor)

        # Assertions
        self.assertFalse(result)
        mock_call_api.assert_called_once()

    @patch('drd.cli.monitor.error_resolver.call_dravid_api')
    @patch('drd.cli.monitor.error_resolver.get_files_to_modify')
    @patch('drd.cli.monitor.error_resolver.get_file_content')
    def test_monitoring_handle_error_with_dravid_parse_error(self, mock_get_file_content, mock_get_files_to_modify, mock_call_api):
        # Setup mocks
        mock_get_files_to_modify.return_value = ['test_file.py']
        mock_get_file_content.return_value = "Test file content"
        mock_call_api.side_effect = ValueError("Parse error")

        # Call the function
        result = monitoring_handle_error_with_dravid(
            self.error, self.line, self.monitor)

        # Assertions
        self.assertFalse(result)
        mock_call_api.assert_called_once()

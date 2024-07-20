import unittest
from unittest.mock import patch, MagicMock, call
import requests

from drd.cli.query.main import execute_dravid_command


class TestExecuteDravidCommand(unittest.TestCase):

    def setUp(self):
        self.executor = MagicMock()
        self.metadata_manager = MagicMock()
        self.query = "Test query"
        self.image_path = None
        self.debug = False
        self.instruction_prompt = None

    @patch('drd.cli.query.main.Executor')
    @patch('drd.cli.query.main.ProjectMetadataManager')
    @patch('drd.cli.query.main.stream_dravid_api')
    @patch('drd.cli.query.main.execute_commands')
    @patch('drd.cli.query.main.print_debug')
    @patch('drd.cli.query.main.print_error')
    @patch('drd.cli.query.main.get_files_to_modify')
    @patch('drd.cli.query.main.run_with_loader')
    def test_execute_dravid_command_debug_mode(self, mock_run_with_loader, mock_get_files, mock_print_error,
                                               mock_print_debug, mock_execute_commands, mock_stream_api,
                                               mock_metadata_manager, mock_executor):
        self.debug = True
        mock_executor.return_value = self.executor
        mock_metadata_manager.return_value = self.metadata_manager
        self.metadata_manager.get_project_context.return_value = "Test project context"
        mock_get_files.return_value = ["file1.py", "file2.py"]

        mock_stream_api.return_value = """
        <response>
            <steps>
                <step>
                    <type>shell</type>
                    <command> echo "hello" </command>
                </step>
                <step>
                    <type>file</type>
                    <operation>CREATE</operation>
                    <filename>text.txt</filename>
                    <content>Test content</content>
                </step>
            </steps>
        </response>
        """
        mock_execute_commands.return_value = (
            True, 2, None, "All commands executed successfully")
        mock_run_with_loader.side_effect = lambda f, *args, **kwargs: f()

        execute_dravid_command(self.query, self.image_path,
                               self.debug, self.instruction_prompt)

        mock_print_debug.assert_has_calls([
            call("Received 2 new command(s)")
        ])

    @patch('drd.cli.query.main.Executor')
    @patch('drd.cli.query.main.ProjectMetadataManager')
    @patch('drd.cli.query.main.stream_dravid_api')
    @patch('drd.cli.query.main.execute_commands')
    @patch('drd.cli.query.main.handle_error_with_dravid')
    @patch('drd.cli.query.main.print_error')
    @patch('drd.cli.query.main.print_info')
    @patch('drd.cli.query.main.get_files_to_modify')
    @patch('drd.cli.query.main.run_with_loader')
    def test_execute_dravid_command_with_error(self, mock_run_with_loader, mock_get_files, mock_print_info,
                                               mock_print_error, mock_handle_error, mock_execute_commands,
                                               mock_stream_api, mock_metadata_manager, mock_executor):
        mock_executor.return_value = self.executor
        mock_metadata_manager.return_value = self.metadata_manager
        self.metadata_manager.get_project_context.return_value = "Test project context"
        mock_get_files.return_value = ["file1.py", "file2.py"]
        mock_stream_api.return_value = """
        <response>
            <explanation>Test explanation</explanation>
            <steps>
                <step>
                    <type>shell</type>
                    <command> echo "hello" </command>
                </step>
            </steps>
        </response>
        """
        mock_execute_commands.return_value = (
            False, 1, "Command failed", "Error output")
        mock_handle_error.return_value = True
        mock_run_with_loader.side_effect = lambda f, *args, **kwargs: f()

        execute_dravid_command(self.query, self.image_path,
                               self.debug, self.instruction_prompt)

        mock_print_error.assert_any_call(
            "Failed to execute command at step 1.")
        mock_handle_error.assert_called_once()
        mock_print_info.assert_any_call(
            "Fix applied successfully. Continuing with the remaining commands.", indent=2)

    @patch('drd.cli.query.main.Executor')
    @patch('drd.cli.query.main.ProjectMetadataManager')
    @patch('drd.cli.query.main.call_dravid_vision_api')
    @patch('drd.cli.query.main.execute_commands')
    @patch('drd.cli.query.main.print_info')
    @patch('drd.cli.query.main.print_warning')
    @patch('drd.cli.query.main.run_with_loader')
    @patch('drd.cli.query.main.get_files_to_modify')  # Add this line
    def test_execute_dravid_command_with_image(self, mock_get_files, mock_run_with_loader,
                                               mock_print_warning, mock_print_info,
                                               mock_execute_commands, mock_call_vision_api,
                                               mock_metadata_manager, mock_executor):
        self.image_path = "test_image.jpg"
        mock_executor.return_value = self.executor
        mock_metadata_manager.return_value = self.metadata_manager
        self.metadata_manager.get_project_context.return_value = "Test project context"
        mock_call_vision_api.return_value = [
            {'type': 'shell', 'command': 'echo "Image processed"'}]
        mock_execute_commands.return_value = (
            True, 1, None, "Image command executed successfully")
        mock_run_with_loader.side_effect = lambda f, *args, **kwargs: f()
        mock_get_files.return_value = []  # Add this line

        execute_dravid_command(self.query, self.image_path,
                               self.debug, self.instruction_prompt)

        mock_call_vision_api.assert_called_once()
        mock_print_info.assert_any_call(
            f"Processing image: {self.image_path}", indent=4)

    @patch('drd.cli.query.main.Executor')
    @patch('drd.cli.query.main.ProjectMetadataManager')
    @patch('drd.cli.query.main.get_files_to_modify')
    @patch('drd.cli.query.main.print_error')
    @patch('drd.cli.query.main.run_with_loader')
    def test_execute_dravid_command_api_error(self, mock_run_with_loader, mock_print_error, mock_get_files,
                                              mock_metadata_manager, mock_executor):
        mock_executor.return_value = self.executor
        mock_metadata_manager.return_value = self.metadata_manager
        self.metadata_manager.get_project_context.return_value = "Test project context"
        mock_get_files.side_effect = requests.exceptions.ConnectionError(
            "API connection error")
        mock_run_with_loader.side_effect = lambda f, *args, **kwargs: f()

        execute_dravid_command(self.query, self.image_path,
                               self.debug, self.instruction_prompt)

        mock_print_error.assert_called_with(
            "An unexpected error occurred: API connection error")


if __name__ == '__main__':
    unittest.main()

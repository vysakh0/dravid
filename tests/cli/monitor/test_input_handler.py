import unittest
from unittest.mock import patch, MagicMock, ANY
from drd.cli.monitor.input_handler import InputHandler


class TestInputHandler(unittest.TestCase):
    def setUp(self):
        self.mock_monitor = MagicMock()
        self.input_handler = InputHandler(self.mock_monitor)

    @patch('drd.cli.monitor.input_handler.execute_dravid_command')
    @patch('drd.cli.monitor.input_handler.input', side_effect=['test input', 'exit', 'y'])
    def test_handle_input(self, mock_input, mock_execute_command):
        self.input_handler.handle_input()
        mock_execute_command.assert_called_once()
        self.mock_monitor.processing_input.set.assert_called()
        self.mock_monitor.processing_input.clear.assert_called()

        # Test exit
        self.input_handler.handle_input()
        self.mock_monitor.stop.assert_called_once()

    @patch('drd.cli.monitor.input_handler.print_info')
    def test_show_options(self, mock_print_info):
        self.input_handler._show_options()
        self.assertEqual(mock_print_info.call_count, 5)

    @patch('drd.cli.monitor.input_handler.execute_dravid_command')
    @patch('drd.cli.monitor.input_handler.InputHandler._handle_vision_input')
    def test_process_input(self, mock_handle_vision, mock_execute_command):
        # Test normal input
        self.input_handler._process_input('test command')
        mock_execute_command.assert_called_once()

        # Test vision input
        self.input_handler._process_input('p')
        mock_handle_vision.assert_called_once()

        # Test exit (cancelled)
        with patch('drd.cli.monitor.input_handler.input', return_value='n'):
            self.input_handler._process_input('exit')
            self.mock_monitor.stop.assert_not_called()

        # Test exit (confirmed)
        with patch('drd.cli.monitor.input_handler.input', return_value='y'):
            self.input_handler._process_input('exit')
            self.mock_monitor.stop.assert_called_once()

    @patch('drd.cli.monitor.input_handler.execute_dravid_command')
    @patch('drd.cli.monitor.input_handler.InputHandler._get_input_with_autocomplete', return_value='/path/to/image.jpg test instruction')
    @patch('os.path.exists', return_value=True)
    def test_handle_vision_input(self, mock_exists, mock_autocomplete, mock_execute_command):
        self.input_handler._handle_vision_input()
        mock_execute_command.assert_called_once()

    @patch('drd.cli.monitor.input_handler.execute_dravid_command')
    @patch('drd.cli.monitor.input_handler.InputParser')
    @patch('os.path.exists')
    def test_handle_general_input(self, mock_exists, mock_parser, mock_execute_command):
        # Test successful case
        mock_exists.return_value = True
        mock_parser.return_value.parse_input.return_value = (
            '/path/to/image.jpg', 'test instruction', [])
        self.input_handler._handle_general_input('test input')
        mock_execute_command.assert_called_once_with(
            'test instruction',
            '/path/to/image.jpg',
            debug=False,
            instruction_prompt=ANY,
            warn=False,
            reference_files=[]
        )

        # Reset mock
        mock_execute_command.reset_mock()

        # Test case where image path is not found
        mock_exists.return_value = False
        self.input_handler._handle_general_input('test input')
        mock_execute_command.assert_not_called()

        # Test case with no image path
        mock_parser.return_value.parse_input.return_value = (
            None, 'test instruction', [])
        self.input_handler._handle_general_input('test input')
        mock_execute_command.assert_called_once_with(
            'test instruction',
            None,
            debug=False,
            instruction_prompt=ANY,
            warn=False,
            reference_files=[]
        )

        # Test with no valid input
        mock_parser.return_value.parse_input.return_value = (None, '', [])
        self.input_handler._handle_general_input('invalid input')
        # execute_dravid_command should not be called again
        mock_execute_command.assert_called_once()

    @patch('drd.cli.monitor.input_handler.click.getchar', side_effect=['\t', '\r'])
    @patch('drd.cli.monitor.input_handler.InputHandler._autocomplete', return_value=['/path/to/file.txt'])
    @patch('drd.cli.monitor.input_handler.click.echo')
    def test_get_input_with_autocomplete(self, mock_echo, mock_autocomplete, mock_getchar):
        result = self.input_handler._get_input_with_autocomplete()
        self.assertEqual(result, '/path/to/file.txt')
        mock_autocomplete.assert_called_once()

    @patch('glob.glob', return_value=['/path/to/file.txt'])
    def test_autocomplete(self, mock_glob):
        result = self.input_handler._autocomplete('/path/to/f')
        self.assertEqual(result, ['/path/to/file.txt'])
        mock_glob.assert_called_once_with('/path/to/f*')

    @patch('glob.glob', return_value=['/path/to/dir/'])
    def test_autocomplete_directory(self, mock_glob):
        result = self.input_handler._autocomplete('/path/to/d')
        self.assertEqual(result, ['/path/to/dir/'])
        mock_glob.assert_called_once_with('/path/to/d*')

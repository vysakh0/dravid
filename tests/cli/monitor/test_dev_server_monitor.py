import unittest
from unittest.mock import patch, MagicMock
from drd.cli.monitor.server_monitor import DevServerMonitor, start_process


class TestDevServerMonitor(unittest.TestCase):

    def setUp(self):
        self.project_dir = '/fake/project/dir'
        self.error_handlers = {
            r"(?:Cannot find module|Module not found|ImportError|No module named)": MagicMock(),
            r"(?:SyntaxError|Expected|Unexpected token)": MagicMock(),
            r"(?:Error:|Failed to compile)": MagicMock(),
        }
        self.test_command = "npm run dev"

    @patch('drd.cli.monitor.server_monitor.start_process')
    @patch('drd.cli.monitor.server_monitor.InputHandler')
    @patch('drd.cli.monitor.server_monitor.OutputMonitor')
    @patch('os.path.exists', return_value=True)
    def test_start(self, mock_exists, mock_output_monitor, mock_input_handler, mock_start_process):
        monitor = DevServerMonitor(
            self.project_dir, self.error_handlers, self.test_command)
        monitor.start()

        mock_start_process.assert_called_once_with(
            self.test_command, self.project_dir)
        mock_output_monitor.return_value.start.assert_called_once()
        mock_input_handler.return_value.start.assert_called_once()

    @patch('drd.cli.monitor.server_monitor.start_process')
    def test_stop(self, mock_start_process):
        monitor = DevServerMonitor(
            self.project_dir, self.error_handlers, self.test_command)
        mock_process = MagicMock()
        monitor.process = mock_process

        monitor.stop()

        self.assertTrue(monitor.should_stop.is_set())
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()

    @patch('drd.cli.monitor.server_monitor.start_process')
    @patch('os.path.exists', return_value=True)
    def test_perform_restart(self, mock_exists, mock_start_process):
        monitor = DevServerMonitor(
            self.project_dir, self.error_handlers, self.test_command)
        mock_process = MagicMock()
        monitor.process = mock_process

        monitor.perform_restart()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        mock_start_process.assert_called_once_with(
            self.test_command, self.project_dir)

    @patch('subprocess.Popen')
    def test_start_process(self, mock_popen):
        start_process("test command", "/test/dir")
        mock_popen.assert_called_once_with(
            "test command",
            stdout=-1,
            stderr=-2,
            stdin=-1,
            text=True,
            bufsize=1,
            universal_newlines=True,
            shell=True,
            cwd="/test/dir"
        )

    @patch('drd.cli.monitor.server_monitor.start_process')
    @patch('os.path.exists', return_value=True)
    def test_invalid_command_restart_limit(self, mock_exists, mock_start_process):
        MAX_RETRIES = 3  # Assuming this is the value in your actual code
        invalid_command = 'invalid_command'
        monitor = DevServerMonitor(
            self.project_dir, self.error_handlers, invalid_command)

        # Simulate process failing to start
        mock_start_process.side_effect = Exception("Failed to start process")

        # Start the monitor
        monitor.start()

        # Simulate OutputMonitor behavior
        for _ in range(MAX_RETRIES):
            monitor.perform_restart()

        # Check that start_process was called MAX_RETRIES + 1 times (initial + retries)
        assert mock_start_process.call_count == MAX_RETRIES + 1

        # Check that the monitor has stopped
        assert monitor.should_stop.is_set()

import unittest
from unittest.mock import patch, MagicMock, call
import threading
import queue
import time

from drd.cli.monitor.server_monitor import DevServerMonitor, run_dev_server_with_monitoring


class TestDevServerMonitor(unittest.TestCase):

    def setUp(self):
        self.project_dir = '/fake/project/dir'
        self.error_handlers = {
            r"(?:Cannot find module|Module not found|ImportError|No module named)": MagicMock(),
            r"(?:SyntaxError|Expected|Unexpected token)": MagicMock(),
            r"(?:Error:|Failed to compile)": MagicMock(),
        }

    @patch('drd.cli.monitor.server_monitor.ProjectMetadataManager')
    @patch('drd.cli.monitor.server_monitor.subprocess.Popen')
    @patch('drd.cli.monitor.server_monitor.threading.Thread')
    @patch('drd.cli.monitor.server_monitor.select')
    def test_start_with_custom_command(self, mock_select, mock_thread, mock_popen, mock_metadata_manager):
        custom_command = "npm run dev"
        monitor = DevServerMonitor(
            self.project_dir, self.error_handlers, custom_command)

        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_popen.return_value = mock_process

        monitor.start()

        mock_popen.assert_called_once_with(
            custom_command,
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            stdin=unittest.mock.ANY,
            text=True,
            bufsize=1,
            universal_newlines=True,
            shell=True,
            cwd=self.project_dir
        )
        mock_thread.assert_called_once()

    @patch('drd.cli.monitor.server_monitor.ProjectMetadataManager')
    @patch('drd.cli.monitor.server_monitor.subprocess.Popen')
    @patch('drd.cli.monitor.server_monitor.threading.Thread')
    @patch('drd.cli.monitor.server_monitor.time.sleep')
    def test_restart(self, mock_sleep, mock_thread, mock_popen, mock_metadata_manager):
        monitor = DevServerMonitor(self.project_dir, self.error_handlers)

        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.return_value = "Test output"
        mock_popen.return_value = mock_process

        # Start the monitor
        monitor.start()

        # Check if a thread was created with _monitor_output as its target
        mock_thread.assert_called_once()
        thread_call_args = mock_thread.call_args[1]
        assert thread_call_args['target'] == monitor._monitor_output
        assert thread_call_args['daemon'] is True

        # Verify the initial Popen call
        assert len(mock_popen.mock_calls) > 0
        initial_call = mock_popen.mock_calls[0]
        # This is the method name, which should be empty for a constructor call
        assert initial_call[0] == ''
        assert initial_call[1][0] == mock_metadata_manager(
        ).get_dev_server_info().get()
        assert initial_call[2]['stdout'] == -1  # subprocess.PIPE
        assert initial_call[2]['stderr'] == -2  # subprocess.STDOUT
        assert initial_call[2]['stdin'] == -1   # subprocess.PIPE
        assert initial_call[2]['text'] is True
        assert initial_call[2]['bufsize'] == 1
        assert initial_call[2]['universal_newlines'] is True
        assert initial_call[2]['shell'] is True
        assert initial_call[2]['cwd'] == monitor.project_dir

        # Simulate a restart
        monitor.request_restart()
        monitor._perform_restart()

        # Check if Popen was called twice (initial start and restart)
        assert mock_popen.call_count == 2

        # Verify that sleep was called during restart
        mock_sleep.assert_called_with(2)

        # Verify that the monitor thread was started only once
        assert mock_thread.call_count == 1

        # Verify that the restart_requested flag is cleared after restart
        assert monitor.restart_requested.is_set() is False

        # Verify the calls made during restart
        restart_calls = [
            call().terminate(),
            call().wait(),
            call(
                mock_metadata_manager().get_dev_server_info().get(),
                stdout=-1, stderr=-2, stdin=-1,
                text=True, bufsize=1, universal_newlines=True, shell=True, cwd=monitor.project_dir
            )
        ]
        mock_popen.assert_has_calls(restart_calls, any_order=False)

    @patch('drd.cli.monitor.server_monitor.ProjectMetadataManager')
    @patch('drd.cli.monitor.server_monitor.subprocess.Popen')
    @patch('drd.cli.monitor.server_monitor.threading.Thread')
    @patch('drd.cli.monitor.server_monitor.select.select')
    def test_stop(self, mock_select, mock_thread, mock_popen, mock_metadata_manager):
        monitor = DevServerMonitor(self.project_dir, self.error_handlers)

        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        monitor.start()
        monitor.stop()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()


@patch('drd.cli.monitor.server_monitor.DevServerMonitor')
@patch('drd.cli.monitor.server_monitor.print_info')
@patch('drd.cli.monitor.server_monitor.time.sleep', side_effect=[None, KeyboardInterrupt])
def test_run_dev_server_with_monitoring(mock_sleep, mock_print_info, mock_monitor):
    mock_monitor_instance = MagicMock()
    mock_monitor.return_value = mock_monitor_instance
    mock_monitor_instance.process.poll.return_value = None

    run_dev_server_with_monitoring()

    mock_monitor.assert_called_once()
    mock_monitor_instance.start.assert_called_once()
    mock_monitor_instance.stop.assert_called_once()
    mock_print_info.assert_any_call(
        "Server monitor started. Press Ctrl+C to stop.")

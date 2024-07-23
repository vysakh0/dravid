import unittest
from unittest.mock import patch, MagicMock, call
import threading
import time
from drd.cli.monitor.output_monitor import OutputMonitor


class TestOutputMonitor(unittest.TestCase):
    def setUp(self):
        self.mock_monitor = MagicMock()
        self.mock_monitor.MAX_RETRIES = 3
        self.mock_monitor.retry_count = 0
        self.output_monitor = OutputMonitor(self.mock_monitor)

    @patch('select.select')
    @patch('time.time')
    @patch('drd.cli.monitor.output_monitor.print_info')
    @patch('drd.cli.monitor.output_monitor.print_error')
    def test_monitor_output_process_ended(self, mock_print_error, mock_print_info, mock_time, mock_select):
        self.mock_monitor.should_stop.is_set.side_effect = [False, False, True]
        self.mock_monitor.process.poll.return_value = 1
        self.mock_monitor.processing_input.is_set.return_value = False
        self.mock_monitor.restart_requested.is_set.return_value = False

        self.output_monitor._monitor_output()

        expected_calls = [
            call("Server process ended unexpectedly."),
            call("Restarting... (Attempt 1/3)")
        ]
        mock_print_info.assert_has_calls(expected_calls, any_order=False)
        self.mock_monitor.perform_restart.assert_called_once()
        self.assertEqual(self.mock_monitor.retry_count, 1)

    @patch('select.select')
    @patch('time.time')
    def test_monitor_output_read_line(self, mock_time, mock_select):
        self.mock_monitor.should_stop.is_set.side_effect = [False, True]
        self.mock_monitor.process.poll.return_value = None
        self.mock_monitor.process.stdout.readline.return_value = "Test output\n"
        self.mock_monitor.processing_input.is_set.return_value = False
        mock_select.return_value = ([self.mock_monitor.process.stdout], [], [])

        with patch.object(self.output_monitor, '_check_for_errors') as mock_check_errors:
            self.output_monitor._monitor_output()

            mock_check_errors.assert_called_once_with(
                "Test output\n", ["Test output\n"])

        self.assertEqual(self.mock_monitor.retry_count, 0)

    def test_check_for_errors(self):
        self.mock_monitor.error_handlers = {
            r"Error:": MagicMock()
        }
        error_buffer = ["Warning: This is a warning\n",
                        "Error: This is an error\n"]

        self.output_monitor._check_for_errors(
            "Error: This is an error\n", error_buffer)

        self.mock_monitor.error_handlers[r"Error:"].assert_called_once_with(
            "Warning: This is a warning\nError: This is an error\n",
            self.mock_monitor
        )
        self.assertEqual(error_buffer, [])

    @patch('time.time')
    def test_check_idle_state(self, mock_time):
        mock_time.return_value = 10
        self.output_monitor.last_output_time = 4
        self.mock_monitor.processing_input.is_set.return_value = False

        self.output_monitor._check_idle_state()

        self.assertTrue(self.output_monitor.idle_detected.is_set())

    @patch('time.time')
    def test_check_idle_state_not_idle(self, mock_time):
        mock_time.return_value = 10
        self.output_monitor.last_output_time = 7
        self.mock_monitor.processing_input.is_set.return_value = False

        self.output_monitor._check_idle_state()

        self.assertFalse(self.output_monitor.idle_detected.is_set())


if __name__ == '__main__':
    unittest.main()

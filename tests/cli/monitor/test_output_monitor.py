import unittest
import sys
from unittest.mock import patch, MagicMock, call
from io import StringIO
from drd.cli.monitor.output_monitor import OutputMonitor


class TestOutputMonitor(unittest.TestCase):

    def setUp(self):
        self.mock_monitor = MagicMock()
        self.output_monitor = OutputMonitor(self.mock_monitor)

    @patch('select.select')
    @patch('time.time')
    @patch('drd.cli.monitor.output_monitor.print_info')
    def test_idle_state(self, mock_print_info, mock_time, mock_select):
        # Setup
        self.mock_monitor.should_stop.is_set.side_effect = [
            False] * 10 + [True]
        self.mock_monitor.process.poll.return_value = None
        self.mock_monitor.processing_input.is_set.return_value = False
        self.mock_monitor.process.stdout = MagicMock()
        self.mock_monitor.process.stdout.readline.return_value = ""
        mock_select.return_value = ([self.mock_monitor.process.stdout], [], [])

        # Create a function to generate increasing time values
        start_time = 1000000  # Start with a large value to avoid negative times

        def time_sequence():
            nonlocal start_time
            start_time += 1  # Increment by 1 second each time
            return start_time

        mock_time.side_effect = time_sequence

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # Run
        self.output_monitor._monitor_output()

        # Restore stdout
        sys.stdout = sys.__stdout__

        # Print captured output
        print("Captured output:")
        print(captured_output.getvalue())

        # Assert
        expected_calls = [
            call("\nNo more tasks to auto-process. What can I do next?"),
            call("\nAvailable actions:"),
            call("1. Ask a question or give an instruction"),
            call("2. Process an image (type 'vision')"),
            call("3. Exit monitoring mode (type 'exit')"),
            call("\nType your choice or command:")
        ]
        mock_print_info.assert_has_calls(expected_calls, any_order=True)

    @patch('select.select')
    @patch('time.time')
    @patch('drd.cli.monitor.output_monitor.print_info')
    def test_idle_state(self, mock_print_info, mock_time, mock_select):
        # Setup
        self.mock_monitor.should_stop.is_set.side_effect = [
            False] * 10 + [True]
        self.mock_monitor.process.poll.return_value = None
        self.mock_monitor.processing_input.is_set.return_value = False
        self.mock_monitor.process.stdout = MagicMock()
        self.mock_monitor.process.stdout.readline.return_value = ""
        mock_select.return_value = ([self.mock_monitor.process.stdout], [], [])
        mock_time.side_effect = [0] + [6] * 10  # Simulate time passing

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # Run
        self.output_monitor._monitor_output()

        # Restore stdout
        sys.stdout = sys.__stdout__

        # Print captured output
        print("Captured output:")
        print(captured_output.getvalue())

        # Assert
        expected_calls = [
            call("\nNo more tasks to auto-process. What can I do next?"),
            call("\nAvailable actions:"),
            call("1. Ask a question or give an instruction"),
            call("2. Process an image (type 'vision')"),
            call("3. Exit monitoring mode (type 'exit')"),
            call("\nType your choice or command:")
        ]
        mock_print_info.assert_has_calls(expected_calls, any_order=True)

    def test_check_for_errors(self):
        # Setup
        error_buffer = ["Error: Test error\n"]
        self.mock_monitor.error_handlers = {
            r"Error:": MagicMock()
        }

        # Run
        self.output_monitor._check_for_errors(
            "Error: Test error\n", error_buffer)

        # Assert
        self.mock_monitor.error_handlers[r"Error:"].assert_called_once_with(
            "Error: Test error\n", self.mock_monitor)


if __name__ == '__main__':
    unittest.main()
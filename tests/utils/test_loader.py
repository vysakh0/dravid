import unittest
from unittest.mock import patch, MagicMock
import threading
import time
from io import StringIO

# Import the Loader class and run_with_loader function
from drd.utils.loader import Loader, run_with_loader


class TestLoader(unittest.TestCase):

    @patch('click.echo')
    def test_loader_start_stop(self, mock_echo):
        loader = Loader("Testing")
        loader.start()
        time.sleep(0.3)  # Allow some time for the animation to run
        loader.stop()

        # Check if echo was called with the correct message
        mock_echo.assert_any_call('\rTesting |', nl=False)

    @patch('click.echo')
    def test_loader_animation(self, mock_echo):
        loader = Loader("Testing")
        loader.start()
        time.sleep(0.5)  # Allow time for multiple animation frames
        loader.stop()

        # Check if different animation frames were displayed
        mock_echo.assert_any_call('\rTesting |', nl=False)
        mock_echo.assert_any_call('\rTesting /', nl=False)

    @patch('click.echo')
    def test_loader_custom_message(self, mock_echo):
        loader = Loader("Custom message")
        loader.start()
        time.sleep(0.2)
        loader.stop()

        # Check if the custom message was used
        mock_echo.assert_any_call('\rCustom message |', nl=False)

    @patch('click.echo')
    def test_loader_stop_clears_line(self, mock_echo):
        loader = Loader("Testing")
        loader.start()
        time.sleep(0.2)
        loader.stop()

        # Check if the line was cleared on stop
        mock_echo.assert_any_call('\r' + ' ' * (len("Testing") + 10), nl=False)
        mock_echo.assert_any_call('\r', nl=False)

    @patch('click.echo')
    def test_run_with_loader(self, mock_echo):
        def mock_function():
            time.sleep(0.5)
            return "Done"

        result = run_with_loader(mock_function, "Processing")

        # Check if the loader was started and stopped
        mock_echo.assert_any_call('\rProcessing |', nl=False)
        mock_echo.assert_any_call(
            '\r' + ' ' * (len("Processing") + 10), nl=False)

        # Check if the function result was returned
        self.assertEqual(result, "Done")

    @patch('click.echo')
    def test_run_with_loader_exception(self, mock_echo):
        def mock_function_with_exception():
            time.sleep(0.5)
            raise ValueError("Test exception")

        with self.assertRaises(ValueError):
            run_with_loader(mock_function_with_exception, "Processing")

        # Check if the loader was started and stopped even with an exception
        mock_echo.assert_any_call('\rProcessing |', nl=False)
        mock_echo.assert_any_call(
            '\r' + ' ' * (len("Processing") + 10), nl=False)

from src.drd.cli.monitor import DevServerMonitor, run_dev_server_with_monitoring, handle_module_not_found, handle_syntax_error, handle_port_in_use
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from queue import Queue

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..')))


class TestMonitor(unittest.TestCase):

    def setUp(self):
        self.project_dir = '/fake/project/dir'
        self.error_handlers = {
            r"(?:Cannot find module|Module not found|ImportError|No module named)": handle_module_not_found,
            r"SyntaxError": handle_syntax_error,
            r"(?:EADDRINUSE|address already in use)": handle_port_in_use,
        }

    @patch('src.drd.cli.monitor.ProjectMetadataManager')
    def test_dev_server_monitor_initialization(self, mock_metadata_manager):
        monitor = DevServerMonitor(self.project_dir, self.error_handlers)
        self.assertEqual(monitor.project_dir, self.project_dir)
        self.assertEqual(monitor.error_handlers, self.error_handlers)
        self.assertIsInstance(monitor.output_queue, Queue)

    # @patch('src.drd.cli.monitor.ProjectMetadataManager')
    # @patch('src.drd.cli.monitor.subprocess.Popen')
    # def test_dev_server_monitor_start(self, mock_popen, mock_metadata_manager):
    #     mock_metadata_manager.return_value.get_dev_server_info.return_value = {
    #         'start_command': 'npm start'}
    #     monitor = DevServerMonitor(self.project_dir, self.error_handlers)
    #     monitor.start()
    #     mock_popen.assert_called_once()

    @patch('src.drd.cli.monitor.ProjectMetadataManager')
    @patch('src.drd.cli.monitor.subprocess.Popen')
    def test_dev_server_monitor_stop(self, mock_popen, mock_metadata_manager):
        monitor = DevServerMonitor(self.project_dir, self.error_handlers)
        monitor.process = MagicMock()
        monitor.stop()
        monitor.process.terminate.assert_called_once()
        monitor.process.wait.assert_called_once()

    # @patch('src.drd.cli.monitor.call_dravid_api')
    # def test_handle_module_not_found(self, mock_call_dravid_api):
    #     monitor = MagicMock()
    #     line = "Error: Cannot find module 'missing-module'"
    #     handle_module_not_found(line, monitor)
    #     mock_call_dravid_api.assert_called_once()

    # @patch('src.drd.cli.monitor.call_dravid_api')
    # def test_handle_port_in_use(self, mock_call_dravid_api):
    #     monitor = MagicMock()
    #     line = "Error: EADDRINUSE: address already in use :::3000"
    #     handle_port_in_use(line, monitor)
    #     mock_call_dravid_api.assert_called_once()

    # @patch('src.drd.cli.monitor.DevServerMonitor')
    # def test_run_dev_server_with_monitoring(self, mock_dev_server_monitor):
    #     with patch('builtins.print'):  # Suppress print statements
    #         run_dev_server_with_monitoring()
    #     mock_dev_server_monitor.assert_called_once()
    #     mock_dev_server_monitor.return_value.start.assert_called_once()
    #     mock_dev_server_monitor.return_value.stop.assert_called_once()


if __name__ == '__main__':
    unittest.main()

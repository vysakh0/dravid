import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import json
import subprocess
from io import StringIO

# Update this import to match your actual module structure
from drd.utils.step_executor import Executor


class TestExecutor(unittest.TestCase):

    def setUp(self):
        self.executor = Executor()

    def test_is_safe_path(self):
        self.assertTrue(self.executor.is_safe_path('test.txt'))
        self.assertFalse(self.executor.is_safe_path('/etc/passwd'))

    def test_is_safe_rm_command(self):
        # Assuming 'rm test.txt' is not considered safe without additional checks
        self.assertFalse(self.executor.is_safe_rm_command('rm test.txt'))
        # Test with a file that exists in the current directory
        with patch('os.path.isfile', return_value=True):
            self.assertTrue(self.executor.is_safe_rm_command(
                'rm existing_file.txt'))
        self.assertFalse(self.executor.is_safe_rm_command('rm -rf /'))
        self.assertFalse(self.executor.is_safe_rm_command('rm -f test.txt'))

    def test_is_safe_command(self):
        self.assertTrue(self.executor.is_safe_command('ls'))
        self.assertFalse(self.executor.is_safe_command('sudo rm -rf /'))

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_perform_file_operation_create(self, mock_file, mock_exists):
        mock_exists.return_value = False
        result = self.executor.perform_file_operation(
            'CREATE', 'test.txt', 'content')
        self.assertTrue(result)
        mock_file.assert_called_with(os.path.join(
            self.executor.current_dir, 'test.txt'), 'w')
        mock_file().write.assert_called_with('content')

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_perform_file_operation_update(self, mock_file, mock_exists):
        mock_exists.return_value = True
        result = self.executor.perform_file_operation(
            'UPDATE', 'test.txt', 'new content')
        self.assertTrue(result)
        mock_file.assert_called_with(os.path.join(
            self.executor.current_dir, 'test.txt'), 'w')
        mock_file().write.assert_called_with('new content')

    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('os.remove')
    def test_perform_file_operation_delete(self, mock_remove, mock_isfile, mock_exists):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        result = self.executor.perform_file_operation('DELETE', 'test.txt')
        self.assertTrue(result)
        mock_remove.assert_called_with(os.path.join(
            self.executor.current_dir, 'test.txt'))

    def test_parse_json(self):
        valid_json = '{"key": "value"}'
        invalid_json = '{key: value}'
        self.assertEqual(self.executor.parse_json(
            valid_json), {"key": "value"})
        self.assertIsNone(self.executor.parse_json(invalid_json))

    def test_merge_json(self):
        existing_content = '{"key1": "value1"}'
        new_content = '{"key2": "value2"}'
        expected_result = json.dumps(
            {"key1": "value1", "key2": "value2"}, indent=2)
        self.assertEqual(self.executor.merge_json(
            existing_content, new_content), expected_result)

    @patch('drd.utils.step_executor.get_ignore_patterns')
    @patch('drd.utils.step_executor.get_folder_structure')
    def test_get_folder_structure(self, mock_get_folder_structure, mock_get_ignore_patterns):
        mock_get_ignore_patterns.return_value = ([], None)
        mock_get_folder_structure.return_value = {
            'folder': {'file.txt': 'file'}}
        result = self.executor.get_folder_structure()
        self.assertEqual(result, {'folder': {'file.txt': 'file'}})

    @patch('subprocess.Popen')
    def test_execute_shell_command(self, mock_popen):
        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, 0]
        mock_process.stdout.readline.return_value = 'output line'
        mock_process.communicate.return_value = ('', '')
        mock_popen.return_value = mock_process

        result = self.executor.execute_shell_command('ls')
        self.assertEqual(result, 'output line')

    @patch('subprocess.run')
    def test_handle_source_command(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=['source', 'test.sh'],
            returncode=0,
            stdout='KEY=value\n',
            stderr=''
        )
        with patch('os.path.isfile', return_value=True):
            result = self.executor._handle_source_command('source test.sh')
        self.assertEqual(result, "Source command executed successfully")
        self.assertEqual(self.executor.env['KEY'], 'value')

    def test_update_env_from_command(self):
        # Test simple assignment
        self.executor._update_env_from_command('TEST_VAR=test_value')
        self.assertEqual(self.executor.env['TEST_VAR'], 'test_value')

        # Test export command
        self.executor._update_env_from_command(
            'export EXPORT_VAR=export_value')
        self.assertEqual(self.executor.env['EXPORT_VAR'], 'export_value')

        # Test set command
        self.executor._update_env_from_command('set SET_VAR=set_value')
        self.assertEqual(self.executor.env['SET_VAR'], 'set_value')

        # Test with quotes
        self.executor._update_env_from_command('QUOTE_VAR="quoted value"')
        self.assertEqual(self.executor.env['QUOTE_VAR'], 'quoted value')

        # Test export with quotes
        self.executor._update_env_from_command(
            'export EXPORT_QUOTE="exported quoted value"')
        self.assertEqual(
            self.executor.env['EXPORT_QUOTE'], 'exported quoted value')

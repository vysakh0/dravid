from src.drd.metadata.initializer import initialize_project_metadata
import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..')))


class TestMetadataInitializer(unittest.TestCase):

    def setUp(self):
        self.project_dir = '/fake/project/dir'

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_initialize_project_metadata_new_project(self, mock_json_dump, mock_file, mock_exists):
        mock_exists.return_value = False
        initialize_project_metadata(self.project_dir)

        mock_file.assert_called_once_with(
            os.path.join(self.project_dir, 'drd.json'), 'w')
        mock_json_dump.assert_called_once()

        # Check the structure of the created metadata
        created_metadata = mock_json_dump.call_args[0][0]
        self.assertIn('project_name', created_metadata)
        self.assertIn('last_updated', created_metadata)
        self.assertIn('files', created_metadata)
        self.assertIn('dev_server', created_metadata)
        self.assertEqual(
            created_metadata['project_name'], os.path.basename(self.project_dir))

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"project_name": "Existing Project", "files": []}')
    @patch('json.dump')
    def test_initialize_project_metadata_existing_project(self, mock_json_dump, mock_file, mock_exists):
        mock_exists.return_value = True
        initialize_project_metadata(self.project_dir)

        mock_file.assert_called_with(
            os.path.join(self.project_dir, 'drd.json'), 'r')
        mock_json_dump.assert_called_once()

        # Check that existing metadata was updated, not overwritten
        updated_metadata = mock_json_dump.call_args[0][0]
        self.assertEqual(updated_metadata['project_name'], "Existing Project")
        self.assertIn('last_updated', updated_metadata)
        self.assertIn('files', updated_metadata)
        self.assertIn('dev_server', updated_metadata)

    @patch('os.path.exists')
    @patch('builtins.open', side_effect=[IOError, mock_open(read_data='{}').return_value])
    @patch('json.dump')
    def test_initialize_project_metadata_file_creation_error(self, mock_json_dump, mock_file, mock_exists):
        mock_exists.return_value = False
        with self.assertRaises(IOError):
            initialize_project_metadata(self.project_dir)

        mock_file.assert_called_with(
            os.path.join(self.project_dir, 'drd.json'), 'w')
        mock_json_dump.assert_not_called()


if __name__ == '__main__':
    unittest.main()

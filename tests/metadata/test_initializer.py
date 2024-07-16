import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
from datetime import datetime
import xml.etree.ElementTree as ET

from drd.metadata.initializer import initialize_project_metadata, initialize_project_metadata_sync


class TestProjectMetadataInitializer(unittest.TestCase):

    def setUp(self):
        self.current_dir = '/fake/project/dir'
        self.folder_structure = {
            'src': {
                'main.py': 'file',
                'utils.py': 'file'
            },
            'tests': {
                'test_main.py': 'file'
            },
            'README.md': 'file'
        }

    @patch('drd.metadata.initializer.get_ignore_patterns')
    @patch('drd.metadata.initializer.get_folder_structure')
    @patch('drd.metadata.initializer.call_dravid_api_with_pagination')
    @patch('drd.metadata.initializer.extract_and_parse_xml')
    @patch('drd.metadata.initializer.process_files')
    @patch('drd.metadata.initializer.ProjectMetadataManager')
    @patch('drd.metadata.initializer.os.walk')
    @patch('drd.metadata.initializer.open', new_callable=mock_open, read_data="file content")
    @patch('drd.metadata.initializer.print_info')
    @patch('drd.metadata.initializer.print_success')
    @patch('drd.metadata.initializer.print_warning')
    @patch('drd.metadata.initializer.datetime')
    async def test_initialize_project_metadata(self, mock_datetime, mock_print_warning, mock_print_success,
                                               mock_print_info, mock_file, mock_walk, mock_metadata_manager,
                                               mock_process_files, mock_extract_xml, mock_call_api,
                                               mock_get_folder_structure, mock_get_ignore_patterns):
        # Set up mocks
        mock_get_ignore_patterns.return_value = (
            [], "No ignore patterns found")
        mock_get_folder_structure.return_value = self.folder_structure
        mock_call_api.return_value = "<response><project_info><project_name>Test Project</project_name><description>A test project</description><dev_server><start_command>npm start</start_command><framework>React</framework><language>JavaScript</language></dev_server></project_info></response>"

        mock_root = ET.fromstring(mock_call_api.return_value)
        mock_extract_xml.return_value = mock_root

        mock_walk.return_value = [
            ('/fake/project/dir', ['src', 'tests'], ['README.md']),
            ('/fake/project/dir/src', [], ['main.py', 'utils.py']),
            ('/fake/project/dir/tests', [], ['test_main.py'])
        ]

        mock_process_files.return_value = [
            ('README.md', 'markdown', 'Project README', []),
            ('src/main.py', 'python', 'Main Python file', ['main_function']),
            ('src/utils.py', 'python', 'Utility functions', ['util_function']),
            ('tests/test_main.py', 'python', 'Tests for main.py', [])
        ]

        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.fromtimestamp.return_value = datetime(
            2023, 1, 1, 12, 0, 0)

        # Call the function
        await initialize_project_metadata(self.current_dir)

        # Assertions
        mock_get_ignore_patterns.assert_called_once_with(self.current_dir)
        mock_get_folder_structure.assert_called_once_with(self.current_dir, [])
        mock_call_api.assert_called_once()
        mock_extract_xml.assert_called_once_with(mock_call_api.return_value)
        mock_process_files.assert_called_once()

        # Check if metadata was correctly created and saved
        mock_metadata_manager.assert_called_once_with(self.current_dir)
        mock_metadata_manager.return_value.save_metadata.assert_called_once()

        # Check the content of the metadata
        saved_metadata = mock_metadata_manager.return_value.metadata
        self.assertEqual(saved_metadata['project_name'], 'Test Project')
        self.assertEqual(saved_metadata['description'], 'A test project')
        self.assertEqual(
            saved_metadata['dev_server']['start_command'], 'npm start')
        self.assertEqual(saved_metadata['dev_server']['framework'], 'React')
        self.assertEqual(
            saved_metadata['dev_server']['language'], 'JavaScript')
        # README.md, main.py, utils.py, test_main.py
        self.assertEqual(len(saved_metadata['files']), 4)

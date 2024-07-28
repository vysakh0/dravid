import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys
import json
from datetime import datetime

# Assuming the project structure, adjust the import path as necessary
from src.drd.metadata.project_metadata import ProjectMetadataManager


class TestProjectMetadataManager(unittest.TestCase):

    def setUp(self):
        self.project_dir = '/fake/project/dir'
        self.manager = ProjectMetadataManager(self.project_dir)

    @patch('os.walk')
    def test_get_ignore_patterns(self, mock_walk):
        mock_walk.return_value = [
            ('/fake/project/dir', [], ['.gitignore']),
            ('/fake/project/dir/subfolder', [], ['.gitignore'])
        ]
        mock_open_calls = [
            mock_open(read_data="*.log\nnode_modules/\n").return_value,
            mock_open(read_data="*.tmp\n").return_value
        ]
        with patch('builtins.open', side_effect=mock_open_calls):
            patterns = self.manager.get_ignore_patterns()

        self.assertIn('*.log', patterns)
        self.assertIn('node_modules/', patterns)
        self.assertIn('subfolder/*.tmp', patterns)

    def test_should_ignore(self):
        self.manager.ignore_patterns = [
            '*.log', 'node_modules/', 'subfolder/*.tmp']
        self.assertTrue(self.manager.should_ignore(
            '/fake/project/dir/test.log'))
        self.assertTrue(self.manager.should_ignore(
            '/fake/project/dir/node_modules/package.json'))
        self.assertTrue(self.manager.should_ignore(
            '/fake/project/dir/node_modules/subfolder/file.js'))
        self.assertTrue(self.manager.should_ignore(
            '/fake/project/dir/subfolder/test.tmp'))
        self.assertFalse(self.manager.should_ignore(
            '/fake/project/dir/src/main.py'))
        self.assertFalse(self.manager.should_ignore(
            '/fake/project/dir/package.json'))

    @patch('os.walk')
    def test_get_directory_structure(self, mock_walk):
        mock_walk.return_value = [
            ('/fake/project/dir', ['src'], ['README.md']),
            ('/fake/project/dir/src', [], ['main.py', 'utils.py'])
        ]
        structure = self.manager.get_directory_structure(self.project_dir)
        expected_structure = {
            'files': ['README.md'],
            'directories': ['src'],
            'src': {
                'files': ['main.py', 'utils.py']
            }
        }
        self.assertEqual(structure, expected_structure)

    def test_is_binary_file(self):
        self.assertTrue(self.manager.is_binary_file('test.exe'))
        self.assertTrue(self.manager.is_binary_file('image.png'))
        self.assertFalse(self.manager.is_binary_file('script.py'))
        self.assertFalse(self.manager.is_binary_file('config.json'))

    @patch('src.drd.metadata.project_metadata.call_dravid_api_with_pagination')
    @patch('builtins.open', new_callable=mock_open, read_data='print("Hello, World!")')
    async def test_analyze_file(self, mock_file, mock_api_call):
        mock_api_call.return_value = '''
        <response>
          <metadata>
            <type>python</type>
            <summary>A simple Python script</summary>
            <exports>None</exports>
            <imports>None</imports>
          </metadata>
        </response>
        '''
        file_info = await self.manager.analyze_file('/fake/project/dir/script.py')
        self.assertEqual(file_info['path'], 'script.py')
        self.assertEqual(file_info['type'], 'python')
        self.assertEqual(file_info['summary'], 'A simple Python script')

    @patch('src.drd.metadata.project_metadata.ProjectMetadataManager.analyze_file')
    @patch('os.walk')
    async def test_build_metadata(self, mock_walk, mock_analyze_file):
        mock_walk.return_value = [
            ('/fake/project/dir', [], ['main.py', 'README.md'])
        ]
        mock_analyze_file.side_effect = [
            {
                'path': 'main.py',
                'type': 'python',
                'summary': 'Main Python script',
                'exports': ['main_function'],
                'imports': ['os']
            },
            None  # Simulating skipping README.md
        ]
        loader = MagicMock()
        metadata = await self.manager.build_metadata(loader)

        self.assertEqual(metadata['environment']['primary_language'], 'python')
        self.assertEqual(len(metadata['key_files']), 1)
        self.assertEqual(metadata['key_files'][0]['path'], 'main.py')

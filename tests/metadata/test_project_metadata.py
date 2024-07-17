from src.drd.metadata.project_metadata import ProjectMetadataManager
import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..')))


class TestProjectMetadataManager(unittest.TestCase):

    def setUp(self):
        self.project_dir = '/fake/project/dir'
        self.manager = ProjectMetadataManager(self.project_dir)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"project_name": "Test Project"}')
    def test_load_metadata(self, mock_file, mock_exists):
        mock_exists.return_value = True
        metadata = self.manager.load_metadata()
        self.assertEqual(metadata["project_name"], "Test Project")
        mock_file.assert_called_once_with(
            os.path.join(self.project_dir, 'drd.json'), 'r')

    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_metadata(self, mock_file, mock_json_dump):
        self.manager.save_metadata()
        mock_file.assert_called_once_with(
            os.path.join(self.project_dir, 'drd.json'), 'w')
        mock_json_dump.assert_called_once()

    @patch.object(ProjectMetadataManager, 'save_metadata')
    def test_update_file_metadata(self, mock_save):
        self.manager.update_file_metadata(
            "test.py", "python", "print('Hello')", "A test Python file")
        mock_save.assert_called_once()
        file_entry = next(
            (f for f in self.manager.metadata['files'] if f['filename'] == "test.py"), None)
        self.assertIsNotNone(file_entry)
        self.assertEqual(file_entry['type'], "python")
        self.assertEqual(file_entry['content_preview'], "print('Hello')")
        self.assertEqual(file_entry['description'], "A test Python file")

    def test_get_project_context(self):
        self.manager.metadata = {
            "project_name": "Test Project",
            "last_updated": "",
            "files": [
                {"filename": "main.py", "type": "python",
                    "description": "Main file"},
                {"filename": "utils.py", "type": "python",
                    "description": "Utility functions"}
            ],
            "dev_server": {
                "start_command": "",
                "framework": "",
                "language": ""
            }
        }
        context = self.manager.get_project_context()
        self.assertIn("Test Project", context)
        self.assertIn("main.py", context)
        self.assertIn("utils.py", context)

    @patch.object(ProjectMetadataManager, 'save_metadata')
    def test_update_dev_server_info(self, mock_save):
        self.manager.update_dev_server_info("npm start", "react", "javascript")
        mock_save.assert_called_once()
        self.assertEqual(
            self.manager.metadata['dev_server']['start_command'], "npm start")
        self.assertEqual(
            self.manager.metadata['dev_server']['framework'], "react")
        self.assertEqual(
            self.manager.metadata['dev_server']['language'], "javascript")

    def test_get_dev_server_info(self):
        self.manager.metadata['dev_server'] = {
            "start_command": "npm start",
            "framework": "react",
            "language": "javascript"
        }
        info = self.manager.get_dev_server_info()
        self.assertEqual(info, self.manager.metadata['dev_server'])

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(ProjectMetadataManager, 'save_metadata')
    def test_update_metadata_from_file(self, mock_save, mock_file, mock_exists):
        mock_exists.return_value = True

        # Initial metadata
        initial_metadata = {
            "project_name": "old_project",
            "last_updated": "",
            "files": [],
            "dev_server": {
                "start_command": "",
                "framework": "",
                "language": ""
            }
        }
        self.manager.metadata = initial_metadata

        # New metadata to be updated
        new_metadata = {
            "project_name": "pyserv",
            "last_updated": "2023-07-18T10:00:00",
            "files": [
                {
                    "filename": "app.py",
                    "content": "from flask import Flask\n\napp = Flask(__name__)",
                    "description": "Main application file",
                    "exports": "app"
                },
                {
                    "filename": "requirements.txt",
                    "content": "Flask==2.3.2\nuvicorn==0.22.0",
                    "description": "Project dependencies"
                }
            ],
            "dev_server": {
                "start_command": "uvicorn app:app --reload",
                "framework": "flask",
                "language": "python"
            }
        }

        # Mock the file read operation to return the new metadata
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(
            new_metadata)

        # Call the method to update metadata
        result = self.manager.update_metadata_from_file()

        # Assert that the update was successful
        self.assertTrue(result)

        # Assert that the metadata has been updated correctly
        self.assertEqual(self.manager.metadata['project_name'], "pyserv")
        self.assertEqual(len(self.manager.metadata['files']), 2)
        self.assertEqual(
            self.manager.metadata['dev_server']['start_command'], "uvicorn app:app --reload")
        self.assertEqual(
            self.manager.metadata['dev_server']['framework'], "flask")
        self.assertEqual(
            self.manager.metadata['dev_server']['language'], "python")

        # Check file metadata
        app_py = next(
            f for f in self.manager.metadata['files'] if f['filename'] == 'app.py')
        self.assertEqual(app_py['description'], "Main application file")
        self.assertEqual(app_py['exports'], "app")
        self.assertTrue(app_py['content_preview'].startswith(
            "from flask import Flask"))

        requirements_txt = next(
            f for f in self.manager.metadata['files'] if f['filename'] == 'requirements.txt')
        self.assertEqual(
            requirements_txt['description'], "Project dependencies")
        self.assertTrue(
            requirements_txt['content_preview'].startswith("Flask==2.3.2"))

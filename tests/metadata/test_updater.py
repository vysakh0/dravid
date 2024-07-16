import unittest
from unittest.mock import patch, MagicMock, mock_open
import xml.etree.ElementTree as ET

from drd.metadata.updater import update_metadata_with_dravid


class TestMetadataUpdater(unittest.TestCase):

    def setUp(self):
        self.current_dir = '/fake/project/dir'
        self.meta_description = "Update project metadata"
        self.project_context = "This is a sample project context"
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

    @patch('drd.metadata.updater.ProjectMetadataManager')
    @patch('drd.metadata.updater.get_ignore_patterns')
    @patch('drd.metadata.updater.get_folder_structure')
    @patch('drd.metadata.updater.call_dravid_api_with_pagination')
    @patch('drd.metadata.updater.extract_and_parse_xml')
    @patch('drd.metadata.updater.find_file_with_dravid')
    @patch('drd.metadata.updater.generate_file_description')
    @patch('drd.metadata.updater.print_info')
    @patch('drd.metadata.updater.print_success')
    @patch('drd.metadata.updater.print_warning')
    @patch('drd.metadata.updater.print_error')
    @patch('builtins.open', new_callable=mock_open, read_data="file content")
    def test_update_metadata_with_dravid(self, mock_file, mock_print_error, mock_print_warning,
                                         mock_print_success, mock_print_info, mock_generate_description,
                                         mock_find_file, mock_extract_xml, mock_call_api,
                                         mock_get_folder_structure, mock_get_ignore_patterns,
                                         mock_metadata_manager):
        # Set up mocks
        mock_metadata_manager.return_value.get_project_context.return_value = self.project_context
        mock_get_ignore_patterns.return_value = (
            [], "No ignore patterns found")
        mock_get_folder_structure.return_value = self.folder_structure

        mock_call_api.return_value = "<response><files><file><path>src/main.py</path><action>update</action></file><file><path>README.md</path><action>remove</action></file></files></response>"
        mock_root = ET.fromstring(mock_call_api.return_value)
        mock_extract_xml.return_value = mock_root

        mock_find_file.return_value = '/fake/project/dir/src/main.py'
        mock_generate_description.return_value = (
            'python', 'Main Python file', ['main_function'])

        # Call the function
        update_metadata_with_dravid(self.meta_description, self.current_dir)

        # Assertions
        mock_metadata_manager.assert_called_once_with(self.current_dir)
        mock_get_ignore_patterns.assert_called_once_with(self.current_dir)
        mock_get_folder_structure.assert_called_once_with(self.current_dir, [])
        mock_call_api.assert_called_once()
        mock_extract_xml.assert_called_once_with(mock_call_api.return_value)

        # Check if metadata was correctly updated and removed
        mock_metadata_manager.return_value.update_file_metadata.assert_called_once_with(
            '/fake/project/dir/src/main.py', 'python', 'file content', 'Main Python file', [
                'main_function']
        )
        mock_metadata_manager.return_value.remove_file_metadata.assert_called_once_with(
            'README.md')

        # Check if appropriate messages were printed
        mock_print_info.assert_any_call(
            "Updating metadata based on the provided description...")
        mock_print_success.assert_any_call(
            "Updated metadata for file: /fake/project/dir/src/main.py")
        mock_print_success.assert_any_call(
            "Removed metadata for file: README.md")
        mock_print_success.assert_any_call("Metadata update completed.")

    @patch('drd.metadata.updater.ProjectMetadataManager')
    @patch('drd.metadata.updater.get_ignore_patterns')
    @patch('drd.metadata.updater.get_folder_structure')
    @patch('drd.metadata.updater.call_dravid_api_with_pagination')
    @patch('drd.metadata.updater.extract_and_parse_xml')
    @patch('drd.metadata.updater.print_info')
    @patch('drd.metadata.updater.print_error')
    def test_update_metadata_with_dravid_no_files(self, mock_print_error, mock_print_info,
                                                  mock_extract_xml, mock_call_api,
                                                  mock_get_folder_structure, mock_get_ignore_patterns,
                                                  mock_metadata_manager):
        # Set up mocks
        mock_metadata_manager.return_value.get_project_context.return_value = self.project_context
        mock_get_ignore_patterns.return_value = (
            [], "No ignore patterns found")
        mock_get_folder_structure.return_value = self.folder_structure

        mock_call_api.return_value = "<response><files></files></response>"
        mock_root = ET.fromstring(mock_call_api.return_value)
        mock_extract_xml.return_value = mock_root

        # Call the function
        update_metadata_with_dravid(self.meta_description, self.current_dir)

        # Assertions
        mock_print_info.assert_any_call(
            "No files identified for metadata update or removal.")

    @patch('drd.metadata.updater.ProjectMetadataManager')
    @patch('drd.metadata.updater.get_ignore_patterns')
    @patch('drd.metadata.updater.get_folder_structure')
    @patch('drd.metadata.updater.call_dravid_api_with_pagination')
    @patch('drd.metadata.updater.extract_and_parse_xml')
    @patch('drd.metadata.updater.print_error')
    def test_update_metadata_with_dravid_error(self, mock_print_error, mock_extract_xml,
                                               mock_call_api, mock_get_folder_structure,
                                               mock_get_ignore_patterns, mock_metadata_manager):
        # Set up mocks
        mock_metadata_manager.return_value.get_project_context.return_value = self.project_context
        mock_get_ignore_patterns.return_value = (
            [], "No ignore patterns found")
        mock_get_folder_structure.return_value = self.folder_structure

        mock_call_api.return_value = "Invalid XML"
        mock_extract_xml.side_effect = Exception("XML parsing error")

        # Call the function
        update_metadata_with_dravid(self.meta_description, self.current_dir)

        # Assertions
        mock_print_error.assert_any_call(
            "Error parsing dravid's response: XML parsing error")
        mock_print_error.assert_any_call("Raw response: Invalid XML")


if __name__ == '__main__':
    unittest.main()

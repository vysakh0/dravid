import unittest
from unittest.mock import patch, mock_open
import os
import xml.etree.ElementTree as ET

from drd.utils.file_utils import (
    parse_file_list_response,
    get_file_content,
    parse_find_file_response,
    fetch_project_guidelines
)


class TestFileOperations(unittest.TestCase):

    @patch('drd.utils.file_utils.extract_and_parse_xml')
    def test_parse_file_list_response_success(self, mock_extract_and_parse_xml):
        mock_root = ET.Element('response')
        ET.SubElement(mock_root, 'file').text = 'file1.txt'
        ET.SubElement(mock_root, 'file').text = 'file2.txt'
        mock_extract_and_parse_xml.return_value = mock_root

        response = "<response><file>file1.txt</file><file>file2.txt</file></response>"
        result = parse_file_list_response(response)

        self.assertEqual(result, ['file1.txt', 'file2.txt'])

    @patch('drd.utils.file_utils.extract_and_parse_xml')
    @patch('drd.utils.file_utils.print_error')
    def test_parse_file_list_response_error(self, mock_print_error, mock_extract_and_parse_xml):
        mock_extract_and_parse_xml.side_effect = Exception("Test error")

        response = "<invalid>xml</invalid>"
        result = parse_file_list_response(response)

        self.assertEqual(result, [])
        mock_print_error.assert_called_once_with(
            "Error parsing file list response: Test error")

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="file content")
    def test_get_file_content_existing_file(self, mock_file, mock_exists):
        mock_exists.return_value = True
        result = get_file_content("test.txt")
        self.assertEqual(result, "file content")

    @patch('os.path.exists')
    def test_get_file_content_non_existing_file(self, mock_exists):
        mock_exists.return_value = False
        result = get_file_content("non_existing.txt")
        self.assertIsNone(result)

    @patch('drd.utils.file_utils.extract_and_parse_xml')
    def test_parse_find_file_response_success(self, mock_extract_and_parse_xml):
        mock_root = ET.Element('response')
        ET.SubElement(mock_root, 'file').text = 'found_file.txt'
        mock_extract_and_parse_xml.return_value = mock_root

        response = "<response><file>found_file.txt</file></response>"
        result = parse_find_file_response(response)

        self.assertEqual(result, 'found_file.txt')

    @patch('drd.utils.file_utils.extract_and_parse_xml')
    @patch('drd.utils.file_utils.print_error')
    def test_parse_find_file_response_error(self, mock_print_error, mock_extract_and_parse_xml):
        mock_extract_and_parse_xml.side_effect = Exception("Test error")

        response = "<invalid>xml</invalid>"
        result = parse_find_file_response(response)

        self.assertIsNone(result)
        mock_print_error.assert_called_once_with(
            "Error parsing dravid's response: Test error")

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="Project guidelines content")
    @patch('drd.utils.file_utils.print_info')
    def test_fetch_project_guidelines_existing_file(self, mock_print_info, mock_file, mock_exists):
        mock_exists.return_value = True
        result = fetch_project_guidelines("/fake/project/dir")
        self.assertEqual(result, "Project guidelines content")
        mock_print_info.assert_called_once_with(
            "Project guidelines found and included in the context.")

    @patch('os.path.exists')
    def test_fetch_project_guidelines_non_existing_file(self, mock_exists):
        mock_exists.return_value = False
        result = fetch_project_guidelines("/fake/project/dir")
        self.assertEqual(result, "")

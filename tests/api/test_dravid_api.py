import unittest
from unittest.mock import patch, MagicMock
from drd.api.dravid_api import (
    stream_dravid_api,
    parse_streaming_xml,
    parse_step,
    call_dravid_api,
    call_dravid_vision_api
)


class TestDravidAPI(unittest.TestCase):

    @patch('drd.api.dravid_api.stream_claude_response')
    @patch('drd.api.dravid_api.pretty_print_xml_stream')
    @patch('drd.api.dravid_api.Loader')
    def test_stream_dravid_api(self, mock_loader, mock_pretty_print, mock_stream_response):
        mock_stream_response.return_value = [
            "<response><step><type>shell</type><command>echo 'test'</command></step>",
            "<step><type>file</type><operation>CREATE</operation><filename>test.txt</filename><content>Test content</content></step></response>"
        ]

        result = list(stream_dravid_api("test query"))

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0], [{'type': 'shell', 'command': "echo 'test'"}])
        self.assertEqual(result[1], [
                         {'type': 'file', 'operation': 'CREATE', 'filename': 'test.txt', 'content': 'Test content'}])

    def test_parse_streaming_xml(self):
        xml_buffer = "<step><type>shell</type><command>echo 'test'</command></step><step><type>file</type><operation>CREATE</operation><filename>test.txt</filename><content>Test content</content></step>"

        result = parse_streaming_xml(xml_buffer)

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0], {'type': 'shell', 'command': "echo 'test'"})
        self.assertEqual(result[1], {'type': 'file', 'operation': 'CREATE',
                         'filename': 'test.txt', 'content': 'Test content'})

    def test_parse_step(self):
        step_content = "<type>shell</type><command>echo 'test'</command>"

        result = parse_step(step_content)

        self.assertEqual(result, {'type': 'shell', 'command': "echo 'test'"})

    @patch('drd.api.dravid_api.call_dravid_api_with_pagination')
    @patch('drd.api.dravid_api.parse_dravid_response')
    def test_call_dravid_api(self, mock_parse_response, mock_call_api):
        mock_call_api.return_value = "<response><step><type>shell</type><command>echo 'test'</command></step></response>"
        mock_parse_response.return_value = [
            {'type': 'shell', 'command': "echo 'test'"}]

        result = call_dravid_api("test query")

        self.assertEqual(result, [{'type': 'shell', 'command': "echo 'test'"}])
        mock_call_api.assert_called_once_with("test query", False, None)
        mock_parse_response.assert_called_once_with(
            "<response><step><type>shell</type><command>echo 'test'</command></step></response>")

    @patch('drd.api.dravid_api.call_dravid_vision_api_with_pagination')
    @patch('drd.api.dravid_api.parse_dravid_response')
    def test_call_dravid_vision_api(self, mock_parse_response, mock_call_vision_api):
        mock_call_vision_api.return_value = "<response><step><type>shell</type><command>echo 'test'</command></step></response>"
        mock_parse_response.return_value = [
            {'type': 'shell', 'command': "echo 'test'"}]

        result = call_dravid_vision_api("test query", "image.jpg")

        self.assertEqual(result, [{'type': 'shell', 'command': "echo 'test'"}])
        mock_call_vision_api.assert_called_once_with(
            "test query", "image.jpg", False, None)
        mock_parse_response.assert_called_once_with(
            "<response><step><type>shell</type><command>echo 'test'</command></step></response>")

import unittest
from unittest.mock import patch, MagicMock, call
from drd.api.main import (
    stream_dravid_api,
    call_dravid_api,
    call_dravid_vision_api
)


class TestDravidAPI(unittest.TestCase):

    @patch('drd.api.main.stream_claude_response')
    @patch('drd.api.main.pretty_print_xml_stream')
    @patch('drd.api.main.Loader')
    @patch('click.echo')
    def test_stream_dravid_api(self, mock_echo, mock_loader, mock_pretty_print, mock_stream_response):
        xml_res = [
            "<response><step><type>shell</type><command>echo 'test'</command></step>",
            "<step><type>file</type><operation>CREATE</operation><filename>test.txt</filename><content>Test content</content></step></response>"
        ]
        mock_stream_response.return_value = xml_res

        # Test when print_chunk is False
        result = stream_dravid_api("test query", print_chunk=False)
        self.assertEqual(result, "".join(xml_res))
        mock_pretty_print.assert_has_calls(
            [call(chunk, {'buffer': '', 'in_step': False}) for chunk in xml_res])
        mock_echo.assert_not_called()

        # Reset mocks
        mock_pretty_print.reset_mock()
        mock_echo.reset_mock()

        # Test when print_chunk is True
        result = stream_dravid_api("test query", print_chunk=True)
        self.assertIsNone(result)
        mock_echo.assert_has_calls([call(chunk, nl=False)
                                   for chunk in xml_res])
        mock_pretty_print.assert_not_called()

        # Ensure the loader was started and stopped in both cases
        self.assertEqual(mock_loader.return_value.start.call_count, 2)
        # for chunk=true it gets stopped in the beginning
        self.assertEqual(mock_loader.return_value.stop.call_count, 3)

        # Test with include_context and instruction_prompt
        stream_dravid_api("test query", include_context=True,
                          instruction_prompt="Test prompt", print_chunk=False)
        mock_stream_response.assert_called_with("test query", "Test prompt")

    @patch('drd.api.main.call_dravid_api_with_pagination')
    @patch('drd.api.main.parse_dravid_response')
    def test_call_dravid_api(self, mock_parse_response, mock_call_api):
        mock_call_api.return_value = "<response><step><type>shell</type><command>echo 'test'</command></step></response>"
        mock_parse_response.return_value = [
            {'type': 'shell', 'command': "echo 'test'"}]

        result = call_dravid_api("test query")

        self.assertEqual(result, [{'type': 'shell', 'command': "echo 'test'"}])
        mock_call_api.assert_called_once_with("test query", False, None)
        mock_parse_response.assert_called_once_with(
            "<response><step><type>shell</type><command>echo 'test'</command></step></response>")

    @patch('drd.api.main.call_claude_vision_api_with_pagination')
    @patch('drd.api.main.parse_dravid_response')
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

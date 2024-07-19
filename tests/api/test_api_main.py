import unittest
from unittest.mock import patch, MagicMock, call
from drd.api.main import (
    stream_dravid_api,
    call_dravid_api,
    call_dravid_vision_api,
    get_api_functions
)


class TestDravidAPI(unittest.TestCase):

    @patch('drd.api.main.get_api_functions')
    @patch('drd.api.main.pretty_print_xml_stream')
    @patch('drd.api.main.Loader')
    @patch('click.echo')
    def test_stream_dravid_api(self, mock_echo, mock_loader, mock_pretty_print, mock_get_api_functions):
        mock_stream_response = MagicMock()
        mock_get_api_functions.return_value = (
            None, None, mock_stream_response)

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

        # Test with include_context and instruction_prompt
        stream_dravid_api("test query", include_context=True,
                          instruction_prompt="Test prompt", print_chunk=False)
        mock_stream_response.assert_called_with("test query", "Test prompt")

    @patch('drd.api.main.get_api_functions')
    @patch('drd.api.main.parse_dravid_response')
    def test_call_dravid_api(self, mock_parse_response, mock_get_api_functions):
        mock_call_api = MagicMock()
        mock_get_api_functions.return_value = (mock_call_api, None, None)

        mock_call_api.return_value = "<response><step><type>shell</type><command>echo 'test'</command></step></response>"
        mock_parse_response.return_value = [
            {'type': 'shell', 'command': "echo 'test'"}]

        result = call_dravid_api("test query")

        self.assertEqual(result, [{'type': 'shell', 'command': "echo 'test'"}])
        mock_call_api.assert_called_once_with("test query", False, None)
        mock_parse_response.assert_called_once_with(
            "<response><step><type>shell</type><command>echo 'test'</command></step></response>")

    @patch('drd.api.main.get_api_functions')
    @patch('drd.api.main.parse_dravid_response')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b'test image data')
    def test_call_dravid_vision_api(self, mock_open, mock_parse_response, mock_get_api_functions):
        mock_call_vision_api = MagicMock()
        mock_get_api_functions.return_value = (
            None, mock_call_vision_api, None)

        mock_call_vision_api.return_value = "<response><step><type>shell</type><command>echo 'test'</command></step></response>"
        mock_parse_response.return_value = [
            {'type': 'shell', 'command': "echo 'test'"}]

        result = call_dravid_vision_api("test query", "image.jpg")

        self.assertEqual(result, [{'type': 'shell', 'command': "echo 'test'"}])
        mock_call_vision_api.assert_called_once_with(
            "test query", "image.jpg", False, None)
        mock_parse_response.assert_called_once_with(
            "<response><step><type>shell</type><command>echo 'test'</command></step></response>")

import unittest
from unittest.mock import patch, MagicMock
import os
import json
import xml.etree.ElementTree as ET
from io import BytesIO

from drd.utils.api_utils import (
    get_api_key,
    get_headers,
    make_api_call,
    parse_response,
    call_dravid_api_with_pagination,
    call_dravid_vision_api_with_pagination,
    stream_claude_response,
    parse_paginated_response
)


class TestApiUtils(unittest.TestCase):

    def setUp(self):
        self.api_key = "test_api_key"
        self.query = "Test query"
        self.image_path = "test_image.jpg"

    @patch.dict(os.environ, {"CLAUDE_API_KEY": "test_api_key"})
    def test_get_api_key(self):
        self.assertEqual(get_api_key(), "test_api_key")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_key_missing(self):
        with self.assertRaises(ValueError):
            get_api_key()

    def test_get_headers(self):
        headers = get_headers(self.api_key)
        self.assertEqual(headers['x-api-key'], self.api_key)
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['Anthropic-Version'], '2023-06-01')

    @patch('requests.post')
    def test_make_api_call(self, mock_post):
        mock_response = MagicMock()
        mock_post.return_value = mock_response
        data = {"key": "value"}
        headers = {"header": "value"}

        response = make_api_call(data, headers)

        mock_post.assert_called_once_with(
            'https://api.anthropic.com/v1/messages', json=data, headers=headers, stream=False)
        self.assertEqual(response, mock_response)

    def test_parse_response_valid_xml(self):
        xml_response = "<response><content>Test content</content></response>"
        parsed = parse_response(xml_response)
        self.assertEqual(parsed, xml_response)

    @patch('drd.utils.api_utils.click.echo')
    def test_parse_response_invalid_xml(self, mock_echo):
        invalid_xml = "Not XML"
        parsed = parse_response(invalid_xml)
        self.assertEqual(parsed, invalid_xml)
        mock_echo.assert_called_once()

    @patch('drd.utils.api_utils.get_api_key')
    @patch('drd.utils.api_utils.make_api_call')
    def test_call_dravid_api_with_pagination(self, mock_make_api_call, mock_get_api_key):
        mock_get_api_key.return_value = self.api_key
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'content': [{'text': "<response>Test response</response>"}],
            'stop_reason': 'stop'
        }
        mock_make_api_call.return_value = mock_response

        response = call_dravid_api_with_pagination(self.query)
        self.assertEqual(response, "<response>Test response</response>")

    @patch('drd.utils.api_utils.get_api_key')
    @patch('drd.utils.api_utils.make_api_call')
    @patch('drd.utils.api_utils.mimetypes.guess_type')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b'test image data')
    def test_call_dravid_vision_api_with_pagination(self, mock_open, mock_guess_type, mock_make_api_call, mock_get_api_key):
        mock_get_api_key.return_value = self.api_key
        mock_guess_type.return_value = ('image/jpeg', None)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'content': [{'text': "<response>Test vision response</response>"}],
            'stop_reason': 'stop'
        }
        mock_make_api_call.return_value = mock_response

        response = call_dravid_vision_api_with_pagination(
            self.query, self.image_path)
        self.assertEqual(response, "<response>Test vision response</response>")

        # Check if the function was called with the correct arguments
        mock_make_api_call.assert_called_once()
        call_args = mock_make_api_call.call_args[0][0]
        self.assertEqual(call_args['messages'][0]
                         ['content'][0]['type'], 'image')
        self.assertEqual(call_args['messages'][0]
                         ['content'][0]['source']['type'], 'base64')
        self.assertEqual(call_args['messages'][0]['content']
                         [0]['source']['media_type'], 'image/jpeg')
        self.assertEqual(call_args['messages'][0]
                         ['content'][1]['type'], 'text')
        self.assertEqual(call_args['messages'][0]
                         ['content'][1]['text'], self.query)

    @patch('drd.utils.api_utils.get_api_key')
    @patch('drd.utils.api_utils.make_api_call')
    def test_stream_claude_response(self, mock_make_api_call, mock_get_api_key):
        mock_get_api_key.return_value = self.api_key
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            b'data: {"type": "content_block_delta", "delta": {"text": "Test"}}',
            b'data: {"type": "content_block_delta", "delta": {"text": " stream"}}',
            b'data: {"type": "message_stop"}'
        ]
        mock_make_api_call.return_value = mock_response

        result = list(stream_claude_response(self.query))
        self.assertEqual(result, ["Test", " stream"])

    def test_parse_paginated_response_xml(self):
        xml_response = "<response><step><type>test</type><content>Test content</content></step></response>"
        parsed = parse_paginated_response(xml_response)
        self.assertEqual(parsed, [{'type': 'test', 'content': 'Test content'}])

    def test_parse_paginated_response_text(self):
        text_response = "Regular text response"
        parsed = parse_paginated_response(text_response)
        self.assertEqual(
            parsed, [{'type': 'explanation', 'content': 'Regular text response'}])
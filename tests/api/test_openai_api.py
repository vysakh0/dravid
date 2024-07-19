import unittest
from unittest.mock import patch, MagicMock
import os
import xml.etree.ElementTree as ET
from io import BytesIO

from drd.api.openai_api import (
    get_api_key,
    parse_response,
    call_openai_api_with_pagination,
    call_openai_vision_api_with_pagination,
    stream_openai_response,
)

MODEL = "gpt-4o-2024-05-13"


class TestOpenAIApiUtils(unittest.TestCase):

    def setUp(self):
        self.api_key = "test_openai_api_key"
        self.query = "Test query"
        self.image_path = "test_image.jpg"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_openai_api_key"})
    def test_get_api_key(self):
        self.assertEqual(get_api_key(), "test_openai_api_key")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_key_missing(self):
        with self.assertRaises(ValueError):
            get_api_key()

    def test_parse_response_valid_xml(self):
        xml_response = "<response><content>Test content</content></response>"
        parsed = parse_response(xml_response)
        self.assertEqual(parsed, xml_response)

    @patch('drd.api.openai_api.click.echo')
    def test_parse_response_invalid_xml(self, mock_echo):
        invalid_xml = "Not XML"
        parsed = parse_response(invalid_xml)
        self.assertEqual(parsed, invalid_xml)
        mock_echo.assert_called_once()

    @patch('drd.api.openai_api.client.chat.completions.create')
    def test_call_openai_api_with_pagination(self, mock_create):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "<response>Test response</response>"
        mock_response.choices[0].finish_reason = 'stop'
        mock_create.return_value = mock_response

        response = call_openai_api_with_pagination(self.query)
        self.assertEqual(response, "<response>Test response</response>")

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['model'], MODEL)
        self.assertEqual(call_args['messages'][1]['content'], self.query)

    @patch('drd.api.openai_api.client.chat.completions.create')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b'test image data')
    def test_call_openai_vision_api_with_pagination(self, mock_open, mock_create):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "<response>Test vision response</response>"
        mock_response.choices[0].finish_reason = 'stop'
        mock_create.return_value = mock_response

        response = call_openai_vision_api_with_pagination(
            self.query, self.image_path)
        self.assertEqual(response, "<response>Test vision response</response>")

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['model'], MODEL)
        self.assertEqual(call_args['messages'][1]
                         ['content'][0]['type'], 'text')
        self.assertEqual(call_args['messages'][1]
                         ['content'][0]['text'], self.query)
        self.assertEqual(call_args['messages'][1]
                         ['content'][1]['type'], 'image_url')
        self.assertTrue(call_args['messages'][1]['content'][1]
                        ['image_url']['url'].startswith('data:image/jpeg;base64,'))

    @patch('drd.api.openai_api.client.chat.completions.create')
    def test_stream_openai_response(self, mock_create):
        mock_response = MagicMock()
        mock_response.__iter__.return_value = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Test"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" stream"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=None))])
        ]
        mock_create.return_value = mock_response

        result = list(stream_openai_response(self.query))
        self.assertEqual(result, ["Test", " stream"])

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['model'], MODEL)
        self.assertEqual(call_args['messages'][1]['content'], self.query)
        self.assertTrue(call_args['stream'])

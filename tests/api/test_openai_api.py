import unittest
from unittest.mock import patch, MagicMock
import os
from openai import OpenAI, AzureOpenAI

from drd.api.openai_api import (
    get_env_variable,
    get_client,
    get_model,
    parse_response,
    call_api_with_pagination,
    call_vision_api_with_pagination,
    stream_response,
    DEFAULT_MODEL
)


class TestOpenAIApiUtils(unittest.TestCase):

    def setUp(self):
        self.api_key = "test_api_key"
        self.query = "Test query"
        self.image_path = "test_image.jpg"

    # ... (keep the existing tests for get_env_variable, get_client, get_model, and parse_response) ...

    @patch('drd.api.openai_api.get_client')
    @patch('drd.api.openai_api.get_model')
    @patch.dict(os.environ, {"DRAVID_LLM": "openai", "OPENAI_MODEL": DEFAULT_MODEL})
    def test_call_api_with_pagination(self, mock_get_model, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_get_model.return_value = DEFAULT_MODEL

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "<response>Test response</response>"
        mock_response.choices[0].finish_reason = 'stop'
        mock_client.chat.completions.create.return_value = mock_response

        response = call_api_with_pagination(self.query)
        self.assertEqual(response, "<response>Test response</response>")

        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args['model'], DEFAULT_MODEL)
        self.assertEqual(call_args['messages'][1]['content'], self.query)

    @patch('drd.api.openai_api.get_client')
    @patch('drd.api.openai_api.get_model')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b'test image data')
    @patch.dict(os.environ, {"DRAVID_LLM": "openai", "OPENAI_MODEL": DEFAULT_MODEL})
    def test_call_vision_api_with_pagination(self, mock_open, mock_get_model, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_get_model.return_value = DEFAULT_MODEL

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "<response>Test vision response</response>"
        mock_response.choices[0].finish_reason = 'stop'
        mock_client.chat.completions.create.return_value = mock_response

        response = call_vision_api_with_pagination(self.query, self.image_path)
        self.assertEqual(response, "<response>Test vision response</response>")

        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args['model'], DEFAULT_MODEL)
        self.assertEqual(call_args['messages'][1]
                         ['content'][0]['type'], 'text')
        self.assertEqual(call_args['messages'][1]
                         ['content'][0]['text'], self.query)
        self.assertEqual(call_args['messages'][1]
                         ['content'][1]['type'], 'image_url')
        self.assertTrue(call_args['messages'][1]['content'][1]
                        ['image_url']['url'].startswith('data:image/jpeg;base64,'))

    @patch('drd.api.openai_api.get_client')
    @patch('drd.api.openai_api.get_model')
    @patch.dict(os.environ, {"DRAVID_LLM": "openai", "OPENAI_MODEL": DEFAULT_MODEL})
    def test_stream_response(self, mock_get_model, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_get_model.return_value = DEFAULT_MODEL

        mock_response = MagicMock()
        mock_response.__iter__.return_value = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Test"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" stream"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=None))])
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = list(stream_response(self.query))
        self.assertEqual(result, ["Test", " stream"])

        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args['model'], DEFAULT_MODEL)
        self.assertEqual(call_args['messages'][1]['content'], self.query)
        self.assertTrue(call_args['stream'])


if __name__ == '__main__':
    unittest.main()

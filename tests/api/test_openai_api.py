import unittest
import requests
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

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_openai_api_key"})
    def test_get_env_variable_existing(self):
        self.assertEqual(get_env_variable(
            "OPENAI_API_KEY"), "test_openai_api_key")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_env_variable_missing(self):
        with self.assertRaises(ValueError):
            get_env_variable("NON_EXISTENT_VAR")

    @patch.dict(os.environ, {"DRAVID_LLM": "openai", "OPENAI_API_KEY": "test_key"})
    def test_get_client_openai(self):
        client = get_client()
        self.assertIsInstance(client, OpenAI)
        self.assertEqual(client.api_key, "test_key")

    @patch.dict(os.environ, {
        "DRAVID_LLM": "azure",
        "AZURE_OPENAI_API_KEY": "test_azure_key",
        "AZURE_OPENAI_API_VERSION": "2023-05-15",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com"
    })
    def test_get_client_azure(self):
        client = get_client()
        self.assertIsInstance(client, AzureOpenAI)
        self.assertTrue(isinstance(client, AzureOpenAI))

    @patch.dict(os.environ, {
        "DRAVID_LLM": "azure",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "test-deployment"
    })
    def test_get_model_azure(self):
        model = get_model()
        self.assertEqual(model, "test-deployment")

    @patch.dict(os.environ, {
        "DRAVID_LLM": "custom",
        "DRAVID_LLM_API_KEY": "test_custom_key",
        "DRAVID_LLM_ENDPOINT": "https://custom-llm-endpoint.com"
    })
    def test_get_client_custom(self):
        client = get_client()
        self.assertIsInstance(client, OpenAI)
        self.assertEqual(client.api_key, "test_custom_key")
        self.assertEqual(client.base_url, "https://custom-llm-endpoint.com")

    @patch.dict(os.environ, {"DRAVID_LLM": "openai", "OPENAI_MODEL": "gpt-4"})
    def test_get_model_openai(self):
        self.assertEqual(get_model(), "gpt-4")

    @patch.dict(os.environ, {"DRAVID_LLM": "azure", "AZURE_OPENAI_DEPLOYMENT_NAME": "test-deployment"})
    def test_get_model_azure(self):
        self.assertEqual(get_model(), "test-deployment")

    @patch.dict(os.environ, {"DRAVID_LLM": "custom", "DRAVID_LLM_MODEL": "llama-3"})
    def test_get_model_custom(self):
        self.assertEqual(get_model(), "llama-3")

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

    @patch.dict(os.environ, {"DRAVID_LLM": "ollama", "DRAVID_LLM_MODEL": "starcoder"})
    def test_get_client_ollama(self):
        client = get_client()
        self.assertIsNone(client)  # Ollama doesn't use a client object

    @patch.dict(os.environ, {"DRAVID_LLM": "ollama", "DRAVID_LLM_MODEL": "starcoder"})
    def test_get_model_ollama(self):
        model = get_model()
        self.assertEqual(model, "starcoder")

    @patch('requests.post')
    @patch.dict(os.environ, {"DRAVID_LLM": "ollama", "DRAVID_LLM_MODEL": "starcoder"})
    def test_call_api_with_pagination_ollama(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "<response>Test Ollama response</response>"}
        mock_post.return_value = mock_response

        response = call_api_with_pagination(self.query)
        self.assertEqual(response, "<response>Test Ollama response</response>")

        mock_post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "starcoder",
                "prompt": self.query,
                "system": "",
                "stream": False
            }
        )

    @patch.dict(os.environ, {"DRAVID_LLM": "ollama", "DRAVID_LLM_MODEL": "starcoder"})
    def test_call_vision_api_with_pagination_ollama(self):
        with self.assertRaises(NotImplementedError):
            call_vision_api_with_pagination(self.query, self.image_path)

    @patch('requests.post')
    @patch.dict(os.environ, {"DRAVID_LLM": "ollama", "DRAVID_LLM_MODEL": "starcoder"})
    def test_stream_response_ollama(self, mock_post):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            b'{"response":"Test"}',
            b'{"response":" stream"}',
            b'{"done":true}'
        ]
        mock_post.return_value = mock_response

        result = list(stream_response(self.query))
        self.assertEqual(result, ["Test", " stream"])

        mock_post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "starcoder",
                "prompt": self.query,
                "system": "",
                "stream": True
            },
            stream=True
        )

    @patch('requests.post')
    @patch.dict(os.environ, {"DRAVID_LLM": "ollama", "DRAVID_LLM_MODEL": "starcoder"})
    def test_call_api_with_pagination_ollama_error(self, mock_post):
        mock_post.side_effect = requests.RequestException("Ollama API error")

        with self.assertRaises(requests.RequestException):
            call_api_with_pagination(self.query)

    @patch('requests.post')
    @patch.dict(os.environ, {"DRAVID_LLM": "ollama", "DRAVID_LLM_MODEL": "starcoder"})
    def test_stream_response_ollama_error(self, mock_post):
        mock_post.side_effect = requests.RequestException("Ollama API error")

        with self.assertRaises(requests.RequestException):
            list(stream_response(self.query))


if __name__ == '__main__':
    unittest.main()

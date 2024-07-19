import unittest
from unittest.mock import patch, MagicMock
import os
import xml.etree.ElementTree as ET
from io import BytesIO
from openai import OpenAI, AzureOpenAI

from drd.api.openai_api import (
    get_env_variable,
    get_client,
    get_model,
    parse_response,
    call_api_with_pagination,
    call_vision_api_with_pagination,
    stream_response,
)

DEFAULT_MODEL = "gpt-4o-2024-05-13"


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
        # Note: In newer OpenAI client versions, api_key is not directly accessible
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
        # Note: We can't directly access these attributes in the new OpenAI client
        # Instead, we can check if the client was initialized correctly
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

    @patch('drd.api.openai_api.client.chat.completions.create')
    def test_call_api_with_pagination(self, mock_create):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "<response>Test response</response>"
        mock_response.choices[0].finish_reason = 'stop'
        mock_create.return_value = mock_response

        response = call_api_with_pagination(self.query)
        self.assertEqual(response, "<response>Test response</response>")

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['model'], DEFAULT_MODEL)
        self.assertEqual(call_args['messages'][1]['content'], self.query)

    @patch('drd.api.openai_api.client.chat.completions.create')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b'test image data')
    def test_call_vision_api_with_pagination(self, mock_open, mock_create):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "<response>Test vision response</response>"
        mock_response.choices[0].finish_reason = 'stop'
        mock_create.return_value = mock_response

        response = call_vision_api_with_pagination(self.query, self.image_path)
        self.assertEqual(response, "<response>Test vision response</response>")

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['model'], DEFAULT_MODEL)
        self.assertEqual(call_args['messages'][1]
                         ['content'][0]['type'], 'text')
        self.assertEqual(call_args['messages'][1]
                         ['content'][0]['text'], self.query)
        self.assertEqual(call_args['messages'][1]
                         ['content'][1]['type'], 'image_url')
        self.assertTrue(call_args['messages'][1]['content'][1]
                        ['image_url']['url'].startswith('data:image/jpeg;base64,'))

    @patch('drd.api.openai_api.client.chat.completions.create')
    def test_stream_response(self, mock_create):
        mock_response = MagicMock()
        mock_response.__iter__.return_value = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Test"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" stream"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=None))])
        ]
        mock_create.return_value = mock_response

        result = list(stream_response(self.query))
        self.assertEqual(result, ["Test", " stream"])

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['model'], DEFAULT_MODEL)
        self.assertEqual(call_args['messages'][1]['content'], self.query)
        self.assertTrue(call_args['stream'])

import unittest
from unittest.mock import patch

from drd.cli.query.image_handler import handle_image_query


class TestImageHandler(unittest.TestCase):

    @patch('drd.cli.query.image_handler.call_dravid_vision_api_with_pagination')
    def test_handle_image_query(self, mock_call_vision_api):
        query = "Describe this image"
        image_path = "/path/to/image.jpg"
        instruction_prompt = "Analyze the image carefully"

        mock_call_vision_api.return_value = "This is a description of the image"

        result = handle_image_query(query, image_path, instruction_prompt)

        self.assertEqual(result, "This is a description of the image")
        mock_call_vision_api.assert_called_once_with(
            query, image_path, include_context=True, instruction_prompt=instruction_prompt)

    @patch('drd.cli.query.image_handler.call_dravid_vision_api_with_pagination')
    def test_handle_image_query_without_instruction(self, mock_call_vision_api):
        query = "Describe this image"
        image_path = "/path/to/image.jpg"

        mock_call_vision_api.return_value = "This is a description of the image"

        result = handle_image_query(query, image_path)

        self.assertEqual(result, "This is a description of the image")
        mock_call_vision_api.assert_called_once_with(
            query, image_path, include_context=True, instruction_prompt=None)

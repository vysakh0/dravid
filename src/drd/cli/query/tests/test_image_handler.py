from src.drd.cli.query.image_handler import handle_image_query
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..')))


class TestImageHandler(unittest.TestCase):

    @patch('src.drd.cli.query.image_handler.call_dravid_vision_api')
    def test_handle_image_query(self, mock_call_dravid_vision_api):
        # Mock the response from call_dravid_vision_api
        mock_call_dravid_vision_api.return_value = "<response><explanation>Test image response</explanation></response>"

        # Test data
        query = "Analyze this image"
        image_path = "/path/to/test_image.jpg"
        instruction_prompt = "Test instruction prompt"

        # Call the function
        result = handle_image_query(query, image_path, instruction_prompt)

        # Assert that the result is as expected
        self.assertEqual(
            result, "<response><explanation>Test image response</explanation></response>")

        # Assert that call_dravid_vision_api was called with the correct arguments
        mock_call_dravid_vision_api.assert_called_once_with(
            query,
            image_path,
            include_context=True,
            instruction_prompt=instruction_prompt
        )

    @patch('src.drd.cli.query.image_handler.call_dravid_vision_api')
    def test_handle_image_query_no_instruction_prompt(self, mock_call_dravid_vision_api):
        # Mock the response from call_dravid_vision_api
        mock_call_dravid_vision_api.return_value = "<response><explanation>Test image response</explanation></response>"

        # Test data
        query = "Analyze this image"
        image_path = "/path/to/test_image.jpg"

        # Call the function without instruction_prompt
        result = handle_image_query(query, image_path)

        # Assert that the result is as expected
        self.assertEqual(
            result, "<response><explanation>Test image response</explanation></response>")

        # Assert that call_dravid_vision_api was called with the correct arguments
        mock_call_dravid_vision_api.assert_called_once_with(
            query,
            image_path,
            include_context=True,
            instruction_prompt=None
        )


if __name__ == '__main__':
    unittest.main()

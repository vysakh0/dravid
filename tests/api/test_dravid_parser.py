import unittest
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET
from drd.api.dravid_parser import (
    extract_outermost_xml,
    escape_nested_cdata,
    escape_special_characters,
    extract_and_parse_xml,
    parse_dravid_response,
    pretty_print_commands
)


class TestDravidParser(unittest.TestCase):

    def test_extract_outermost_xml(self):
        response = "Some text before <response><content>Test</content></response> Some text after"
        result = extract_outermost_xml(response)
        self.assertEqual(
            result, "<response><content>Test</content></response>")

        with self.assertRaises(ValueError):
            extract_outermost_xml("No XML here")

    def test_escape_nested_cdata(self):
        xml = "<![CDATA[Test]]>"
        result = escape_nested_cdata(xml)
        self.assertEqual(result, "<![CDATA[Test]]>")

        xml_with_nested = "<![CDATA[Test ]]> nested ]]>"
        result = escape_nested_cdata(xml_with_nested)
        self.assertEqual(result, "<![CDATA[Test ]]]]><![CDATA[> nested ]]>")

    def test_escape_special_characters(self):
        text = "Test & < >"
        result = escape_special_characters(text)
        self.assertEqual(result, "Test &amp; &lt; &gt;")

    def test_extract_and_parse_xml(self):
        response = "<response><content>Test</content></response>"
        result = extract_and_parse_xml(response)
        self.assertIsInstance(result, ET.Element)
        self.assertEqual(result.tag, "response")
        self.assertEqual(result.find("content").text, "Test")

    def test_parse_dravid_response(self):
        response = """
        <response>
            <explanation>Test explanation</explanation>
            <steps>
                <step>
                    <type>shell</type>
                    <command>echo "Hello"</command>
                </step>
                <step>
                    <type>file</type>
                    <operation>CREATE</operation>
                    <filename>test.txt</filename>
                    <content>Test content</content>
                </step>
            </steps>
        </response>
        """
        result = parse_dravid_response(response)
        self.assertEqual(len(result), 3)
        self.assertEqual(
            result[0], {"type": "explanation", "content": "Test explanation"})
        self.assertEqual(
            result[1], {"type": "shell", "command": 'echo "Hello"'})
        self.assertEqual(result[2], {"type": "file", "operation": "CREATE",
                         "filename": "test.txt", "content": "Test content"})

    @patch('drd.api.dravid_parser.click.echo')
    @patch('drd.api.dravid_parser.highlight')
    def test_pretty_print_commands(self, mock_highlight, mock_echo):
        commands = [
            {"type": "explanation", "content": "Test explanation"},
            {"type": "shell", "command": 'echo "Hello"'},
            {"type": "file", "operation": "CREATE",
                "filename": "test.txt", "content": "Test content"}
        ]
        mock_highlight.return_value = "Highlighted content"

        pretty_print_commands(commands)

        self.assertEqual(mock_echo.call_count, 10)

        self.assertEqual(mock_highlight.call_count, 2)

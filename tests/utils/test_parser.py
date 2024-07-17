import unittest
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET
from lxml import etree
from drd.utils.parser import (
    extract_outermost_xml,
    extract_and_parse_xml,
    parse_dravid_response,
    parse_file_list_response,
    parse_find_file_response
)


class TestDravidParser(unittest.TestCase):

    def test_extract_outermost_xml(self):
        response = "Some text before <response><content>Test</content></response> Some text after"
        result = extract_outermost_xml(response)
        self.assertEqual(
            result, "<response><content>Test</content></response>")

        with self.assertRaises(ValueError):
            extract_outermost_xml("No XML here")

    def test_extract_and_parse_xml(self):
        response = "<response><content>Test</content></response>"
        result = extract_and_parse_xml(response)
        self.assertIsInstance(result, etree._Element)
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

    def test_extract_and_parse_xml_with_html(self):
        response = """
        <response>
          <step>
            <type>file</type>
            <operation>CREATE</operation>
            <filename>index.html</filename>
            <content>
              <![CDATA[
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Welcome to MyApp</title>
                </head>
                <body>
                    <h1>Welcome to MyApp</h1>
                    <p>This is the landing page for our simple web project.</p>

                    <nav>
                        <ul>
                            <li><a href="hello.html">Hello Page</a></li>
                            <li><a href="about.html">About Page</a></li>
                        </ul>
                    </nav>
                </body>
                </html>
              ]]>
            </content>
          </step>
        </response>
        """
        result = extract_and_parse_xml(response)
        self.assertIsInstance(result, etree._Element)
        self.assertEqual(result.tag, "response")
        content = result.find(".//content").text
        self.assertIn("<!DOCTYPE html>", content)
        self.assertNotIn("CDATA", content)
        self.assertNotIn("]]", content)
        self.assertIn("<html lang=\"en\">", content)

    # TODO:  nested <![CDATA[This is doubly nested CDATA content]]>
    def test_nested_cdata(self):
        response = """
        <response>
          <step>
            <type>file</type>
            <operation>CREATE</operation>
            <filename>index.html</filename>
            <content>
              <![CDATA[
                <!DOCTYPE html>
                <html lang="en">
                    <![CDATA[ hello ]]
                </body>
                </html>
              ]]>
            </content>
          </step>
        </response>
        """
        result = extract_and_parse_xml(response)
        self.assertIsInstance(result, etree._Element)
        self.assertEqual(result.tag, "response")
        content = result.find(".//content").text
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("<![CDATA[ hello ]]", content)
        self.assertIn("<html lang=\"en\">", content)

    def test_nested_react_cdata(self):
        response = """
        <response>
          <step>
            <type>file</type>
            <operation>CREATE</operation>
            <filename>index.html</filename>
            <content>
              <![CDATA[
                    import Image from 'next/image'

                    export default function Home() {
                      return (
                        <main className="flex min-h-screen flex-col items-center justify-between p-24">
                          <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
                            <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
                                href="https://vercel.com?utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
                          </div>
                          </div>
                        </main>
                      )
                    }
              ]]>
            </content>
          </step>
        </response>
        """
        result = parse_dravid_response(response)
        self.assertEqual(len(result), 1)  # One step
        self.assertEqual(result[0]['type'], 'file')
        self.assertEqual(result[0]['operation'], 'CREATE')
        self.assertEqual(result[0]['filename'], 'index.html')
        self.assertIn('export default function Home', result[0]['content'])
        self.assertNotIn("<![CDATA[", result[0]['content'])
        self.assertNotIn("]]>", result[0]['content'])
        self.assertIn("import Image from 'next/image'", result[0]['content'])
        self.assertIn(
            'className="flex min-h-screen flex-col items-center justify-between p-24"', result[0]['content'])

    def test_nested_tags_in_cdata(self):
        response = """
        <response>
          <step>
            <type>file</type>
            <operation>CREATE</operation>
            <filename>script.js</filename>
            <content>
              <![CDATA[
                function createElement() {
                  const div = document.createElement('div');
                  div.innerHTML = '<p>This is a <strong>nested</strong> element</p>';
                  return div;
                }
              ]]>
            </content>
          </step>
        </response>
        """
        result = extract_and_parse_xml(response)
        self.assertIsInstance(result, etree._Element)
        content = result.find(".//content").text
        self.assertIn(
            "<p>This is a <strong>nested</strong> element</p>", content)

    def test_malformed_xml(self):
        response = """
        <response>
          <step>
            <type>file</type>
            <operation>CREATE</operation>
            <filename>index.html</filename>
            <content>
              <![CDATA[
                <div>
                  <p>This tag is not closed
                </div>
              ]]>
            </content>
          </step>
        </response>
        """
        result = extract_and_parse_xml(response)
        self.assertIsInstance(result, etree._Element)

    def test_malformed_html_in_cdata(self):
        response = """
        <response>
          <step>
            <type>file</type>
            <operation>CREATE</operation>
            <filename>index.html</filename>
            <content>
              <![CDATA[
                <div>
                  <p>This tag is not closed
                </div>
              ]]>
            </content>
          </step>
        </response>
        """
        result = extract_and_parse_xml(response)
        self.assertIsInstance(result, etree._Element)
        content = result.find(".//content").text
        self.assertIn("<div>", content)
        self.assertIn("<p>This tag is not closed", content)
        self.assertIn("</div>", content)

    def test_complex_cdata_content(self):
        response = """
        <response>
          <explanation>This is an explanation with CDATA content</explanation>
          <steps>
            <step>
              <type>file</type>
              <operation>CREATE</operation>
              <filename>complex_cdata.xml</filename>
              <content><![CDATA[
                <response>
                  <explanation>Nested explanation</explanation>
                  <steps>
                    <step>
                      <type>file</type>
                      <operation>UPDATE</operation>
                      <filename>nested_file.txt</filename>
                      <content><![CDATA[This is doubly nested CDATA content]]></content>
                    </step>
                  </steps>
                </response>
              ]]></content>
            </step>
          </steps>
        </response>
        """
        result = parse_dravid_response(response)
        self.assertEqual(len(result), 2)  # Explanation + 1 step
        self.assertEqual(result[0]['type'], 'explanation')
        self.assertEqual(result[0]['content'],
                         'This is an explanation with CDATA content')
        self.assertEqual(result[1]['type'], 'file')
        self.assertEqual(result[1]['operation'], 'CREATE')
        self.assertEqual(result[1]['filename'], 'complex_cdata.xml')
        self.assertIn('<response>', result[1]['content'])
        self.assertIn(
            '<explanation>Nested explanation</explanation>', result[1]['content'])
        # self.assertIn(
        # '<![CDATA[This is doubly nested CDATA content]]>', result[1]['content'])

    @ patch('drd.utils.parser.extract_and_parse_xml')
    def test_parse_file_list_response_success(self, mock_extract_and_parse_xml):
        mock_root = ET.Element('response')
        ET.SubElement(mock_root, 'file').text = 'file1.txt'
        ET.SubElement(mock_root, 'file').text = 'file2.txt'
        mock_extract_and_parse_xml.return_value = mock_root

        response = "<response><file>file1.txt</file><file>file2.txt</file></response>"
        result = parse_file_list_response(response)

        self.assertEqual(result, ['file1.txt', 'file2.txt'])

    @ patch('drd.utils.parser.extract_and_parse_xml')
    @ patch('drd.utils.utils.print_error')
    def test_parse_file_list_response_error(self, mock_print_error, mock_extract_and_parse_xml):
        mock_extract_and_parse_xml.side_effect = Exception("Test error")

        response = "<response><file>found_file.txt</file></response>"
        result = parse_file_list_response(response)
        self.assertIsNone(result)

    @ patch('drd.utils.parser.extract_and_parse_xml')
    @ patch('drd.utils.utils.print_error')
    def test_parse_find_file_response_error(self, mock_print_error, mock_extract_and_parse_xml):
        mock_extract_and_parse_xml.side_effect = Exception("Test error")

        response = "<response><>xml</invalid>"
        result = parse_find_file_response(response)

        self.assertIsNone(result)

    @ patch('drd.utils.parser.extract_and_parse_xml')
    def test_parse_find_file_response_success(self, mock_extract_and_parse_xml):
        mock_root = ET.Element('response')
        ET.SubElement(mock_root, 'file').text = 'found_file.txt'
        mock_extract_and_parse_xml.return_value = mock_root

        response = "<response><file>found_file.txt</file></response>"
        result = parse_find_file_response(response)

        self.assertEqual(result, 'found_file.txt')

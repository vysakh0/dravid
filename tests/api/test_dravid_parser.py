import unittest
from unittest.mock import patch, MagicMock
from lxml import etree
from drd.api.dravid_parser import (
    extract_outermost_xml,
    extract_and_parse_xml,
    parse_dravid_response,
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

    # def test_cdata_within_cdata(self):
    #     response = """
    #     <response>
    #       <step>
    #         <type>file</type>
    #         <operation>CREATE</operation>
    #         <filename>nested_cdata.txt</filename>
    #         <content>
    #           <![CDATA[
    #             This is outer CDATA
    #             <![CDATA[
    #               This is inner CDATA
    #             ]]>
    #             Back to outer CDATA
    #           ]]>
    #         </content>
    #       </step>
    #     </response>
    #     """
    #     result = extract_and_parse_xml(response)
    #     self.assertIsInstance(result, etree._Element)
    #     content = result.find(".//content").text
    #     self.assertIn("This is outer CDATA", content)
    #     self.assertIn("<![CDATA[", content)
    #     self.assertIn("This is inner CDATA", content)
    #     self.assertIn("]]>", content)
    #     self.assertIn("Back to outer CDATA", content)

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

    # def test_parse_dravid_response_with_nested_cdata(self):
    #     response = """
    #     <response>
    #       <explanation>Creating a file with nested CDATA</explanation>
    #       <steps>
    #         <step>
    #           <type>file</type>
    #           <operation>CREATE</operation>
    #           <filename>nested_cdata.txt</filename>
    #           <content>
    #             <![CDATA[
    #               Outer CDATA
    #               <![CDATA[
    #                 Inner CDATA
    #               ]]>
    #               Still outer CDATA
    #             ]]>
    #           </content>
    #         </step>
    #       </steps>
    #     </response>
    #     """
    #     result = parse_dravid_response(response)
    #     self.assertEqual(len(result), 2)  # Explanation + 1 step
    #     self.assertEqual(result[0]['type'], 'explanation')
    #     self.assertEqual(result[1]['type'], 'file')
    #     self.assertIn('Outer CDATA', result[1]['content'])
    #     self.assertIn('<![CDATA[', result[1]['content'])
    #     self.assertIn('Inner CDATA', result[1]['content'])
    #     self.assertIn(']]>', result[1]['content'])
    #     self.assertIn('Still outer CDATA', result[1]['content'])

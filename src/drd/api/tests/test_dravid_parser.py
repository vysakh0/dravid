import unittest
from src.drd.api.dravid_parser import extract_and_parse_xml, parse_dravid_response


class TestDravidParser(unittest.TestCase):

    def test_extract_and_parse_xml_valid(self):
        valid_xml = "<response><step><type>shell</type><command>echo 'Hello'</command></step></response>"
        root = extract_and_parse_xml(valid_xml)
        self.assertIsNotNone(root)
        self.assertEqual(root.tag, 'response')
        self.assertEqual(len(root.findall('.//step')), 1)

    def test_extract_and_parse_xml_invalid(self):
        invalid_xml = "<response><step><type>shell</type><command>echo 'Hello'</command></step>"
        with self.assertRaises(ValueError):
            extract_and_parse_xml(invalid_xml)

    def test_parse_dravid_response(self):
        response = """
        <response>
            <explanation>This is a test explanation</explanation>
            <steps>
                <step>
                    <type>shell</type>
                    <command>echo 'Hello, World!'</command>
                </step>
                <step>
                    <type>file</type>
                    <operation>CREATE</operation>
                    <filename>test.txt</filename>
                    <content>This is a test file</content>
                </step>
            </steps>
        </response>
        """
        commands = parse_dravid_response(response)
        self.assertEqual(len(commands), 3)  # Explanation + 2 steps
        self.assertEqual(commands[0]['type'], 'explanation')
        self.assertEqual(commands[1]['type'], 'shell')
        self.assertEqual(commands[2]['type'], 'file')


if __name__ == '__main__':
    unittest.main()

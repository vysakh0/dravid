import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import re


def extract_and_parse_xml(response: str) -> ET.Element:
    # Try to extract XML content
    xml_start = response.find('<response>')
    xml_end = response.rfind('</response>')
    if xml_start != -1 and xml_end != -1:
        # +11 to include '</response>'
        xml_content = response[xml_start:xml_end + 11]
    else:
        raise ValueError("No valid XML response found")

    # Parse the XML
    try:
        root = ET.fromstring(xml_content)
        return root
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        print("Original response:")
        print(response)

        # Attempt to identify the problematic part
        line_num, col_num = e.position
        lines = xml_content.split('\n')
        if line_num <= len(lines):
            problematic_line = lines[line_num - 1]
            print(f"Problematic line ({line_num}):")
            print(problematic_line)
            print(' ' * (col_num - 1) + '^')

            # Try to fix common issues
            fixed_line = re.sub(
                r'&(?!amp;|lt;|gt;|apos;|quot;)', '&amp;', problematic_line)
            if fixed_line != problematic_line:
                print("Attempting to fix the line:")
                print(fixed_line)
                lines[line_num - 1] = fixed_line
                fixed_xml = '\n'.join(lines)
                try:
                    return ET.fromstring(fixed_xml)
                except ET.ParseError:
                    print("Fix attempt failed.")

        raise


def parse_claude_response(response: str) -> List[Dict[str, Any]]:
    try:
        root = extract_and_parse_xml(response)
        commands = []
        explanation = root.find('explanation')
        if explanation is not None and explanation.text:
            commands.append({
                'type': 'explanation',
                'content': explanation.text.strip()
            })
        for step in root.findall('.//step'):
            command = {}
            for child in step:
                if child.tag == 'content':
                    command[child.tag] = child.text.strip(
                    ) if child.text else ''
                else:
                    command[child.tag] = child.text
            commands.append(command)
        return commands
    except Exception as e:
        print(f"Error parsing Claude response: {e}")
        print("Original response:")
        print(response)
        return []


def pretty_print_commands(commands: List[Dict[str, Any]]):
    for i, cmd in enumerate(commands, 1):
        print(f"Command {i}:")
        for key, value in cmd.items():
            if key == 'content' and len(value) > 100:
                print(f"  {key}: {value[:100]}... (truncated)")
            else:
                print(f"  {key}: {value}")
        print()

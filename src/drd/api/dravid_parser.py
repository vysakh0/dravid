import xml.etree.ElementTree as ET
from lxml import etree
from typing import List, Dict, Any
import re


def extract_outermost_xml(response: str) -> str:
    xml_start = response.find('<response>')
    xml_end = response.rfind('</response>')
    if xml_start != -1 and xml_end != -1:
        return response[xml_start:xml_end + 11]
    raise ValueError("No valid XML response found")


def escape_nested_cdata(xml_content: str) -> str:
    # Simplified function: just return the content as is
    return xml_content


def extract_and_parse_xml(response: str) -> etree.Element:
    try:
        xml_content = extract_outermost_xml(response)
        xml_content = escape_nested_cdata(xml_content)
        parser = etree.XMLParser(recover=True)
        return etree.fromstring(xml_content.encode('utf-8'), parser=parser)
    except etree.XMLSyntaxError as e:
        print(f"Error parsing XML: {e}")
        print("Original response:")
        print(response)
        print("Processed XML content:")
        print(xml_content)
        raise


def parse_dravid_response(response: str) -> List[Dict[str, Any]]:
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
        print(f"Error parsing dravid response: {e}")
        print("Original response:")
        print(response)
        return []

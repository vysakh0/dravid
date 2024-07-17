import xml.etree.ElementTree as ET
from lxml import etree
from typing import List, Dict, Any
import re
from .utils import print_error


def extract_outermost_xml(response: str) -> str:
    xml_start = response.find('<response>')
    xml_end = response.rfind('</response>')
    if xml_start != -1 and xml_end != -1:
        return response[xml_start:xml_end + 11]
    raise ValueError("No valid XML response found")


def extract_and_parse_xml(response: str) -> etree.Element:
    try:
        xml_content = extract_outermost_xml(response)
        parser = etree.XMLParser(recover=True, strip_cdata=False)
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

        # Extract explanation
        explanation = root.find('explanation')
        if explanation is not None and explanation.text:
            commands.append({
                'type': 'explanation',
                'content': explanation.text.strip()
            })

        # Extract steps
        for step in root.findall('.//step'):
            command = {}
            for tag in ['type', 'operation', 'filename', 'content', 'command']:
                element = step.find(tag)
                if element is not None:
                    if tag == 'content':
                        # Use tostring to preserve CDATA and nested elements
                        command[tag] = etree.tostring(
                            element, encoding='unicode', method='text').strip()
                    else:
                        command[tag] = element.text.strip(
                        ) if element.text else ''
            if command:
                commands.append(command)

        return commands
    except Exception as e:
        print_error(f"Error parsing dravid response: {e}")
        print("Original response:")
        print(response)
        return []


def parse_file_list_response(response: str):
    try:
        root = extract_and_parse_xml(response)
        files = root.findall('.//file')
        return [file.text.strip() for file in files if file.text]
    except Exception as e:
        print_error(f"Error parsing file list response: {e}")
        return None


def parse_find_file_response(response: str):
    try:
        root = extract_and_parse_xml(response)
        file_element = root.find('.//file')
        return file_element.text.strip() if file_element is not None and file_element.text else None
    except Exception as e:
        print_error(f"Error parsing dravid's response: {str(e)}")
        return None

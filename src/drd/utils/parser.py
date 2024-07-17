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


def parse_element_content(element: etree.Element) -> str:
    if element.text:
        content = element.text
    else:
        content = ''

    for child in element:
        if isinstance(child.tag, str):
            if child.tag == 'content':
                child_content = etree.tostring(
                    child, encoding='unicode', method='xml')
                # Extract content between <content> tags
                match = re.search(r'<content>(.*?)</content>',
                                  child_content, re.DOTALL)
                if match:
                    content += match.group(1).strip()
                else:
                    content += child_content
            else:
                content += etree.tostring(child,
                                          encoding='unicode', method='xml')
        elif child.tag is etree.CDATA:
            content += f'<![CDATA[{child.text}]]>'
        if child.tail:
            content += child.tail

    return content.strip()


def parse_dravid_response(response: str) -> List[Dict[str, Any]]:
    try:
        xml_content = extract_outermost_xml(response)
        commands = []

        # Extract explanation
        explanation_match = re.search(
            r'<explanation>(.*?)</explanation>', xml_content, re.DOTALL)
        if explanation_match:
            commands.append({
                'type': 'explanation',
                'content': explanation_match.group(1).strip()
            })

        # Extract steps
        steps = re.findall(r'<step>(.*?)</step>', xml_content, re.DOTALL)
        for step in steps:
            command = {}
            for tag in ['type', 'operation', 'filename', 'content', 'command']:
                match = re.search(f'<{tag}>(.*?)</{tag}>', step, re.DOTALL)
                if match:
                    content = match.group(1)
                    if tag == 'content':
                        # Preserve CDATA content without parsing
                        cdata_match = re.search(
                            r'<!\[CDATA\[(.*?)\]\]>', content, re.DOTALL)
                        if cdata_match:
                            content = f'<![CDATA[{cdata_match.group(1)}]]>'
                    command[tag] = content.strip()
            commands.append(command)

        return commands
    except Exception as e:
        print(f"Error parsing dravid response: {e}")
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

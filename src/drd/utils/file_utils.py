import os
from ..api import extract_and_parse_xml
from ..utils import print_error


def parse_file_list_response(response: str):
    try:
        root = extract_and_parse_xml(response)
        files = root.findall('.//file')
        return [file.text.strip() for file in files if file.text]
    except Exception as e:
        print_error(f"Error parsing file list response: {e}")
        return []


def get_file_content(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.read()
    return None


def parse_find_file_response(response: str):
    try:
        root = extract_and_parse_xml(response)
        suggested_file = root.find('.//file').text.strip()
        return suggested_file if suggested_file else None
    except Exception as e:
        print_error(f"Error parsing dravid's response: {str(e)}")
        return None

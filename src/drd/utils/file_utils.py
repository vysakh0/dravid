import os
from ..api import extract_and_parse_xml
from ..utils import print_error, print_info


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


def fetch_project_guidelines(project_dir):
    guidelines_path = os.path.join(project_dir, 'project_guidelines.txt')
    project_guidelines = ""
    if os.path.exists(guidelines_path):
        with open(guidelines_path, 'r') as guidelines_file:
            project_guidelines = guidelines_file.read()
        print_info("Project guidelines found and included in the context.")
    return project_guidelines

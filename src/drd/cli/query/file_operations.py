import os
from ...api import call_dravid_api_with_pagination, extract_and_parse_xml
from ...utils import print_error, print_info
from ...metadata.project_metadata import ProjectMetadataManager


def get_files_to_modify(query, project_context):
    file_query = f"""
{project_context}

User query: {query}

Based on the user's query and the project context, which files will need to be modified?
Please respond with a list of filenames in the following XML format:

<response>
  <files>
    <file>path/to/file1.ext</file>
    <file>path/to/file2.ext</file>
  </files>
</response>

Only include files that will need to be modified to fulfill the user's request.
"""
    response = call_dravid_api_with_pagination(
        file_query, include_context=True)
    return parse_file_list_response(response)


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


def find_file_with_dravid(filename, project_context, max_retries=2, current_retry=0):
    if os.path.exists(filename):
        return filename

    if current_retry >= max_retries:
        print_error(f"File not found after {max_retries} retries: {filename}")
        return None

    metadata_manager = ProjectMetadataManager(os.getcwd())
    project_metadata = metadata_manager.get_project_context()

    query = f"""
{project_context}

Project Metadata:
{project_metadata}

The file "{filename}" was not found. Based on the project context, metadata, and the filename, can you suggest the correct path or an alternative file that might contain the updated content?

Respond with an XML structure containing the suggested file path:

<response>
  <file>suggested/path/to/file.ext</file>
</response>

If you can't suggest an alternative, respond with an empty <file> tag.
"""

    response = call_dravid_api_with_pagination(query, include_context=True)

    try:
        root = extract_and_parse_xml(response)
        suggested_file = root.find('.//file').text.strip()
        if suggested_file:
            print_info(
                f"Dravid suggested an alternative file: {suggested_file}")
            return find_file_with_dravid(suggested_file, project_context, max_retries, current_retry + 1)
        else:
            print_error("Dravid couldn't suggest an alternative file.")
            return None
    except Exception as e:
        print_error(f"Error parsing dravid's response: {str(e)}")
        return None

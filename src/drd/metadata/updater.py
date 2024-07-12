import os
from ..api.dravid_api import call_dravid_api_with_pagination
from ..api.dravid_parser import extract_and_parse_xml
from .project_metadata import ProjectMetadataManager
from ..utils.utils import print_error, print_success, print_info
from ..utils import generate_description


def find_file_with_dravid(filename, project_context, max_retries=2, current_retry=0):
    if os.path.exists(filename):
        return filename

    if current_retry >= max_retries:
        print_error(f"File not found after {max_retries} retries: {filename}")
        return None

    query = f"""
{project_context}

The file "{filename}" was not found. Based on the project context and the filename, can you suggest the correct path or an alternative file that might contain the updated content?

Respond with an XML structure containing the suggested file path:

<response>
  <file>suggested/path/to/file.ext</file>
</response>

If you can't suggest an alternative, respond with an empty <file> tag.
"""

    response = call_dravid_api_with_pagination(query, include_context=True)

    try:
        root = extract_and_parse_xml(response)
        suggested_file = root.find('.//file').text
        if suggested_file and suggested_file.strip():
            print_info(
                f"Dravid suggested an alternative file: {suggested_file}")
            return find_file_with_dravid(suggested_file.strip(), project_context, max_retries, current_retry + 1)
        else:
            print_info("Dravid couldn't suggest an alternative file.")
            return None
    except Exception as e:
        print_error(f"Error parsing dravid's response: {str(e)}")
        return None


def update_metadata_with_dravid(meta_description, current_dir):
    print_info("Updating metadata based on the provided description...")
    metadata_manager = ProjectMetadataManager(current_dir)
    project_context = metadata_manager.get_project_context()

    files_query = f"""
{project_context}

User update description: {meta_description}

Based on the user's description and the project context, please identify which files need to have their metadata updated or removed.
Respond with an XML structure containing the files to update or remove:

<response>
  <files>
    <file>
      <path>path/to/file1.ext</path>
      <action>update</action>
    </file>
    <file>
      <path>path/to/file2.ext</path>
      <action>remove</action>
    </file>
    <!-- Add more file elements as needed -->
  </files>
</response>

Include files that need to be updated or removed based on the user's description.
"""

    files_response = call_dravid_api_with_pagination(
        files_query, include_context=True)

    try:
        root = extract_and_parse_xml(files_response)
        files_to_process = [
            {
                'path': file.find('path').text.strip(),
                'action': file.find('action').text.strip()
            }
            for file in root.findall('.//file')
        ]

        if not files_to_process:
            print_info("No files identified for metadata update or removal.")
            return

        print_info(
            f"Files identified for processing: {', '.join([f['path'] for f in files_to_process])}")

        for file_info in files_to_process:
            filename = file_info['path']
            action = file_info['action']

            if action == 'remove':
                metadata_manager.remove_file_metadata(filename)
                print_success(f"Removed metadata for file: {filename}")
                continue

            found_filename = find_file_with_dravid(filename, project_context)
            if not found_filename:
                continue

            try:
                with open(found_filename, 'r') as f:
                    content = f.read()

                metadata_query = f"""
{project_context}

File: {found_filename}
Content:
{content}

Based on the file content and the project context, please generate appropriate metadata for this file.
Respond with an XML structure containing the metadata:

<response>
  <metadata>
    <type>file_type</type>
    <description>Description of the file's contents or purpose</description>
  </metadata>
</response>
"""

                metadata_response = call_dravid_api_with_pagination(
                    metadata_query, include_context=True)
                metadata_root = extract_and_parse_xml(metadata_response)
                file_type = metadata_root.find('.//type').text.strip()
                description = metadata_root.find('.//description').text.strip()

                metadata_manager.update_file_metadata(
                    found_filename,
                    file_type,
                    content,
                    description
                )
                print_success(f"Updated metadata for file: {found_filename}")
            except Exception as e:
                print_error(f"Error processing {found_filename}: {str(e)}")

        print_success("Metadata update completed.")
    except Exception as e:
        print_error(f"Error parsing dravid's response: {str(e)}")

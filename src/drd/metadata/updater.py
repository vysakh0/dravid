import os
from ..api.dravid_api import call_dravid_api_with_pagination
from ..api.dravid_parser import extract_and_parse_xml
from .project_metadata import ProjectMetadataManager
from ..utils.utils import print_error, print_success, print_info
from .common_utils import get_ignore_patterns, get_folder_structure, generate_file_description


def find_file_with_dravid(filename, project_context, folder_structure, max_retries=2, current_retry=0):
    if os.path.exists(filename):
        return filename

    if current_retry >= max_retries:
        print_error(f"File not found after {max_retries} retries: {filename}")
        return None

    query = f"""
{project_context}

Current folder structure:
{folder_structure}

The file "{filename}" was not found. Based on the project context, folder structure, and the filename, can you suggest the correct path or an alternative file that might contain the updated content?

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
            return find_file_with_dravid(suggested_file.strip(), project_context, folder_structure, max_retries, current_retry + 1)
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

    ignore_patterns, ignore_message = get_ignore_patterns(current_dir)
    print_info(ignore_message)

    folder_structure = get_folder_structure(current_dir, ignore_patterns)
    print_info("Current folder structure:")
    print_info(folder_structure)

    files_query = f"""
Project context: {project_context}

Current folder structure:
{folder_structure}

User update description: {meta_description}

You're a project metadata (project context) maintainer, 
your job is to identify the relevant files for which the metadata needs to be updated or added or removed based on user update desc.

Based on the user's description, project context, and the current folder structure, please identify which files need to have their metadata updated or removed.
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

Respond strictly only with xml response as it will be used for parsing, no other extra words.
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

            found_filename = find_file_with_dravid(
                filename, project_context, folder_structure)
            if not found_filename:
                continue

            try:
                with open(found_filename, 'r') as f:
                    content = f.read()

                file_type, description = generate_file_description(
                    found_filename, content, project_context, folder_structure)

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

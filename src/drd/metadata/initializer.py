import os
import json
from datetime import datetime
from ..api.dravid_api import call_dravid_api_with_pagination
from ..api.dravid_parser import extract_and_parse_xml
from .project_metadata import ProjectMetadataManager
from ..utils.utils import print_error, print_success, print_info
from .common_utils import get_ignore_patterns, get_folder_structure, should_ignore, generate_file_description


def initialize_project_metadata(current_dir):
    print_info("Initializing project metadata...")

    ignore_patterns, ignore_message = get_ignore_patterns(current_dir)
    print_info(ignore_message)

    folder_structure = get_folder_structure(current_dir, ignore_patterns)
    print_info("The current folder structure:")
    print_info(folder_structure)
    query = f"""
Current folder structure:
{folder_structure}

Based on the folder structure, please analyze the project and provide the following information:
1. Project name
2. Main programming language(s) used
3. Framework(s) used (if any)
4. Recommended dev server start command (if applicable)
5. A brief description of the project

Respond with an XML structure containing this information:

<response>
  <project_info>
    <project_name>project_name</project_name>
    <dev_server>
      <start_command>start_command</start_command>
      <framework>framework_name</framework>
      <language>programming_language</language>
    </dev_server>
    <description>project_description</description>
  </project_info>
</response>
"""
    try:
        response = call_dravid_api_with_pagination(query, include_context=True)
        root = extract_and_parse_xml(response)
        project_info = root.find('.//project_info')

        if project_info is None:
            raise ValueError(
                "Failed to extract project information from dravid's response")

        metadata = {
            "project_name": project_info.find('project_name').text.strip(),
            "last_updated": datetime.now().isoformat(),
            "files": [],
            "dev_server": {
                "start_command": project_info.find('.//dev_server/start_command').text.strip(),
                "framework": project_info.find('.//dev_server/framework').text.strip(),
                "language": project_info.find('.//dev_server/language').text.strip()
            },
            "description": project_info.find('description').text.strip()
        }

        for root, dirs, files in os.walk(current_dir):
            dirs[:] = [d for d in dirs if not should_ignore(
                os.path.join(root, d), ignore_patterns)]
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, current_dir)

                if should_ignore(relative_path, ignore_patterns):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception as e:
                    content = f"Error reading file: {str(e)}"

                file_type, description = generate_file_description(
                    relative_path, content, json.dumps(metadata), folder_structure)

                file_metadata = {
                    "filename": relative_path,
                    "type": file_type,
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    "content_preview": content[:100].replace('\n', ' ') + ('...' if len(content) > 100 else ''),
                    "description": description
                }
                metadata["files"].append(file_metadata)

        metadata_manager = ProjectMetadataManager(current_dir)
        metadata_manager.metadata = metadata
        metadata_manager.save_metadata()

        print_success("Project metadata initialized successfully.")
        print_info("Generated metadata:")
        print(json.dumps(metadata, indent=2))

    except Exception as e:
        print_error(f"Error initializing project metadata: {str(e)}")
        print_error("Stack trace:")
        import traceback
        traceback.print_exc()

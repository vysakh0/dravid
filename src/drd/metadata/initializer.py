import os
import json
import asyncio
from datetime import datetime
from .project_metadata import ProjectMetadataManager
from ..utils.utils import print_info, print_success, print_error, print_warning
from ..utils.loader import Loader
from ..api.main import call_dravid_api_with_pagination
from ..utils.parser import extract_and_parse_xml
from ..prompts.get_project_info_prompts import get_project_info_prompt


async def initialize_project_metadata(project_dir):
    print_info("Initializing project metadata...")
    builder = ProjectMetadataManager(project_dir)

    # Get folder structure
    folder_structure = builder.get_directory_structure(project_dir)
    print_info("Current folder structure:")
    print_info(json.dumps(folder_structure, indent=2))

    # Get project info
    print_info("Fetching project information...")
    query = get_project_info_prompt(json.dumps(folder_structure, indent=2))
    loader = Loader("Analyzing project structure")
    loader.start()
    try:
        response = call_dravid_api_with_pagination(query, include_context=True)
        root = extract_and_parse_xml(response)
        project_info = root.find('.//project_info')
        if project_info is None:
            print_warning(
                "Could not extract project information from the API response. Using default values.")
        else:
            builder.metadata['project_info']['name'] = project_info.find('project_name').text.strip(
            ) if project_info.find('project_name') is not None else builder.metadata['project_info']['name']
            builder.metadata['project_info']['description'] = project_info.find('description').text.strip(
            ) if project_info.find('description') is not None else builder.metadata['project_info']['description']
            builder.metadata['environment']['primary_language'] = project_info.find(
                'primary_language').text.strip() if project_info.find('primary_language') is not None else ""
            builder.metadata['environment']['primary_framework'] = project_info.find(
                'primary_framework').text.strip() if project_info.find('primary_framework') is not None else ""
            dev_server = project_info.find('dev_server')
            if dev_server is not None and dev_server.find('start_command') is not None:
                builder.metadata['dev_server']['start_command'] = dev_server.find(
                    'start_command').text.strip()

            # Process inferred directory structure
            dir_structure = project_info.find('directory_structure')
            if dir_structure is not None:
                for dir_elem in dir_structure.findall('directory'):
                    dir_name = dir_elem.find('name').text.strip()
                    dir_desc = dir_elem.find('description').text.strip()
                    builder.metadata['directory_structure'][dir_name] = dir_desc

    except Exception as e:
        print_warning(f"Error fetching project information: {str(e)}")
        print_warning("Continuing with default values.")
    finally:
        loader.stop()

    # Build metadata
    print_info("Analyzing project files...")
    loader = Loader("Processing files")
    loader.start()
    try:
        metadata = await builder.build_metadata(loader)
    finally:
        loader.stop()

    # Save metadata to drd.json
    drd_path = os.path.join(project_dir, 'drd.json')
    with open(drd_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print_success(
        f"Project metadata initialized successfully. Saved to {drd_path}")
    print_info("Generated metadata:")
    print_info(json.dumps(metadata, indent=2))

    return metadata


def initialize_project_metadata_sync(current_dir):
    asyncio.run(initialize_project_metadata(current_dir))

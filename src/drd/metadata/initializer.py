import os
import json
from datetime import datetime
import asyncio
from ..api.main import call_dravid_api_with_pagination
from ..utils.parser import extract_and_parse_xml
from .project_metadata import ProjectMetadataManager
from ..utils.utils import print_error, print_success, print_info, print_warning
from ..utils.loader import run_with_loader, Loader
from .common_utils import get_ignore_patterns, get_folder_structure, should_ignore
from .rate_limit_handler import process_files
from ..prompts.get_project_info_prompts import get_project_info_prompt


async def initialize_project_metadata(current_dir):
    print_info("Initializing project metadata...")
    ignore_patterns, ignore_message = get_ignore_patterns(current_dir)
    print_info(ignore_message)

    folder_structure = get_folder_structure(current_dir, ignore_patterns)
    print_info("The current folder structure:")
    print_info(folder_structure)

    query = get_project_info_prompt(folder_structure)
    try:
        # Use run_with_loader to call the synchronous function
        response = run_with_loader(
            lambda: call_dravid_api_with_pagination(
                query, include_context=True),
            "Fetching project information"
        )
        root = extract_and_parse_xml(response)
        project_info = root.find('.//project_info')
        if project_info is None:
            raise ValueError(
                "Failed to extract project information from dravid's response")

        metadata = {
            "project_name": project_info.find('project_name').text.strip() if project_info.find('project_name') is not None else "Unknown Project",
            "last_updated": datetime.now().isoformat(),
            "files": [],
            "dev_server": {
                "start_command": project_info.find('.//dev_server/start_command').text.strip() if project_info.find('.//dev_server/start_command') is not None else "",
                "framework": project_info.find('.//dev_server/framework').text.strip() if project_info.find('.//dev_server/framework') is not None else "Unknown",
                "language": project_info.find('.//dev_server/language').text.strip() if project_info.find('.//dev_server/language') is not None else "Unknown"
            },
            "description": project_info.find('description').text.strip() if project_info.find('description') is not None else "No description available"
        }

        files_to_process = []
        total_files = sum([len(files) for _, _, files in os.walk(current_dir)])
        processed_files = 0

        loader = Loader("Reading files")
        loader.start()

        for root, dirs, files in os.walk(current_dir):
            dirs[:] = [d for d in dirs if not should_ignore(
                os.path.join(root, d), ignore_patterns)]
            for file in files:
                processed_files += 1
                loader.message = f"Reading files ({processed_files}/{total_files})"

                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, current_dir)
                if should_ignore(relative_path, ignore_patterns):
                    continue
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception as e:
                    content = f"Error reading file: {str(e)}"
                files_to_process.append((relative_path, content))

        loader.stop()
        print_success(f"Read {len(files_to_process)} files")

        # Process files asynchronously
        print_info("Processing file metadata...")
        processed_files = await process_files(files_to_process, json.dumps(metadata), folder_structure)

        for filename, file_type, description, exports in processed_files:
            file_path = os.path.join(current_dir, filename)
            try:
                content = next(content for name,
                               content in files_to_process if name == filename)
                content_preview = content[:100].replace(
                    '\n', ' ') + ('...' if len(content) > 100 else '')
            except StopIteration:
                print_warning(f"Could not find content for file: {filename}")
                content_preview = "Content not available"

            file_metadata = {
                "filename": filename,
                "type": file_type,
                "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "content_preview": content_preview,
                "description": description,
                "exports": exports
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


def initialize_project_metadata_sync(current_dir):
    asyncio.run(initialize_project_metadata(current_dir))

import asyncio
from ..api.dravid_api import call_dravid_api_with_pagination
from ..api.dravid_parser import extract_and_parse_xml
from ..prompts.file_metada_desc_prompts import get_file_metadata_prompt


async def process_single_file(filename, content, project_context, folder_structure):
    metadata_query = get_file_metadata_prompt(
        filename, content, project_context, folder_structure)
    try:
        response = call_dravid_api_with_pagination(
            metadata_query, include_context=True)
        root = extract_and_parse_xml(response)

        type_elem = root.find('.//type')
        desc_elem = root.find('.//description')
        exports_elem = root.find('.//exports')

        file_type = type_elem.text.strip(
        ) if type_elem is not None and type_elem.text else "unknown"
        description = desc_elem.text.strip(
        ) if desc_elem is not None and desc_elem.text else "No description available"
        exports = exports_elem.text.strip(
        ) if exports_elem is not None and exports_elem.text else ""

        return filename, file_type, description, exports
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return filename, "unknown", f"Error: {e}", ""


async def process_files(files, project_context, folder_structure):
    tasks = [process_single_file(filename, content, project_context, folder_structure)
             for filename, content in files]
    return await asyncio.gather(*tasks)

import os
import re
from ..api.main import call_dravid_api_with_pagination
from ..utils.parser import extract_and_parse_xml
from ..prompts.file_metada_desc_prompts import get_file_metadata_prompt
from ..prompts.metadata_update_prompts import get_file_suggestion_prompt
from ..utils import print_info, print_error


def parse_gitignore(gitignore_path):
    ignore_patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    pattern = line.replace('.', r'\.').replace(
                        '*', '.*').replace('?', '.')
                    if pattern.startswith('/'):
                        pattern = '^' + pattern[1:]
                    elif pattern.endswith('/'):
                        pattern += '.*'
                    else:
                        pattern = '.*' + pattern
                    try:
                        ignore_patterns.append(re.compile(pattern))
                        # Debug print
                        print(
                            f"ignoring file pattern part of gitignore: {pattern}")
                    except re.error as e:
                        # Debug print
                        print(f"Error compiling pattern '{pattern}': {e}")
    print(f"Total patterns: {len(ignore_patterns)}")  # Debug print
    return ignore_patterns


def should_ignore(path, ignore_patterns):
    return any(pattern.search(path) for pattern in ignore_patterns)


def get_folder_structure(start_path, ignore_patterns):
    structure = []
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * level
        folder_name = os.path.basename(root)
        rel_path = os.path.relpath(root, start_path)
        rel_path = '' if rel_path == '.' else rel_path
        if not should_ignore(rel_path, ignore_patterns):
            structure.append(f"{indent}{folder_name}/")
            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                file_path = os.path.join(rel_path, file)
                if not should_ignore(file_path, ignore_patterns):
                    structure.append(f"{sub_indent}{file}")
        dirs[:] = [d for d in dirs if not should_ignore(
            os.path.join(rel_path, d), ignore_patterns)]
    return '\n'.join(structure)


def get_ignore_patterns(current_dir):
    gitignore_path = os.path.join(current_dir, '.gitignore')
    if os.path.exists(gitignore_path):
        ignore_patterns = parse_gitignore(gitignore_path)
        ignore_patterns.append(re.compile('.git'))
        return ignore_patterns, "Using .gitignore patterns for file exclusion."
    else:
        default_patterns = ['node_modules', 'dist',
                            'build', 'venv', '.git', '__pycache__']
        ignore_patterns = [re.compile(f'.*{pattern}.*')
                           for pattern in default_patterns]
        return ignore_patterns, "No .gitignore found. Using default ignore patterns."


def generate_file_description(filename, content, project_context, folder_structure):
    metadata_query = get_file_metadata_prompt(
        filename, content, project_context, folder_structure)
    print_info(
        f"Getting description of {filename} to update metadata for future reference")
    print_info("LLM calls to be made: 1")
    response = call_dravid_api_with_pagination(
        metadata_query, include_context=True)
    try:
        root = extract_and_parse_xml(response)

        metadata = root.find('.//metadata')
        if metadata is None:
            raise ValueError("Metadata section not found in the response")

        type_element = metadata.find('type')
        description_element = metadata.find('description')
        exports_element = metadata.find('exports')

        file_type = type_element.text.strip(
        ) if type_element is not None and type_element.text else "unknown"
        description = description_element.text.strip(
        ) if description_element is not None and description_element.text else "No description available"
        exports = exports_element.text.strip(
        ) if exports_element is not None and exports_element.text else ""

        print_info(
            f"Generated metadata for {filename}: Type: {file_type}, Description: {description[:50]}..., Exports: {exports[:50]}...")
        return file_type, description, exports
    except Exception as e:
        print_error(f"Error parsing metadata response for {filename}: {e}")
        print_error(f"Raw response: {response}")
        return "unknown", f"Error generating description: {str(e)}", ""


def find_file_with_dravid(filename, project_context, folder_structure, max_retries=2, current_retry=0):
    if os.path.exists(filename):
        return filename

    if current_retry >= max_retries:
        print_error(f"File not found after {max_retries} retries: {filename}")
        return None

    query = get_file_suggestion_prompt(
        filename, project_context, folder_structure)
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

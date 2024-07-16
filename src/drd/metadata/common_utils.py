import os
import re
from ..api.dravid_api import call_dravid_api_with_pagination
from ..api.dravid_parser import extract_and_parse_xml
from ..prompts.file_metada_desc_prompts import get_file_metadata_prompt
from ..utils import print_info


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
                    ignore_patterns.append(re.compile(pattern))
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
        f"Get description.. of {filename} to update metadainfo for future reference")
    print_info("LLM calls to be made: 1")
    response = call_dravid_api_with_pagination(
        metadata_query, include_context=True)
    try:
        root = extract_and_parse_xml(response)
        file_type = root.find('.//type').text.strip()
        description = root.find('.//description').text.strip()
        return file_type, description
    except Exception as e:
        print(f"Error parsing metadata response: {e}")
        return "unknown", "Error generating description"

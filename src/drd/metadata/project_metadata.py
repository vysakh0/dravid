import os
import json
from datetime import datetime
import fnmatch
import xml.etree.ElementTree as ET
import mimetypes
from ..prompts.file_metada_desc_prompts import get_file_metadata_prompt
from ..api import call_dravid_api_with_pagination
from ..utils.utils import print_info, print_warning


class ProjectMetadataManager:
    def __init__(self, project_dir):
        self.project_dir = os.path.abspath(project_dir)
        self.metadata = {
            "project_info": {
                "name": os.path.basename(project_dir),
                "version": "1.0.0",
                "description": "",
                "last_updated": datetime.now().isoformat()
            },
            "environment": {
                "primary_language": "",
                "other_languages": [],
                "primary_framework": "",
                "runtime_version": ""
            },
            "directory_structure": {},
            "key_files": [],
            "external_dependencies": [],
            "dev_server": {
                "start_command": ""
            }
        }
        self.ignore_patterns = self.get_ignore_patterns()
        self.binary_extensions = {
            '.pyc', '.pyo', '.so', '.dll', '.exe', '.bin'}
        self.image_extensions = {'.jpg', '.jpeg',
                                 '.png', '.gif', '.bmp', '.svg', '.ico'}

    def get_ignore_patterns(self):
        patterns = [
            '**/.git/**', '**/node_modules/**', '**/dist/**', '**/build/**',
            '**/__pycache__/**', '**/.venv/**', '**/.idea/**', '**/.vscode/**'
        ]

        for root, _, files in os.walk(self.project_dir):
            if '.gitignore' in files:
                gitignore_path = os.path.join(root, '.gitignore')
                rel_root = os.path.relpath(root, self.project_dir)
                with open(gitignore_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if rel_root == '.':
                                patterns.append(line)
                            else:
                                patterns.append(os.path.join(rel_root, line))

        return patterns

    def should_ignore(self, path):
        try:
            path_str = str(path)
            abs_path = os.path.abspath(path_str)
            rel_path = os.path.relpath(abs_path, self.project_dir)

            if rel_path.startswith('..'):
                return True

            return any(fnmatch.fnmatch(rel_path, pattern) for pattern in self.ignore_patterns)
        except Exception as e:
            print_warning(f"Error in should_ignore for path {path}: {str(e)}")
            return True

    def get_directory_structure(self, start_path):
        structure = {}
        for root, dirs, files in os.walk(start_path):
            if self.should_ignore(root):
                continue
            path = os.path.relpath(root, start_path)
            if path == '.':
                structure['files'] = [
                    f for f in files if not self.should_ignore(os.path.join(root, f))]
                structure['directories'] = []
            else:
                parts = path.split(os.sep)
                current = structure
                for part in parts[:-1]:
                    if 'directories' not in current:
                        current['directories'] = []
                    if part not in current['directories']:
                        current['directories'].append(part)
                    current = current.setdefault(part, {})
                if parts[-1] not in current:
                    current['directories'] = current.get('directories', [])
                    current['directories'].append(parts[-1])
                    current[parts[-1]] = {
                        'files': [f for f in files if not self.should_ignore(os.path.join(root, f))]}
        return structure

    def is_binary_file(self, file_path):
        _, extension = os.path.splitext(file_path)
        if extension.lower() in self.binary_extensions or extension.lower() in self.image_extensions:
            return True

        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type and not mime_type.startswith('text') and not mime_type.endswith('json')

    async def analyze_file(self, file_path):
        rel_path = os.path.relpath(file_path, self.project_dir)

        if self.is_binary_file(file_path):
            file_info = {
                "path": rel_path,
                "type": "binary",
                "summary": "Binary or non-text file",
                "exports": [],
                "imports": []
            }
        else:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                if file_path.endswith('.md'):
                    return None  # Skip markdown files

                prompt = get_file_metadata_prompt(rel_path, content, json.dumps(
                    self.metadata), json.dumps(self.metadata['directory_structure']))
                response = call_dravid_api_with_pagination(
                    prompt, include_context=True)

                root = ET.fromstring(response)
                metadata = root.find('metadata')

                file_info = {
                    "path": rel_path,
                    "type": metadata.find('type').text,
                    "summary": metadata.find('description').text,
                    "exports": metadata.find('exports').text.split(',') if metadata.find('exports').text != 'None' else [],
                    "imports": metadata.find('imports').text.split(',') if metadata.find('imports').text != 'None' else []
                }

                dependencies = metadata.find('external_dependencies')
                if dependencies is not None:
                    for dep in dependencies.findall('dependency'):
                        self.metadata['external_dependencies'].append({
                            "name": dep.find('name').text,
                            "version": dep.find('version').text,
                            "type": dep.find('type').text
                        })

                if rel_path == 'package.json':
                    self.analyze_package_json(content)

            except Exception as e:
                print_warning(f"Error analyzing file {file_path}: {str(e)}")
                file_info = {
                    "path": rel_path,
                    "type": "unknown",
                    "summary": "Error occurred during analysis",
                    "exports": [],
                    "imports": []
                }

        return file_info

    def analyze_package_json(self, content):
        try:
            package_data = json.loads(content)
            self.metadata['project_info']['name'] = package_data.get(
                'name', self.metadata['project_info']['name'])
            self.metadata['project_info']['version'] = package_data.get(
                'version', self.metadata['project_info']['version'])
            self.metadata['project_info']['description'] = package_data.get(
                'description', self.metadata['project_info']['description'])

            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})

            for name, version in {**dependencies, **dev_dependencies}.items():
                self.metadata['external_dependencies'].append({
                    "name": name,
                    "version": version,
                    "type": "npm"
                })

            if 'react' in dependencies:
                self.metadata['environment']['primary_framework'] = 'React'
            if 'next' in dependencies:
                self.metadata['environment']['primary_framework'] = 'Next.js'

            scripts = package_data.get('scripts', {})
            if 'dev' in scripts:
                self.metadata['dev_server']['start_command'] = f"npm run {scripts['dev']}"
            elif 'start' in scripts:
                self.metadata['dev_server']['start_command'] = f"npm run {scripts['start']}"

        except json.JSONDecodeError:
            print_warning("Error parsing package.json")

    async def build_metadata(self, loader):
        self.metadata['directory_structure'] = self.get_directory_structure(
            self.project_dir)

        total_files = sum([len(files) for root, _, files in os.walk(
            self.project_dir) if not self.should_ignore(root)])
        processed_files = 0

        for root, _, files in os.walk(self.project_dir):
            if self.should_ignore(root):
                continue
            for file in files:
                file_path = os.path.join(root, file)
                if not self.should_ignore(file_path):
                    file_info = await self.analyze_file(file_path)
                    if file_info:
                        self.metadata['key_files'].append(file_info)
                    processed_files += 1
                    loader.message = f"Analyzing files ({processed_files}/{total_files})"

        # Determine languages
        all_languages = set(file['type'] for file in self.metadata['key_files']
                            if file['type'] not in ['binary', 'unknown'])
        if all_languages:
            self.metadata['environment']['primary_language'] = max(all_languages, key=lambda x: sum(
                1 for file in self.metadata['key_files'] if file['type'] == x))
            self.metadata['environment']['other_languages'] = list(
                all_languages - {self.metadata['environment']['primary_language']})

        self.metadata['project_info']['last_updated'] = datetime.now().isoformat()

        return self.metadata

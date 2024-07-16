import json
import os
from datetime import datetime


class ProjectMetadataManager:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.metadata_file = os.path.join(self.project_dir, 'drd.json')
        self.metadata = self.load_metadata()

    def load_metadata(self):
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            "project_name": os.path.basename(self.project_dir),
            "last_updated": "",
            "files": [],
            "dev_server": {
                "start_command": "",
                "framework": "",
                "language": ""
            }
        }

    def save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def update_file_metadata(self, filename, file_type, content, description=None, exports=None):
        self.metadata['last_updated'] = datetime.now().isoformat()
        file_entry = next(
            (f for f in self.metadata['files'] if f['filename'] == filename), None)
        if file_entry is None:
            file_entry = {'filename': filename}
            self.metadata['files'].append(file_entry)
        file_entry.update({
            'type': file_type,
            'last_modified': datetime.now().isoformat(),
            'content_preview': content[:100] + ('...' if len(content) > 100 else ''),
            'description': description or file_entry.get('description', ''),
            'exports': exports
        })
        self.save_metadata()

    def remove_file_metadata(self, filename):
        self.metadata['last_updated'] = datetime.now().isoformat()
        self.metadata['files'] = [
            f for f in self.metadata['files'] if f['filename'] != filename]
        self.save_metadata()

    def get_file_metadata(self, filename):
        return next((f for f in self.metadata['files'] if f['filename'] == filename), None)

    def get_project_context(self):
        return json.dumps(self.metadata, indent=2)

    def update_dev_server_info(self, start_command, framework, language):
        self.metadata['dev_server'] = {
            "start_command": start_command,
            "framework": framework,
            "language": language
        }
        self.save_metadata()

    def get_dev_server_info(self):
        return self.metadata['dev_server']

    def update_metadata_from_file(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                content = f.read()
            file_type = filename.split('.')[-1]
            self.update_file_metadata(filename, file_type, content)
            return True
        return False

import os
import json
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
            "project_name": "",
            "last_updated": "",
            "files": [],
            "dev_server": {
                "start_command": "",
                "framework": "",
                "language": ""
            }
        }

    def get_project_context(self):
        if not os.path.exists(self.metadata_file):
            return None
        return json.dumps(self.metadata, indent=2)

    def update_file_metadata(self, filename, file_type, content, description=None, exports=None):
        self.metadata['last_updated'] = datetime.now().isoformat()
        file_entry = next(
            (f for f in self.metadata['files'] if f['filename'] == filename), None)
        if file_entry is None:
            file_entry = {"filename": filename}
            self.metadata['files'].append(file_entry)
        file_entry.update({
            "type": file_type,
            "content_preview": content[:100],
            "description": description,
            "exports": exports
        })
        self.save_metadata()

    def update_dev_server_info(self, start_command, framework, language):
        self.metadata['dev_server'] = {
            "start_command": start_command,
            "framework": framework,
            "language": language
        }
        self.save_metadata()

    def get_dev_server_info(self):
        return self.metadata['dev_server']

    def save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def update_metadata_from_file(self):
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                new_metadata = json.load(f)
            self.metadata.update(new_metadata)
            return True
        return False

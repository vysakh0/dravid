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
        return {"project_name": os.path.basename(self.project_dir), "last_updated": "", "files": []}

    def save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def update_file_metadata(self, filename, file_type, content, description=None):
        self.metadata['last_updated'] = datetime.now().isoformat()

        # Create or update file entry
        file_entry = next(
            (f for f in self.metadata['files'] if f['filename'] == filename), None)
        if file_entry is None:
            file_entry = {'filename': filename}
            self.metadata['files'].append(file_entry)

        file_entry.update({
            'type': file_type,
            'last_modified': datetime.now().isoformat(),
            'content_preview': content[:100] + ('...' if len(content) > 100 else ''),
            'description': description or file_entry.get('description', '')
        })

        self.save_metadata()

    def get_file_metadata(self, filename):
        return next((f for f in self.metadata['files'] if f['filename'] == filename), None)

    def get_project_context(self):
        return json.dumps(self.metadata, indent=2)

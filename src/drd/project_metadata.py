import json
import os
from datetime import datetime


class ProjectMetadataManager:
    def __init__(self, project_dir=None):
        self.project_dir = project_dir or os.getcwd()
        self.metadata_file = self._find_or_create_metadata_file()

    def _find_or_create_metadata_file(self):
        # Always use drd.json in the project directory
        return os.path.join(self.project_dir, 'drd.json')

    def load_metadata(self):
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {"project_name": os.path.basename(self.project_dir), "last_updated": "", "files": []}

    def save_metadata(self, metadata):
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def update_file_metadata(self, filename, file_type, content, description=None):
        metadata = self.load_metadata()
        metadata['last_updated'] = datetime.now().isoformat()

        # Create or update file entry
        file_entry = next(
            (f for f in metadata['files'] if f['filename'] == filename), None)
        if file_entry is None:
            file_entry = {'filename': filename}
            metadata['files'].append(file_entry)

        file_entry.update({
            'type': file_type,
            'last_modified': datetime.now().isoformat(),
            'content_preview': content[:100] + ('...' if len(content) > 100 else ''),
            'description': description or file_entry.get('description', '')
        })

        self.save_metadata(metadata)

    def get_file_metadata(self, filename):
        metadata = self.load_metadata()
        return next((f for f in metadata['files'] if f['filename'] == filename), None)

    def get_project_context(self):
        metadata = self.load_metadata()
        return json.dumps(metadata, indent=2)


def get_project_context():
    # This function is kept for backwards compatibility
    return ProjectMetadataManager().get_project_context()

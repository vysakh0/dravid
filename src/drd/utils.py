import json
import os

METADATA_FILE = 'project_metadata.json'


def get_project_context():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
        return json.dumps(metadata, indent=2)
    return "{}"

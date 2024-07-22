import os
import base64
import mimetypes
from .utils import print_info


def clean_path(path):
    path = path.strip("'\"")
    path = path.replace("\\ ", " ")
    return os.path.normpath(path)


def get_file_content(fname):
    filename = clean_path(fname)
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            lines = f.readlines()
            numbered_lines = [
                f"{i+1}:{line.rstrip()}" for i, line in enumerate(lines)]
            return "\n".join(numbered_lines)
    return None


def fetch_project_guidelines(project_dir):
    guidelines_path = os.path.join(project_dir, 'project_guidelines.txt')
    project_guidelines = ""
    if os.path.exists(guidelines_path):
        with open(guidelines_path, 'r') as guidelines_file:
            project_guidelines = guidelines_file.read()
        print_info("Project guidelines found and included in the context.")
    return project_guidelines


def is_directory_empty(path):
    return len(os.listdir(path)) == 0


def convert_to_base64(img_path):
    image_path = clean_path(img_path)
    mime_type, _ = mimetypes.guess_type(image_path)
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        return mime_type, image_data

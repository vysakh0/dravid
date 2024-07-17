def get_file_identification_prompt():
    return """You are a file identification assistant. Based on the user's query and the project context, 
identify which file the user is likely referring to. If no existing file seems relevant, suggest a new file name. 
Respond with a JSON object containing the 'filename' and a boolean 'exists' indicating if it's an existing file.
Do not respond anything other than the json. No extra text except the json.
"""


def get_file_description_prompt():
    return """You are a file description assistant. Based on the file content provided, 
generate a brief, informative description of the file in 100 characters or less. Just strictly description alone, no other text"""


def get_files_to_modify_prompt(query, project_context):
    return f"""
{project_context}
User query: {query}
Based on the user's query and the project context, which files will need to be modified?
Please respond with a list of filenames in the following XML format:
<response>
  <files>
    <file>path/to/file1.ext</file>
    <file>path/to/file2.ext</file>
  </files>
</response>
Only include files that will need to be modified to fulfill the user's request.
"""


def find_file_prompt(filename, project_context, project_metadata):
    return f"""
{project_context}
Project Metadata:
{project_metadata}
The file "{filename}" was not found. Based on the project context, metadata, and the filename, can you suggest the correct path or an alternative file that might contain the updated content?
Respond with an XML structure containing the suggested file path:
<response>
  <file>suggested/path/to/file.ext</file>
</response>
If you can't suggest an alternative, respond with empty <file> tag.
"""

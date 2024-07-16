def get_file_metadata_prompt(filename, content, project_context, folder_structure):
    return f"""
{project_context}
Current folder structure:
{folder_structure}
File: {filename}
Content:
{content}
You're the project context maintainer, your role is to keep relevant meta info about the entire project 
so it can be used by an AI coding assistant in future for reference.
Now based on the file content, project context, and the current folder structure, 
please generate appropriate metadata for this file. 
The exports refer to the available functions or variables in the content that is available for importing,
depending on language please include only functions or variables that are available for importing.
Respond with an XML structure containing the metadata
<response>
  <metadata>
    <type>file_type</type>
    <description>Description based on the file's contents, project context, folder structure for </description>
    <exports>fun:getProject,fun:setValue,var:API_KEY</exports>
  </metadata>
</response>
Respond strictly only with xml response as it will be used for parsing, no other extra words. 
If there are no exports, use <exports>None</exports> instead of an empty tag.
Ensure that all tags (type, description, exports) are always present and non-empty.
"""

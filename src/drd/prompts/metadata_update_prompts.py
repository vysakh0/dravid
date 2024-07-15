# File: prompts/metadata_update_prompts.py

def get_file_suggestion_prompt(filename, project_context, folder_structure):
    return f"""
{project_context}

Current folder structure:
{folder_structure}

The file "{filename}" was not found. Based on the project context, folder structure, and the filename, can you suggest the correct path or an alternative file that might contain the updated content?

Respond with an XML structure containing the suggested file path:

<response>
  <file>suggested/path/to/file.ext</file>
</response>

If you can't suggest an alternative, respond with an empty <file> tag.
"""


def get_files_to_update_prompt(project_context, folder_structure, meta_description):
    return f"""
Project context: {project_context}

Current folder structure:
{folder_structure}

User update description: {meta_description}

You're a project metadata (project context) maintainer, 
your job is to identify the relevant files for which the metadata needs to be updated or added or removed based on user update desc.

Based on the user's description, project context, and the current folder structure, please identify which files need to have their metadata updated or removed.
Respond with an XML structure containing the files to update or remove:

<response>
  <files>
    <file>
      <path>path/to/file1.ext</path>
      <action>update</action>
    </file>
    <file>
      <path>path/to/file2.ext</path>
      <action>remove</action>
    </file>
    <!-- Add more file elements as needed -->
  </files>
</response>

Respond strictly only with xml response as it will be used for parsing, no other extra words.
"""

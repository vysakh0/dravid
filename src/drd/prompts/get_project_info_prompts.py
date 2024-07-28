def get_project_info_prompt(folder_structure):
    return f"""
Analyze the following folder structure and provide information about the project:

{folder_structure}

Based on this structure, please provide the following information:
1. Project name
2. Primary programming language used
3. Primary framework used (if any)
4. Recommended dev server start command (if applicable)
5. A brief description of the project
6. Inferred high-level directory structure with brief descriptions for main directories

Respond with an XML structure of this pattern:

<response>
  <project_info>
    <project_name>project_name_here</project_name>
    <primary_language>primary_language_here</primary_language>
    <primary_framework>primary_framework_here</primary_framework>
    <dev_server>
      <start_command>start_command_here</start_command>
    </dev_server>
    <description>brief_description_here</description>
    <directory_structure>
      <directory>
        <name>directory_name_here</name>
        <description>brief_description_of_directory_contents</description>
      </directory>
      <!-- Repeat for each main directory -->
    </directory_structure>
  </project_info>
</response>

Ensure all tags are present, even if you're unsure about some information (use 'unknown' in those cases).
For the directory structure, focus on main directories and provide brief descriptions of their likely contents based on common project structures.
"""

def get_project_info_prompt(folder_structure):
    return f"""
Current folder structure:
{folder_structure}

Based on the folder structure, please analyze the project and provide the following information:
1. Project name
2. Main programming language(s) used
3. Framework(s) used (if any)
4. Recommended dev server start command (if applicable)
5. A brief description of the project

Respond with an XML structure containing this information:

<response>
  <project_info>
    <project_name>project_name</project_name>
    <dev_server>
      <start_command>start_command</start_command>
      <framework>framework_name</framework>
      <language>programming_language</language>
    </dev_server>
    <description>project_description</description>
  </project_info>
</response>
"""

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

Respond with an XML structure of this patern:

<response>
  <project_info>
    <project_name>myproject</project_name>
    <dev_server>
      <start_command>npm run dev</start_command>
      <framework>nextjs</framework>
      <language>javascript</language>
    </dev_server>
    <description>an e-commerce website</description>
  </project_info>
</response>
"""

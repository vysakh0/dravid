def get_file_metadata_prompt(filename, content, project_context, folder_structure):
    return f"""
{project_context}
Current folder structure:
{folder_structure}
File: {filename}
Content:
{content}

You're the project context maintainer. Your role is to keep relevant meta info about the entire project 
so it can be used by an AI coding assistant in future for reference.

Based on the file content, project context, and the current folder structure, 
please generate appropriate metadata for this file

Guidelines:
1. 'path' should be the full path of the file within the project.
2. 'type' should be the programming language or file type (e.g., "typescript", "python", "json").
3. 'summary' should be a concise description of the file's main purpose.
4. 'exports' should list the exported items with their types (fun: for functions, class: for classes, var: for variables etc).
5. 'imports' should list imports from other project files, including the path and imported item.
6. 'external_dependencies' should list external dependencies for dependency management files if the current file appears to
be deps management file (package.json, requirements.txt, Cargo.toml etc).
7. If there are no exports, imports, or external dependencies, use an empty array [].
8. Ensure all fields are present in the JSON object.
9. If there are no exports, use <exports>None</exports> instead of an empty tag.
10. If there are no imports, use <imports>None</imports> instead of an empty tag.
11. If there are no external dependencies, omit the <external_dependencies> tag entirely.
12. Ensure that all other tags (type, description, file_category, exports, imports) are always present and non-empty.


Respond with an XML structure containing the metadata:

<response>
  <metadata>
    <type>file_type</type>
    <summary>summary based on the file's contents, project context, and folder structure</summary>
    <exports>fun:functionName,class:ClassName,var:variableName</exports>
    <imports>path/to/file</imports>
    <external_dependencies>
      <dependency>
        <dependency>name1@version1</dependency>
        <dependency>name2@version2</dependency>
    </external_dependencies>
  </metadata>
</response>

examples:
<response>
  <metadata>
    <path>src/components/Layout.tsx</path>
    <type>typescript</type>
    <summary>Main layout component</summary>
    <exports>fun:Layout</exports>
    <imports>src/components/Footer</imports>
  </metadata>
</response>

<response>
  <metadata>
    <path>package.json</path>
    <type>json</type>
    <summary>Node.js project configuration and dependencies</summary>
    <exports>None</exports>
    <imports>None</imports>
    <external_dependencies>
      <dependency>react@18.2.0</dependency>
      <dependency>next@13.4.1</dependency>
      <dependency>typescript@5.0.4</dependency>
    </external_dependencies>
  </metadata>
</response>

Respond strictly only with the XML response as it will be used for parsing, no other extra words. 
"""

import traceback
import click
from ..utils.api_utils import call_dravid_api_with_pagination
from ..api.dravid_parser import parse_dravid_response, extract_and_parse_xml, pretty_print_commands
from ..utils import print_error, print_success, print_info
from ..metadata.common_utils import generate_file_description
import xml.etree.ElementTree as ET


def handle_error_with_dravid(error, cmd, executor, metadata_manager, depth=0, previous_context=""):
    if depth > 3:
        print_error(
            "Max error handling depth reached. Unable to resolve the issue.")
        return False

    print_error(f"Error executing command: {error}")

    # Capture the full error message and traceback
    error_message = str(error)
    error_type = type(error).__name__
    error_trace = ''.join(traceback.format_exception(
        type(error), error, error.__traceback__))

    project_context = metadata_manager.get_project_context()
    error_query = f"""
# Error Context
Previous context: {previous_context}

An error occurred while executing the following command:
{cmd['type']}: {cmd.get('command') or cmd.get('filename')}

Error type: {error_type}
Error message: {error_message}

Error trace:
{error_trace}

Project context:
{project_context}

# Instructions for dravid: Error Resolution Assistant
Analyze the error above and provide steps to fix it. 
Your response should be in strictly XML format with no other extra messages. Use the following format:
<response>
<explanation>A brief explanation of the steps, if necessary</explanation>
<steps>
    <step>
    <type>shell</type>
    <command>command to execute</command>
    </step>
    <step>
    <type>file</type>
    <operation>CREATE</operation>
    <filename>path/to/file.ext</filename>
    <content>
        <![CDATA[
        file content here
        ]]>
    </content>
    </step>
    <step>
    <type>file</type>
    <operation>UPDATE</operation>
    <filename>path/to/existing/file.ext</filename>
    <content>
        <![CDATA[
        content to append or replace
        ]]>
    </content>
    </step>
    <step>
    <type>file</type>
    <operation>DELETE</operation>
    <filename>path/to/file/to/delete.ext</filename>
    </step>
</steps>
</response>

Important guidelines:
1. If the error is coz of current directory having some files, please give notice to the user to create a fresh
project and try again, may be you can generate a "echo 'you have existing files in your project, please try in a new folder'"
equivalent shell script alone.
2. Include non-interactive flags for commands that might prompt for user input.
3. Use relative paths for all file operations.
4. Do not use 'cd' commands. All operations should be relative to the current directory.
5. If a command fails due to existing files, provide alternative steps to handle the situation (e.g., suggesting file removal or using a different directory).
6. Strictly generate XML only, no other extra words.
7. For file updates, especially configuration files like package.json, always provide the ENTIRE file content within the CDATA section.
8. If you need to update a specific part of a file, first fetch the current content, then provide the fully updated content.
9. Try to avoid sudo approach as much but as a last resort.
10. Give OS & arch specific information whenever needed.
11. When initializing a project, include a step to update the dev server info in the project metadata.
12. If a file is created or updated, include a step to update the file metadata in the project metadata.
Ensure all steps are executable and maintain a logical flow of operations.
13. When provided with an image, analyze its content and incorporate relevant information into your project setup instructions. This may include:
   - Identifying the programming language or framework shown in the image
   - Recognizing file structures or code snippets that need to be implemented
   - Detecting any specific libraries or dependencies that should be included
   - Inferring project requirements or features based on visual elements in the image
14. If there is a need to create a .png or .jpg files with no content, you can prefix the filename with "placeholder-"
15. Create reusable functions or components as much as possible in separate files so to avoid large lined files.
16. Always give full file response, never say code unchanged or partial responses. 
17. If you see an opportunity to reuse a code by extracting into a function or variable, please do.
18. Strive to create less 120 lines of code in a file, feel free to split and create new files to reference. This makes it
easy for coding assistants to load only needed context
19. Since you will be run as a program things like `source ~/.zshrc` script won't work, so after you suggest 
an export like 
 echo 'export PATH="/usr/local/opt/maven/bin:$PATH"' >> ~/.zshrc
don't try to suggest the command: `source ~/.zshrc`, instead suggest a shell command to export that env in the current terminal
like
export PATH="/usr/local/opt/maven/bin:$PATH

20. Do not attempt to delete any files outside the current directory like ~/.zshrc or others. 
21. Never run destructive commands like `rm -rf`. NEVER.
For eg, if there is an existing project and the new project can't be initialised
or when some file conflicts for shell command to succeed then suggest a shell script like 
"echo 'create a new directory and try again'"
22. When suggesting a installation script for language related installation, prefer version manager.
For eg, if you need to install python, use something like pyenv and related steps.
"""

    print_info("Sending error information to dravid for analysis...")
    response = call_dravid_api_with_pagination(
        error_query, include_context=True)

    try:
        # Use the existing extract_and_parse_xml function for better error handling
        root = extract_and_parse_xml(response)
        # Use the existing parse_dravid_response function
        fix_commands = parse_dravid_response(response)
    except ValueError as e:
        print_error(f"Error parsing dravid's response: {str(e)}")
        return False

    print_info("dravid's suggested fix:")
    pretty_print_commands(fix_commands)
    print_info("Applying dravid's suggested fix...")
    fix_applied, step_completed, error_message, all_outputs = apply_fix_commands(
        fix_commands, executor, metadata_manager)

    if fix_applied:
        print_success("All fix steps successfully applied.")
        print_info("Fix application details:")
        click.echo(all_outputs)
        return True
    else:
        print_error(f"Failed to apply the fix at step {step_completed}.")
        print_error(f"Error message: {error_message}")
        print_info("Fix application details:")
        click.echo(all_outputs)

        # Recursively try to fix the error in applying the fix
        return handle_error_with_dravid(Exception(error_message),
                                        {"type": "fix",
                                            "command": f"apply fix step {step_completed}"},
                                        executor, metadata_manager, depth + 1, all_outputs)


def apply_fix_commands(fix_commands, executor, metadata_manager):
    all_outputs = []
    total_steps = len(fix_commands)

    for i, cmd in enumerate(fix_commands, 1):
        if cmd['type'] == 'explanation':
            print_info(
                f"Step {i}/{total_steps}: Explanation: {cmd['content']}")
            all_outputs.append(
                f"Step {i}/{total_steps}: Explanation - {cmd['content']}")
            continue

        if cmd['type'] == 'shell':
            print_info(
                f"Step {i}/{total_steps}: Running the fix: {cmd['command']}")
            try:
                output = executor.execute_shell_command(cmd['command'])
                if output is None:
                    raise Exception(f"Command failed: {cmd['command']}")
                print_success(
                    f"Step {i}/{total_steps}: Successfully executed: {cmd['command']}")
                if output:
                    click.echo(f"Command output:\n{output}")
                all_outputs.append(
                    f"Step {i}/{total_steps}: Shell command - {cmd['command']}\nOutput: {output}")
            except Exception as e:
                error_message = f"Step {i}/{total_steps}: Error executing fix command: {cmd['command']}\nError details: {str(e)}"
                print_error(error_message)
                all_outputs.append(error_message)
                return False, i, str(e), "\n".join(all_outputs)
        elif cmd['type'] == 'file':
            print_info(
                f"Step {i}/{total_steps}: Performing file operation: {cmd['operation']} on {cmd['filename']}")
            try:
                operation_performed = executor.perform_file_operation(
                    cmd['operation'],
                    cmd['filename'],
                    cmd.get('content'),
                    force=True
                )
                if operation_performed:
                    print_success(
                        f"Step {i}/{total_steps}: Successfully performed {cmd['operation']} on file: {cmd['filename']}")
                    all_outputs.append(
                        f"Step {i}/{total_steps}: File operation - {cmd['operation']} - {cmd['filename']} - Success")

                    # Update metadata for CREATE and UPDATE operations
                    if cmd['operation'] in ['CREATE', 'UPDATE']:
                        project_context = metadata_manager.get_project_context()
                        folder_structure = executor.get_folder_structure()
                        file_type, description = generate_file_description(
                            cmd['filename'],
                            cmd.get('content', ''),
                            project_context,
                            folder_structure
                        )
                        metadata_manager.update_file_metadata(
                            cmd['filename'],
                            file_type,
                            cmd.get('content', ''),
                            description
                        )
                else:
                    raise Exception(
                        f"File operation failed: {cmd['operation']} on {cmd['filename']}")
            except Exception as e:
                error_message = f"Step {i}/{total_steps}: Error performing file operation: {cmd['operation']} on {cmd['filename']}\nError details: {str(e)}"
                print_error(error_message)
                all_outputs.append(error_message)
                return False, i, str(e), "\n".join(all_outputs)
    return True, total_steps, None, "\n".join(all_outputs)

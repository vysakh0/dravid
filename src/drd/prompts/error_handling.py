import traceback
import click
from ..utils.api_utils import call_dravid_api_with_pagination
from ..api.dravid_parser import parse_dravid_response, extract_and_parse_xml, pretty_print_commands
from ..utils import print_error, print_success, print_info, generate_description
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
                        description = generate_description(
                            cmd['filename'], cmd.get('content', ''))
                        metadata_manager.update_file_metadata(
                            cmd['filename'],
                            cmd['filename'].split('.')[-1],
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

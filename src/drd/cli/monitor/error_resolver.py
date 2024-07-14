import traceback
from ...api.dravid_api import call_dravid_api_with_pagination
from ...api.dravid_parser import parse_dravid_response, pretty_print_commands
from ...utils.step_executor import Executor
from ...utils.utils import print_error, print_success, print_info


def monitoring_handle_error_with_dravid(error, line, monitor):
    print_error(f"Error detected: {error}")

    error_message = str(error)
    error_type = type(error).__name__
    error_trace = ''.join(traceback.format_exception(
        type(error), error, error.__traceback__))
    project_context = monitor.metadata_manager.get_project_context()

    error_query = f"""
    # Error Context
    An error occurred while running the server:

    Error type: {error_type}
    Error message: {error_message}

    Error trace:
    {error_trace}

    Relevant output line:
    {line}

    Project context:
    {project_context}

    # Instructions for dravid: Error Resolution Assistant
    Analyze the error above and provide steps to fix it.
    This is being run in a monitoring thread, so don't suggest server starting commands like npm run dev.
    When there is file content to be shown, make sure to give full content don't say "rest of the thing remain same".
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

    print_info("Sending error information to Dravid for analysis...")
    response = call_dravid_api_with_pagination(
        error_query, include_context=True)

    try:
        fix_commands = parse_dravid_response(response)
    except ValueError as e:
        print_error(f"Error parsing dravid's response: {str(e)}")
        return False

    print_info("dravid's suggested fix:")
    pretty_print_commands(fix_commands)

    user_input = monitor.get_user_input(
        "Do you want to apply this fix? [y/N]: ")
    if user_input == 'y':
        print_info("Applying dravid's suggested fix...")
        executor = Executor()
        for cmd in fix_commands:
            if cmd['type'] == 'shell':
                print_info(f"Executing: {cmd['command']}")
                executor.execute_shell_command(cmd['command'])
            elif cmd['type'] == 'file':
                print_info(
                    f"Performing file operation: {cmd['operation']} on {cmd['filename']}")
                executor.perform_file_operation(
                    cmd['operation'], cmd['filename'], cmd.get('content'))
        print_success("Fix applied. Requesting server restart...")
        monitor.request_restart()
        return True
    else:
        print_info("Fix not applied. Continuing with current state.")
        return False

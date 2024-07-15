import traceback
from ...api.dravid_api import call_dravid_api_with_pagination
from ...api.dravid_parser import parse_dravid_response, pretty_print_commands
from ...utils.step_executor import Executor
from ...utils.utils import print_error, print_success, print_info
from ...prompts.monitor_error_resolution import get_error_resolution_prompt


def monitoring_handle_error_with_dravid(error, line, monitor):
    print_error(f"Error detected: {error}")
    error_message = str(error)
    error_type = type(error).__name__
    error_trace = ''.join(traceback.format_exception(
        type(error), error, error.__traceback__))
    project_context = monitor.metadata_manager.get_project_context()

    error_query = get_error_resolution_prompt(
        error_type, error_message, error_trace, line, project_context
    )

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

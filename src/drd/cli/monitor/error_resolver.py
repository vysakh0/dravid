import traceback
from ...api.main import call_dravid_api
from ...utils.step_executor import Executor
from ...utils.utils import print_error, print_success, print_info, print_command_details
from ...utils.loader import run_with_loader
from ...prompts.monitor_error_resolution import get_error_resolution_prompt
from ..query.file_operations import get_files_to_modify
from ...utils.file_utils import get_file_content


def monitoring_handle_error_with_dravid(error, line, monitor):
    print_error(f"Error detected: {error}")

    error_message = str(error)
    error_type = type(error).__name__
    error_trace = ''.join(traceback.format_exception(
        type(error), error, error.__traceback__))

    project_context = monitor.metadata_manager.get_project_context()

    print_info("Identifying relevant files for error context...")
    error_details = f"error_msg: {error_message}, error_type: {error_type}, error_trace: {error_trace}"
    files_to_check = run_with_loader(
        lambda: get_files_to_modify(error_details, project_context),
        "Analyzing project files"
    )

    print_info(f"Found {len(files_to_check)} potentially relevant files.")

    file_contents = {}
    for file in files_to_check:
        content = get_file_content(file)
        if content:
            file_contents[file] = content
            print_info(f"  - Read content of {file}")

    file_context = "\n".join(
        [f"Content of {file}:\n{content}" for file,
            content in file_contents.items()]
    )

    error_query = get_error_resolution_prompt(
        error_type, error_message, error_trace, line, project_context, file_context
    )

    print_info("Sending error information to Dravid for analysis...")
    try:
        fix_commands = call_dravid_api(error_query, include_context=True)
    except ValueError as e:
        print_error(f"Error parsing dravid's response: {str(e)}")
        return False

    print_info("Dravid's suggested fix:")
    print_command_details(fix_commands)

    user_input = monitor.get_user_input(
        "Do you want to proceed with this fix? You will be able to stop anytime during the step. [y/N]: "
    )

    if user_input.lower() == 'y':
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

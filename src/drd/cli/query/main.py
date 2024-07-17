import click
from ...api.main import stream_dravid_api, call_dravid_vision_api
from ...utils.step_executor import Executor
from ...metadata.project_metadata import ProjectMetadataManager
from .dynamic_command_handler import handle_error_with_dravid, execute_commands
from ...utils import print_error, print_success, print_info, print_step, print_debug, print_warning, run_with_loader
from ...utils.file_utils import get_file_content, fetch_project_guidelines
from ...metadata.common_utils import generate_file_description
from .file_operations import get_files_to_modify
from ...utils.parser import parse_dravid_response


def execute_dravid_command(query, image_path, debug, instruction_prompt):
    print_info("Starting Dravid CLI tool..")
    print_warning("Please make sure you are in a fresh directory.")
    print_warning(
        "If it is an existing project, please ensure you're in a git branch")
    print_warning("Use Ctrl+C to exit if you're not")

    executor = Executor()
    metadata_manager = ProjectMetadataManager(executor.current_dir)

    try:
        project_context = metadata_manager.get_project_context()

        if project_context:
            print_info("Identifying related files to the query...")
            print_info("LLM calls to be made: 1")
            files_to_modify = run_with_loader(
                lambda: get_files_to_modify(query, project_context),
                "Analyzing project files"
            )

            print_info(
                f"Found {len(files_to_modify)} potentially relevant files.")
            if debug:
                print_info("Possible files to be modified:")
                for file in files_to_modify:
                    print(f"  - {file}")

            print_info("Reading file contents...")
            file_contents = {}
            for file in files_to_modify:
                content = get_file_content(file)
                if content:
                    file_contents[file] = content
                    print_info(f"  - Read content of {file}")

            project_guidelines = fetch_project_guidelines(executor.current_dir)
            file_context = "\n".join(
                [f"Current content of {file}:\n{content}" for file, content in file_contents.items()])
            full_query = f"{project_context}\n\nProject Guidelines:\n{project_guidelines}\n\nCurrent file contents:\n{file_context}\n\nUser query: {query}"
        else:
            print_info(
                "No current project context found. Will create a new project in the current directory.")
            full_query = f"User query: {query}"

        print_info("Preparing to send query to Claude API...")
        if image_path:
            print_info(f"Processing image: {image_path}")
            print_info("LLM calls to be made: 1")
            commands = run_with_loader(
                lambda: call_dravid_vision_api(
                    full_query, image_path, include_context=True, instruction_prompt=instruction_prompt),
                "Analyzing image and generating response"
            )
        else:
            print_info("Streaming response from Claude API...")
            print_info("LLM calls to be made: 1")
            xml_result = stream_dravid_api(
                full_query, include_context=True, instruction_prompt=instruction_prompt, print_chunk=False)
            commands = parse_dravid_response(xml_result)
            # return None
            if debug:
                print_debug(f"Received {len(commands)} new command(s)")

        if not commands:
            print_error(
                "Failed to parse Claude's response or no commands to execute.")
            return

        print_info(
            f"Parsed {len(commands)} commands from Claude's response.")

        # Execute commands using the new execute_commands function
        success, step_completed, error_message, all_outputs = execute_commands(
            commands, executor, metadata_manager, debug=debug)

        if not success:
            print_error(f"Failed to execute command at step {step_completed}.")
            print_error(f"Error message: {error_message}")
            print_info("Attempting to fix the error...")
            if handle_error_with_dravid(Exception(error_message), commands[step_completed-1], executor, metadata_manager, debug=debug):
                print_info(
                    "Fix applied successfully. Continuing with the remaining commands.")
                # Re-execute the remaining commands
                remaining_commands = commands[step_completed:]
                success, _, error_message, additional_outputs = execute_commands(
                    remaining_commands, executor, metadata_manager, debug=debug)
                all_outputs += "\n" + additional_outputs
            else:
                print_error(
                    "Unable to fix the error. Skipping this command and continuing with the next.")

        print_info("Execution details:")
        click.echo(all_outputs)

        print_success("Dravid CLI tool execution completed.")
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        if debug:
            import traceback
            traceback.print_exc()

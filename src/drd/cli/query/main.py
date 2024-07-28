import click
from ...api.main import stream_dravid_api, call_dravid_vision_api
from ...utils.step_executor import Executor
from ...metadata.project_metadata import ProjectMetadataManager
from .dynamic_command_handler import handle_error_with_dravid, execute_commands
from ...utils import print_error, print_success, print_info, print_debug, print_warning, print_step, print_header, run_with_loader
from ...utils.file_utils import get_file_content, fetch_project_guidelines, is_directory_empty
from .file_operations import get_files_to_modify
from ...utils.parser import parse_dravid_response


def execute_dravid_command(query, image_path, debug, instruction_prompt, warn=None, reference_files=None):
    print_header("Starting Dravid AI ...")

    if warn:
        print_warning("Please ensure you review and commit(git) changes")
        print("\n")

    executor = Executor()

    metadata_manager = ProjectMetadataManager(executor.current_dir)

    try:
        project_context = metadata_manager.get_project_context()

        files_info = None
        if project_context:
            print_info("🔍 Identifying related files to the query...", indent=2)
            print_info("(1 LLM call)", indent=4)
            files_info = run_with_loader(
                lambda: get_files_to_modify(query, project_context),
                "Analyzing project files"
            )

            if debug:
                print_info("Files and dependencies analysis:", indent=4)
                if files_info['main_file']:
                    print_info(
                        f"Main file to modify: {files_info['main_file']}", indent=6)
                print_info("Dependencies:", indent=6)
                for dep in files_info['dependencies']:
                    print_info(f"- {dep['file']}", indent=8)
                    for imp in dep['imports']:
                        print_info(f"  Imports: {imp}", indent=10)
                print_info("New files to create:", indent=6)
                for new_file in files_info['new_files']:
                    print_info(f"- {new_file['file']}", indent=8)
                print_info("File contents to load:", indent=6)
                for file in files_info['file_contents_to_load']:
                    print_info(f"- {file}", indent=8)

        full_query = construct_full_query(
            query, executor, project_context, files_info, reference_files)
        print(full_query, "full query")

        print_info("💡 Preparing to send query to LLM...", indent=2)
        if image_path:
            print_info(f"Processing image: {image_path}", indent=4)
            print_info("(1 LLM call)", indent=4)
            commands = run_with_loader(
                lambda: call_dravid_vision_api(
                    full_query, image_path, include_context=True, instruction_prompt=instruction_prompt),
                "Analyzing image and generating response"
            )
        else:
            print_info("💬 Streaming response from LLM...", indent=2)
            print_info("(1 LLM call)", indent=4)
            xml_result = stream_dravid_api(
                full_query, include_context=True, instruction_prompt=instruction_prompt, print_chunk=False)
            commands = parse_dravid_response(xml_result)
            if debug:
                print_debug(f"Received {len(commands)} new command(s)")

        if not commands:
            print_error(
                "Failed to parse LLM's response or no commands to execute.")
            print_debug("Actual result: " + str(xml_result))
            return

        success, step_completed, error_message, all_outputs = execute_commands(
            commands, executor, metadata_manager, debug=debug)

        print("no scucess", success)
        if not success:
            print("called")
            print_error(
                f"Failed to execute command at step {step_completed}.")
            print_error(f"Error message: {error_message}")
            print_info("Attempting to fix the error...")
            if handle_error_with_dravid(Exception(error_message), commands[step_completed-1], executor, metadata_manager, debug=debug):
                print_info(
                    "Fix applied successfully. Continuing with the remaining commands.", indent=2)
                remaining_commands = commands[step_completed:]
                success, _, error_message, additional_outputs = execute_commands(
                    remaining_commands, executor, metadata_manager, debug=debug)
                all_outputs += "\n" + additional_outputs
            else:
                print_error(
                    "Unable to fix the error. Skipping this command and continuing with the next.")

        print_info("Execution details:", indent=2)
        click.echo(all_outputs)

        print_success("Dravid CLI Tool execution completed.")
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        if debug:
            import traceback
            traceback.print_exc()


def construct_full_query(query, executor, project_context, files_info=None, reference_files=None):
    is_empty = is_directory_empty(executor.current_dir)

    if is_empty:
        print_info(
            "Current directory is empty. Will create a new project.", indent=2)
        full_query = f"Current directory is empty.\n\nUser query: {query}"
    elif not project_context:
        print_info(
            "No current project context found, but directory is not empty.", indent=2)
        full_query = f"Current directory is not empty, but no project context is available.\n\nUser query: {query}"
    else:
        print_info(
            "Constructing query with project context and file information.", indent=2)

        project_guidelines = fetch_project_guidelines(executor.current_dir)

        full_query = f"{project_context}\n\n"
        full_query += f"Project Guidelines:\n{project_guidelines}\n\n"

        if files_info:
            if files_info['file_contents_to_load']:
                file_contents = {}
                for file in files_info['file_contents_to_load']:
                    content = get_file_content(file)
                    if content:
                        file_contents[file] = content
                        print_info(f"  - Read content of {file}", indent=4)

                file_context = "\n".join(
                    [f"Current content of {file}:\n{content}" for file, content in file_contents.items()])
                full_query += f"Current file contents:\n{file_context}\n\n"

            if files_info['dependencies']:
                dependency_context = "\n".join(
                    [f"Dependency {dep['file']} exports: {', '.join(dep['imports'])}" for dep in files_info['dependencies']])
                full_query += f"Dependencies:\n{dependency_context}\n\n"

            if files_info['new_files']:
                new_files_context = "\n".join(
                    [f"New file to create: {new_file['file']}" for new_file in files_info['new_files']])
                full_query += f"New files to create:\n{new_files_context}\n\n"

            if files_info['main_file']:
                full_query += f"Main file to modify: {files_info['main_file']}\n\n"

        full_query += "Current directory is not empty.\n\n"
        full_query += f"User query: {query}"

    if reference_files:
        print_info("📄 Reading reference file contents...", indent=2)
        reference_contents = {}
        for file in reference_files:
            content = get_file_content(file)
            if content:
                reference_contents[file] = content
                print_info(f"  - Read content of {file}", indent=4)

        reference_context = "\n\n".join(
            [f"Reference file {file}:\n{content}" for file, content in reference_contents.items()])
        full_query += f"\n\nReference files:\n{reference_context}"

    return full_query

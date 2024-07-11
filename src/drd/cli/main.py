import click
import os
from dotenv import load_dotenv
from .query import execute_dravid_command
from ..prompts.claude_instructions import get_instruction_prompt
from .monitor import run_dev_server_with_monitoring
from ..metadata.initializer import initialize_project_metadata
from ..metadata.updater import update_metadata_with_dravid
from colorama import init

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()


@click.command()
@click.argument('query', required=False)
@click.option('--image', type=click.Path(exists=True), help='Path to an image file to include with the query')
@click.option('--debug', is_flag=True, help='Print more information on how this coding assistant executes your instruction')
@click.option('--monitor-fix', is_flag=True, help='Start the dev server monitor to automatically fix errors')
@click.option('--meta-add', help='Update metadata based on the provided description')
@click.option('--meta-init', is_flag=True, help='Initialize project metadata')
def dravid_cli(query, image, debug, monitor_fix, meta_add, meta_init):
    if monitor_fix:
        run_dev_server_with_monitoring()
    elif meta_add:
        update_metadata_with_dravid(meta_add, os.getcwd())
    elif meta_init:
        initialize_project_metadata(os.getcwd())
    elif query:
        instruction_prompt = get_instruction_prompt()
        execute_dravid_command(query, image, debug, instruction_prompt)
    else:
        click.echo(
            "Please provide a query, use --meta-add to update metadata, or use --meta-init to initialize project metadata.")


if __name__ == '__main__':
    dravid_cli()

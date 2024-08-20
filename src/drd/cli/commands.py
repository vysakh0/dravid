import logging
import click
import sys
import ast
import os
import asyncio
from dotenv import load_dotenv
from .query import execute_dravid_command
from ..prompts.instructions import get_instruction_prompt
from .monitor import run_dev_server_with_monitoring
from ..metadata.initializer import initialize_project_metadata
from ..metadata.updater import update_metadata_with_dravid
from ..utils.utils import print_error
from .ask_handler import handle_ask_command

VERSION = "0.14.0"  # Update this as you release new versions


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='dravid_monitor.log',
                    filemode='a')

# Also log to console
# console = logging.StreamHandler()
# console.setLevel(logging.INFO)
# formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# console.setFormatter(formatter)
# logging.getLogger('').addHandler(console)


def parse_multiline_input(input_string):
    try:
        # Use ast.literal_eval to safely evaluate the string as a Python literal
        parsed = ast.literal_eval(input_string)
        if isinstance(parsed, str):
            return parsed
    except (SyntaxError, ValueError):
        pass
    return input_string  # Return the original string if parsing fails


def handle_query_command(query, image, debug):
    if not query and not sys.stdin.isatty():
        query = sys.stdin.read().strip()
    if not query:
        click.echo("Please provide a query using the --do option.")
        return

    query = parse_multiline_input(query)
    instruction_prompt = get_instruction_prompt()
    execute_dravid_command(query, image, debug, instruction_prompt, warn=True)


def dravid_cli_logic(command, do, image, debug, meta_add, meta_init, ask, file, version):
    if version:
        click.echo(f"Dravid CLI version {VERSION}")
        return

    if meta_add:
        update_metadata_with_dravid(meta_add, os.getcwd())
    elif meta_init:
        asyncio.run(initialize_project_metadata(os.getcwd()))
    elif ask or file:
        handle_ask_command(ask, file, debug)
    elif do is not None:
        handle_query_command(do, image, debug)
    elif command:
        run_dev_server_with_monitoring(command)
    else:
        click.echo("Please provide a command to run or use --do for queries.")

import click
from dotenv import load_dotenv
from colorama import init
from .commands import dravid_cli_logic

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()


@click.command()
@click.argument('query', required=False)
@click.option('--image', '--img', type=click.Path(exists=True), help='Path to an image file to include with the query')
@click.option('--debug', is_flag=True, help='Print more information on how this coding assistant executes your instruction')
@click.option('--hot-fix', '--hf', is_flag=True, help='Start the server monitor to automatically fix errors')
@click.option('--meta-add', '--a', help='Update metadata based on the provided description')
@click.option('--meta-init', '--i', is_flag=True, help='Initialize project metadata')
@click.option('--ask', help='Ask an open-ended question and get a streamed response from Claude')
@click.option('--file', type=click.Path(), multiple=True, help='Read content from specified file(s) and include in the context')
@click.option('--version', is_flag=True, help='Show the version of the tool')
@click.option('--command', '--cmd', help='Custom command to run in the monitor (e.g., "npm run test")')
def dravid_cli(query, image, debug, hot_fix, meta_add, meta_init, ask, file, version, command):
    dravid_cli_logic(query, image, debug, hot_fix,
                     meta_add, meta_init, ask, file, version, command)


if __name__ == '__main__':
    dravid_cli()

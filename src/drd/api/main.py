import click
from .claude_api import call_claude_api_with_pagination, call_claude_vision_api_with_pagination, stream_claude_response
from ..utils import print_debug
from ..utils.loader import Loader
from ..utils.pretty_print_stream import pretty_print_xml_stream
from ..utils.parser import parse_dravid_response
import xml.etree.ElementTree as ET


def stream_dravid_api(query, include_context=False, instruction_prompt=None, print_chunk=False):
    xml_buffer = ""
    loader = Loader("Gathering responses from Claude API...")
    loader.start()
    state = {
        'buffer': '',
        'in_step': False,
    }
    try:
        for chunk in stream_claude_response(query, instruction_prompt):
            if print_chunk:
                click.echo(chunk, nl=False)
            else:
                pretty_print_xml_stream(chunk, state)
            xml_buffer += chunk
    finally:
        loader.stop()

    if not print_chunk:
        return xml_buffer
    else:
        return None


def call_dravid_api(query, include_context=False, instruction_prompt=None):
    response = call_dravid_api_with_pagination(
        query, include_context, instruction_prompt)
    return parse_dravid_response(response)


def call_dravid_vision_api(query, image_path, include_context=False, instruction_prompt=None):
    response = call_claude_vision_api_with_pagination(
        query, image_path, include_context, instruction_prompt)
    return parse_dravid_response(response)


def call_dravid_api_with_pagination(query, include_context=False, instruction_prompt=None):
    response = call_claude_api_with_pagination(
        query, include_context, instruction_prompt)
    return response


def call_dravid_vision_api_with_pagination(query, include_context=False, instruction_prompt=None):
    response = call_claude_vision_api_with_pagination(
        query, include_context, instruction_prompt)
    return response

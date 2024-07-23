import os
import click
from .claude_api import call_claude_api_with_pagination, call_claude_vision_api_with_pagination, stream_claude_response
from .openai_api import call_api_with_pagination, call_vision_api_with_pagination, stream_response
from ..utils import print_debug, print_info
from ..utils.loader import Loader
from ..utils.pretty_print_stream import pretty_print_xml_stream
from ..utils.parser import parse_dravid_response
import xml.etree.ElementTree as ET


def get_api_functions():
    llm_type = os.getenv('DRAVID_LLM', 'claude').lower()
    if llm_type == 'claude':
        return call_claude_api_with_pagination, call_claude_vision_api_with_pagination, stream_claude_response
    elif llm_type in ['openai', 'azure', 'custom', 'ollama']:
        return call_api_with_pagination, call_vision_api_with_pagination, stream_response
    else:
        raise ValueError(f"Unsupported LLM type: {llm_type}")


def stream_dravid_api(query, include_context=False, instruction_prompt=None, print_chunk=False):
    _, _, stream_response = get_api_functions()

    if print_chunk:
        print_info("DRAVID: ")
        for chunk in stream_response(query, instruction_prompt):
            click.echo(chunk, nl=False)
        return None
    else:
        xml_buffer = ""
        loader = Loader("Gathering responses from API...")
        state = {
            'buffer': '',
            'in_step': False,
        }
        try:
            for chunk in stream_response(query, instruction_prompt):
                if print_chunk:
                    click.echo(chunk, nl=False)
                else:
                    pretty_print_xml_stream(chunk, state)
                xml_buffer += chunk
        finally:
            loader.stop()
        return xml_buffer


def call_dravid_api(query, include_context=False, instruction_prompt=None):
    call_api, _, _ = get_api_functions()
    response = call_api(query, include_context, instruction_prompt)
    return parse_dravid_response(response)


def call_dravid_vision_api(query, image_path, include_context=False, instruction_prompt=None):
    _, call_vision_api, _ = get_api_functions()
    response = call_vision_api(
        query, image_path, include_context, instruction_prompt)
    return parse_dravid_response(response)


def call_dravid_api_with_pagination(query, include_context=False, instruction_prompt=None):
    call_api, _, _ = get_api_functions()
    response = call_api(query, include_context, instruction_prompt)
    return response


def call_dravid_vision_api_with_pagination(query, image_path, include_context=False, instruction_prompt=None):
    _, call_vision_api, _ = get_api_functions()
    response = call_vision_api(
        query, image_path, include_context, instruction_prompt)
    return response

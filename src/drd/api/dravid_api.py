from ..utils.api_utils import call_dravid_api_with_pagination, call_dravid_vision_api_with_pagination, stream_claude_response, parse_paginated_response
from ..utils import print_error, print_info, print_debug
from ..utils.loader import Loader
from ..utils.pretty_print_stream import pretty_print_xml_stream
from .dravid_parser import parse_dravid_response
import xml.etree.ElementTree as ET
import click
import re


def stream_dravid_api(query, include_context=False, instruction_prompt=None, debug=False):
    xml_buffer = ""
    loader = Loader("Preparing response from Claude API")
    loader.start()
    state = {
        'buffer': '',
        'in_step': False,
    }

    try:
        for chunk in stream_claude_response(query, instruction_prompt):
            if debug:
                print_debug(f"Raw chunk received: {chunk}")

            pretty_print_xml_stream(chunk, state)
            xml_buffer += chunk
    finally:
        loader.stop()

    return xml_buffer


def call_dravid_api(query, include_context=False, instruction_prompt=None):
    response = call_dravid_api_with_pagination(
        query, include_context, instruction_prompt)
    return parse_dravid_response(response)


def call_dravid_vision_api(query, image_path, include_context=False, instruction_prompt=None):
    response = call_dravid_vision_api_with_pagination(
        query, image_path, include_context, instruction_prompt)
    return parse_dravid_response(response)

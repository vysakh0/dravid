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
    in_response = False
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

            if not in_response:
                in_response = True

            if in_response:
                pretty_print_xml_stream(chunk, state)
                xml_buffer += chunk

                commands = parse_streaming_xml(xml_buffer)
                if commands:
                    yield commands
                    # Keep any partial XML in the buffer
                    last_end = xml_buffer.rfind('</step>')
                    if last_end != -1:
                        xml_buffer = xml_buffer[last_end + 7:]
                    else:
                        xml_buffer = ""

            if '</response>' in chunk:
                if debug:
                    print_debug("Response end detected")
                break
    finally:
        loader.stop()


def parse_streaming_xml(xml_buffer):
    commands = []
    for match in re.finditer(r'<step>(.*?)</step>', xml_buffer, re.DOTALL):
        step_content = match.group(1)
        command = parse_step(step_content)
        if command:
            commands.append(command)
    return commands


def parse_step(step_content):
    command = {}
    for tag in ['type', 'operation', 'filename', 'content', 'command']:
        match = re.search(f'<{tag}>(.*?)</{tag}>', step_content, re.DOTALL)
        if match:
            command[tag] = match.group(1).strip()
    return command if command else None


def call_dravid_api(query, include_context=False, instruction_prompt=None):
    response = call_dravid_api_with_pagination(
        query, include_context, instruction_prompt)
    return parse_dravid_response(response)


def call_dravid_vision_api(query, image_path, include_context=False, instruction_prompt=None):
    response = call_dravid_vision_api_with_pagination(
        query, image_path, include_context, instruction_prompt)
    return parse_dravid_response(response)

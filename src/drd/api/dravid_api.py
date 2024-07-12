from ..utils.api_utils import call_dravid_api_with_pagination, call_dravid_vision_api_with_pagination, stream_claude_response, parse_paginated_response
import xml.etree.ElementTree as ET


def stream_dravid_api(query, include_context=False, instruction_prompt=None):
    xml_buffer = ""
    for chunk in stream_claude_response(query, instruction_prompt):
        xml_buffer += chunk
        complete_commands, xml_buffer = parse_streaming_xml(xml_buffer)
        if complete_commands:
            yield complete_commands


def parse_streaming_xml(xml_buffer):
    complete_commands = []
    while True:
        start = xml_buffer.find('<step>')
        end = xml_buffer.find('</step>')

        if start != -1 and end != -1 and start < end:
            step = xml_buffer[start:end+7]
            try:
                root = ET.fromstring(f'<root>{step}</root>')
                command = {}
                for child in root.find('step'):
                    if child.tag == 'content':
                        command[child.tag] = child.text.strip(
                        ) if child.text else ''
                    else:
                        command[child.tag] = child.text
                complete_commands.append(command)
                xml_buffer = xml_buffer[end+7:]
            except ET.ParseError:
                break
        else:
            break

    return complete_commands, xml_buffer


def call_dravid_api(query, include_context=False, instruction_prompt=None):
    response = call_dravid_api_with_pagination(
        query, include_context, instruction_prompt)
    return parse_paginated_response(response)


def call_dravid_vision_api(query, image_path, include_context=False, instruction_prompt=None):
    response = call_dravid_vision_api_with_pagination(
        query, image_path, include_context, instruction_prompt)
    return parse_paginated_response(response)

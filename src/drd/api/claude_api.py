import requests
import os
import json
from typing import Dict, Any, Optional, List
from ..utils.parser import extract_and_parse_xml, parse_dravid_response
from ..utils.file_utils import convert_to_base64
from typing import Dict, Any, Optional, List, Generator
import xml.etree.ElementTree as ET
import click

API_URL = 'https://api.anthropic.com/v1/messages'
MODEL = 'claude-3-5-sonnet-20240620'
MAX_TOKENS = 8000


def get_api_key() -> str:
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")
    return api_key


def get_headers(api_key: str) -> Dict[str, str]:
    return {
        'x-api-key': api_key,
        'Content-Type': 'application/json',
        "Anthropic-Beta": "max-tokens-3-5-sonnet-2024-07-15",
        'Anthropic-Version': '2023-06-01'
    }


def make_api_call(data: Dict[str, Any], headers: Dict[str, str], stream: bool = False) -> requests.Response:
    response = requests.post(
        API_URL, json=data, headers=headers, stream=stream)
    response.raise_for_status()
    return response


def parse_response(response: str) -> str:
    try:
        root = extract_and_parse_xml(response)
        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        click.echo(f"Error parsing XML response: {e}", err=True)
        return response


def call_claude_api_with_pagination(query: str, include_context: bool = False, instruction_prompt: Optional[str] = None) -> str:
    api_key = get_api_key()
    headers = get_headers(api_key)
    full_response = ""

    data = {
        'model': MODEL,
        'system': instruction_prompt or "",
        'messages': [{'role': 'user', 'content': query}],
        'max_tokens': MAX_TOKENS
    }

    while True:
        response = make_api_call(data, headers)
        resp = response.json()
        full_response += resp['content'][0]['text']

        if 'stop_reason' in resp and resp['stop_reason'] == 'max_tokens':
            # If the response was truncated, continue the conversation
            data['messages'].append(
                {'role': 'assistant', 'content': full_response})
            data['messages'].append(
                {'role': 'user', 'content': 'Please continue.'})
        else:
            break

    return parse_response(full_response)


def call_claude_vision_api_with_pagination(query: str, image_path: str, include_context: bool = False, instruction_prompt: Optional[str] = None) -> str:
    api_key = get_api_key()
    headers = get_headers(api_key)

    mime_type, image_data = convert_to_base64(image_path)

    full_response = ""
    data = {
        'model': MODEL,
        'system': instruction_prompt or "",
        'messages': [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64',
                            'media_type': mime_type,
                            'data': image_data
                        }
                    },
                    {
                        'type': 'text',
                        'text': query
                    }
                ]
            }
        ],
        'max_tokens': MAX_TOKENS
    }

    while True:
        response = make_api_call(data, headers)
        resp = response.json()
        full_response += resp['content'][0]['text']

        if 'stop_reason' in resp and resp['stop_reason'] == 'max_tokens':
            # If the response was truncated, continue the conversation
            data['messages'].append(
                {'role': 'assistant', 'content': full_response})
            data['messages'].append(
                {'role': 'user', 'content': 'Please continue.'})
        else:
            break

    return parse_response(full_response)


def stream_claude_response(query: str, instruction_prompt: Optional[str] = None) -> Generator[str, None, None]:
    api_key = get_api_key()
    headers = get_headers(api_key)
    headers['Accept'] = 'text/event-stream'

    data = {
        'model': MODEL,
        'system': instruction_prompt or "",
        'messages': [{'role': 'user', 'content': query}],
        'max_tokens': MAX_TOKENS,
        'stream': True
    }

    response = make_api_call(data, headers, stream=True)

    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if data['type'] == 'content_block_delta':
                    chunk = data['delta']['text']
                    yield chunk
                elif data['type'] == 'message_stop':
                    break

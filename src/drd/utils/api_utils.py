import requests
import os
import json
import base64
from ..api.dravid_parser import extract_and_parse_xml
import xml.etree.ElementTree as ET
import click


def call_dravid_api(query, include_context=False, instruction_prompt=None):
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")

    headers = {
        'x-api-key': f'{api_key}',
        'Content-Type': 'application/json',
        'Anthropic-Version': '2023-06-01'
    }

    instruction_prompt = instruction_prompt or ""

    data = {
        'model': 'claude-3-5-sonnet-20240620',
        'system': instruction_prompt,
        'messages': [
            {'role': 'user', 'content': query}
        ],
        'max_tokens': 4000
    }

    response = requests.post(
        'https://api.anthropic.com/v1/messages', json=data, headers=headers)
    response.raise_for_status()

    resp = response.json()['content'][0]['text']
    print(resp, "resp")

    try:
        root = extract_and_parse_xml(resp)
        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        print(f"Error parsing XML response: {e}")
        return resp


def call_dravid_vision_api(query, image_path, include_context=False, instruction_prompt=None):
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")

    headers = {
        'x-api-key': f'{api_key}',
        'Content-Type': 'application/json',
        'Anthropic-Version': '2023-06-01'
    }

    instruction_prompt = instruction_prompt or ""

    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')

    data = {
        'model': 'claude-3-5-sonnet-20240620',
        'system': instruction_prompt,
        'messages': [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64',
                            'media_type': 'image/png',  # Adjust based on actual image type
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
        'max_tokens': 4000
    }

    response = requests.post(
        'https://api.anthropic.com/v1/messages', json=data, headers=headers)
    response.raise_for_status()

    resp = response.json()['content'][0]['text']
    print(resp, "resp")

    try:
        root = extract_and_parse_xml(resp)
        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        print(f"Error parsing XML response: {e}")
        return resp


def stream_claude_response(query, instruction_prompt=None):
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")

    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Anthropic-Version': '2023-06-01'
    }

    instruction_prompt = instruction_prompt or ""

    data = {
        'model': 'claude-3-5-sonnet-20240620',
        'system': instruction_prompt,
        'messages': [
            {'role': 'user', 'content': query}
        ],
        'max_tokens': 4000,
        'stream': True
    }

    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        json=data,
        headers=headers,
        stream=True
    )
    response.raise_for_status()

    full_response = ""
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if data['type'] == 'content_block_delta':
                    chunk = data['delta']['text']
                    full_response += chunk
                    click.echo(chunk, nl=False)
                elif data['type'] == 'message_stop':
                    click.echo()
                    break

    return full_response
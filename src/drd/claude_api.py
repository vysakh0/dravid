import json
import os
import requests
from .utils import get_project_context
from .prompts.claude_instructions import get_instruction_prompt
from .prompts.file_operations import get_file_identification_prompt, get_file_description_prompt


def call_claude_api(query, include_context=False):
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")

    headers = {
        'x-api-key': f'{api_key}',
        'Content-Type': 'application/json',
        'Anthropic-Version': '2023-06-01'
    }

    instruction_prompt = get_instruction_prompt()

    if include_context:
        project_context = get_project_context()
        query = f"Project context:\n{project_context}\n\nUser query: {query}"

    data = {
        'model': 'claude-3-5-sonnet-20240620',
        'system': instruction_prompt,
        'messages': [
            {'role': 'user', 'content': query}
        ],
        'max_tokens': 2000
    }

    response = requests.post(
        'https://api.anthropic.com/v1/messages', json=data, headers=headers)
    response.raise_for_status()

    resp = response.json()['content'][0]['text']
    print(resp, "resp")
    return resp


def identify_file(query):
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")

    headers = {
        'x-api-key': f'{api_key}',
        'Anthropic-Version': '2023-06-01',
        'Content-Type': 'application/json'
    }

    project_context = get_project_context()
    system_message = get_file_identification_prompt()

    data = {
        'model': 'claude-3-5-sonnet-20240620',
        'system': system_message,
        'messages': [
            {'role': 'user', 'content': f"Project context:\n{project_context}\n\nUser query: {query}"}
        ],
        'max_tokens': 1000
    }

    response = requests.post(
        'https://api.anthropic.com/v1/messages', json=data, headers=headers)
    response.raise_for_status()

    try:
        resp = response.json()['content'][0]['text']
        print(resp, "---")
        file_info = json.loads(response.json()['content'][0]['text'])
        return file_info['filename'], file_info['exists']
    except json.JSONDecodeError:
        raise ValueError(
            "Failed to parse file identification response from Claude")


def generate_description(filename, content):
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")

    headers = {
        'x-api-key': f'{api_key}',
        'Content-Type': 'application/json',
        'Anthropic-Version': '2023-06-01'
    }

    system_message = get_file_description_prompt()

    data = {
        'model': 'claude-3-5-sonnet-20240620',
        'system': system_message,
        'messages': [
            {'role': 'user',
                'content': f"Filename: {filename}\n\nContent:\n{content[:1000]}..."}
        ],
        'max_tokens': 1000
    }

    response = requests.post(
        'https://api.anthropic.com/v1/messages', json=data, headers=headers)
    response.raise_for_status()

    description = response.json()['content'][0]['text'].strip()
    return description[:100]  # Ensure the description is not too long

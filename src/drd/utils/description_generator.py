import requests
import os


def generate_description(filename, content):
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")

    headers = {
        'x-api-key': f'{api_key}',
        'Content-Type': 'application/json',
        'Anthropic-Version': '2023-06-01'
    }

    system_message = "You are a file description assistant. Based on the file content provided, generate a brief, informative description of the file in 100 characters or less. Just strictly description alone, no other text"

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

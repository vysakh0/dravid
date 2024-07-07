import json
import os
import requests
from .utils import get_project_context

# Rest of the file remains the same


def get_instruction_prompt():
    return """
# Instructions for Claude: Project Setup Assistant

You are a project setup assistant. Make sure you generate steps in the proper order, the prerequisiste steps should come first
to avoid errors. If the command involves nextjs app or rails or python app create a suitable directory instead of using current directory directly.
Your responses should follow a specific JSON format to ensure reliable parsing. 
If there is a need to create a project please create the files under it.
Generate strictly json only no text before or after.
Use the following structure:

{
  "explanation": "A brief explanation of the steps, if necessary",
  "steps": [
    {
      "type": "shell",
      "command": "command to execute"
    },
    {
      "type": "file",
      "operation": "CREATE",
      "filename": "path/to/file.ext",
      "content": "file content here"
    },
    {
      "type": "file",
      "operation": "UPDATE",
      "filename": "path/to/existing/file.ext",
      "content": "content to append or replace"
    },
    {
      "type": "file",
      "operation": "DELETE",
      "filename": "path/to/file/to/delete.ext"
    }
  ]
}
The "explanation" field is optional and can be used for any text that doesn't fit into a specific command or file operation.
When asked to perform tasks, provide step-by-step instructions using this JSON format. Be sure to include all necessary steps, file creations, and modifications. 
Always use valid JSON syntax no extra words outside json before or after.

Important guidelines:
1. For commands that might prompt for user input (like create-next-app), always include flags to make them non-interactive. For example:
   - Use `npx create-next-app@latest my-app --typescript --eslint --tailwind --src-dir --app --import-alias "@/*" --use-npm` instead of `npx create-next-app@latest my-app`
   - For other potentially interactive commands, research and include appropriate flags to make them non-interactive.

2. When using 'cd' commands, be aware that the current working directory changes. After a 'cd' command:
   - Use relative paths for file operations and commands.
   - Do not include the project folder name in file paths for operations within that folder.
   - For example, after `cd my-nextjs-app`, use "filename": "src/app/page.tsx" instead of "filename": "my-nextjs-app/src/app/page.tsx".

3. Always provide absolute paths when creating or referring to files outside the current project directory.

4. If you need to perform operations in the parent directory or another absolute path, use a 'cd' command first to change the working directory.

Remember to maintain a logical flow of operations, ensuring that directories exist before creating files within them, and that you're in the correct directory when executing commands or performing file operations.
"""


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

    system_message = """You are a file identification assistant. Based on the user's query and the project context, 
    identify which file the user is likely referring to. If no existing file seems relevant, suggest a new file name. 
    Respond with a JSON object containing the 'filename' and a boolean 'exists' indicating if it's an existing file.
    Do not respond anything other than the json. No extra text except the json.
    """

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

    system_message = """You are a file description assistant. Based on the file content provided, 
    generate a brief, informative description of the file in 100 characters or less. Just strictly description alone, no other text"""

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

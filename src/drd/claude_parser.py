import json
import re


def parse_claude_response(response):
    try:
        # First, try to parse the response as-is
        parsed_response = json.loads(response)
        return process_parsed_response(parsed_response)
    except json.JSONDecodeError:
        # If parsing fails, attempt to fix common issues
        fixed_response = fix_json_response(response)
        try:
            parsed_response = json.loads(fixed_response)
            return process_parsed_response(parsed_response)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return []


def fix_json_response(response):
    # Remove any text before the first '{' and after the last '}'
    response = re.sub(r'^[^{]*', '', response)
    response = re.sub(r'[^}]*$', '', response)

    # Escape newlines and other control characters in string values
    def escape_string(match):
        return json.dumps(match.group(0))[1:-1]  # Remove outer quotes

    response = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', escape_string, response)

    return response


def process_parsed_response(parsed_response):
    commands = parsed_response.get('steps', [])
    if 'explanation' in parsed_response:
        commands.insert(0, {
            'type': 'explanation',
            'content': parsed_response['explanation']
        })
    return commands


def pretty_print_commands(commands):
    for i, cmd in enumerate(commands, 1):
        print(f"Command {i}:")
        for key, value in cmd.items():
            if key == 'content' and len(value) > 100:
                print(f"  {key}: {value[:100]}... (truncated)")
            else:
                print(f"  {key}: {value}")
        print()

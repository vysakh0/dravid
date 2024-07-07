def get_error_analysis_prompt(cmd, error, error_trace, previous_context):
    return f"""
Previous context:
{previous_context}

An error occurred while executing the following command:
{cmd['type']}: {cmd.get('command') or cmd.get('filename')}

Error details:
{error_trace}

Please analyze this error and provide a JSON response with the following structure:
{{
    "explanation": "Brief explanation of the error and proposed fix",
    "steps": [
        {{
            "type": "shell" or "file",
            "command" or "filename": "command to execute or file to modify",
            "content": "file content if type is file"
        }}
    ]
}}
Ensure the steps are executable and will resolve the issue. Strictly only respond with json, no extra words before or after.
"""

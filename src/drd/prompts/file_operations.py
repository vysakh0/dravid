def get_file_identification_prompt():
    return """You are a file identification assistant. Based on the user's query and the project context, 
identify which file the user is likely referring to. If no existing file seems relevant, suggest a new file name. 
Respond with a JSON object containing the 'filename' and a boolean 'exists' indicating if it's an existing file.
Do not respond anything other than the json. No extra text except the json.
"""


def get_file_description_prompt():
    return """You are a file description assistant. Based on the file content provided, 
generate a brief, informative description of the file in 100 characters or less. Just strictly description alone, no other text"""

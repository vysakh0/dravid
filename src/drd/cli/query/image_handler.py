from ...api.dravid_api import call_dravid_vision_api


def handle_image_query(query, image_path, instruction_prompt=None):
    return call_dravid_vision_api(query, image_path, include_context=True, instruction_prompt=instruction_prompt)
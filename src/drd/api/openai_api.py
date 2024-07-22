import os
import json
import base64
from typing import Dict, Any, Optional, List, Generator
from openai import OpenAI, AzureOpenAI
from ..utils.parser import extract_and_parse_xml, parse_dravid_response
from ..utils.file_utils import convert_to_base64
import xml.etree.ElementTree as ET
import click
from .ollama_api import get_ollama_client, call_ollama_api_with_pagination, stream_ollama_response

DEFAULT_MODEL = "gpt-4o-2024-05-13"
MAX_TOKENS = 4000


def get_env_variable(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"{name} not found in environment variables")
    return value


def get_client():
    llm_type = get_env_variable('DRAVID_LLM', 'openai').lower()

    if llm_type == 'azure':
        return AzureOpenAI(
            api_key=get_env_variable("AZURE_OPENAI_API_KEY"),
            api_version=get_env_variable("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=get_env_variable("AZURE_OPENAI_ENDPOINT")
        )
    elif llm_type == 'openai':
        return OpenAI()
    elif llm_type == 'custom':
        api_key = get_env_variable("DRAVID_LLM_API_KEY")
        api_base = get_env_variable("DRAVID_LLM_ENDPOINT")
        return OpenAI(api_key=api_key, base_url=api_base)
    elif llm_type == 'ollama':
        return get_ollama_client()
    else:
        raise ValueError(f"Unsupported LLM type: {llm_type}")


def get_model():
    llm_type = get_env_variable('DRAVID_LLM', 'openai').lower()
    if llm_type == 'azure':
        return get_env_variable("AZURE_OPENAI_DEPLOYMENT_NAME")
    elif llm_type == 'custom' or llm_type == 'ollama':
        return get_env_variable("DRAVID_LLM_MODEL")
    else:
        return get_env_variable("OPENAI_MODEL", DEFAULT_MODEL)


def parse_response(response: str) -> str:
    try:
        root = extract_and_parse_xml(response)
        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        click.echo(f"Error parsing XML response: {e}", err=True)
        return response


def call_api_with_pagination(query: str, include_context: bool = False, instruction_prompt: Optional[str] = None) -> str:
    llm_type = get_env_variable('DRAVID_LLM', 'openai').lower()
    model = get_model()

    if llm_type == 'ollama':
        return call_ollama_api_with_pagination(query, model, include_context, instruction_prompt)

    client = get_client()
    full_response = ""
    messages = [
        {"role": "system", "content": instruction_prompt or ""},
        {"role": "user", "content": query}
    ]

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=MAX_TOKENS
        )
        full_response += response.choices[0].message.content

        if response.choices[0].finish_reason != 'length':
            break

        messages.append({"role": "assistant", "content": full_response})
        messages.append({"role": "user", "content": "Please continue."})

    return parse_response(full_response)


def call_vision_api_with_pagination(query: str, image_path: str, include_context: bool = False, instruction_prompt: Optional[str] = None) -> str:
    llm_type = get_env_variable('DRAVID_LLM', 'openai').lower()
    if llm_type == 'ollama':
        raise NotImplementedError(
            "Vision API is not supported for Ollama models")

    client = get_client()
    model = get_model()

    mime_type, image_data = convert_to_base64(image_path)
    full_response = ""
    messages = [
        {"role": "system", "content": instruction_prompt or ""},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/{mime_type};base64,{image_data}"}}
            ]
        }
    ]

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=MAX_TOKENS
        )
        full_response += response.choices[0].message.content

        if response.choices[0].finish_reason != 'length':
            break

        messages.append({"role": "assistant", "content": full_response})
        messages.append({"role": "user", "content": "Please continue."})

    return parse_response(full_response)


def stream_response(query: str, instruction_prompt: Optional[str] = None) -> Generator[str, None, None]:
    llm_type = get_env_variable('DRAVID_LLM', 'openai').lower()
    model = get_model()

    if llm_type == 'ollama':
        yield from stream_ollama_response(model, query, instruction_prompt or "")
        return

    client = get_client()
    messages = [
        {"role": "system", "content": instruction_prompt or ""},
        {"role": "user", "content": query}
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=MAX_TOKENS,
        stream=True
    )

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content

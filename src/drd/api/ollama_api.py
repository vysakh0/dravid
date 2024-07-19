import requests
from typing import Dict, Any, Generator, Optional
import json

OLLAMA_ENDPOINT = "http://localhost:11434/api"


def get_ollama_client():
    # This is a placeholder function to maintain consistency with other APIs
    # Ollama doesn't require a client object, but we'll use this to set up any necessary configurations
    return None


def call_ollama_api(model: str, prompt: str, system_prompt: str = "") -> str:
    data = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    response = requests.post(f"{OLLAMA_ENDPOINT}/generate", json=data)
    response.raise_for_status()
    return response.json()["response"]


def stream_ollama_response(model: str, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
    data = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": True
    }
    response = requests.post(
        f"{OLLAMA_ENDPOINT}/generate", json=data, stream=True)
    response.raise_for_status()

    for line in response.iter_lines():
        if line:
            chunk = json.loads(line)
            if chunk.get("response"):
                yield chunk["response"]


def call_ollama_api_with_pagination(query: str, model: str, include_context: bool = False, instruction_prompt: Optional[str] = None) -> str:
    full_response = call_ollama_api(model, query, instruction_prompt or "")
    return full_response

# Note: Ollama doesn't have built-in support for image input like OpenAI.
# For vision-related tasks, we'd need to use a different approach or model.


def call_ollama_vision_api_with_pagination(query: str, image_path: str, model: str, include_context: bool = False, instruction_prompt: Optional[str] = None) -> str:
    raise NotImplementedError("Vision API is not supported for Ollama models")

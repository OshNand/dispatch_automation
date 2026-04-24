import requests
import json
from config.settings import settings

def query_llm(prompt: str, json_format: bool = False) -> str:
    """
    Sends a prompt to the local Ollama instance.
    Returns the generated text.
    """
    url = f"{settings.OLLAMA_BASE_URL}/generate"
    
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    if json_format:
        payload["format"] = "json"

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except requests.exceptions.RequestException as e:
        return f'{{"error": "Failed to connect to LLM: {str(e)}"}}'

import requests
import json
from shared.utils.config import settings
from typing import Dict, Any

class OllamaWrapper:
    def __init__(self):
        self.url = settings.OLLAMA_URL

    def generate(self, prompt: str, model: str = "llama3.2", json_mode: bool = False) -> str:
        # Ollama HTTP API: POST /api/generate with stream=False for single response
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "timeout": 120
        }
        # Use format="json" for structured outputs (tag extraction, etc.)
        if json_mode:
            payload["format"] = "json"
        
        resp = requests.post(
            f"{self.url}/api/generate",
            json=payload,
            timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns response field with generated text
        return data.get("response") or data.get("text") or str(data)

    def embed(self, texts: list, model: str = "nomic-embed-text") -> list:
        # Ollama embedding endpoint
        resp = requests.post(
            f"{self.url}/api/embed",
            json={"model": model, "input": texts},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns embeddings array
        return data.get("embeddings", [data])

import requests
import json
from shared.utils.config import settings

class OllamaLocal:
    def __init__(self, url: str = None):
        self.url = (url or settings.OLLAMA_URL).rstrip('/')

    def generate(self, prompt: str, model: str = "llama3.2") -> str:
        resp = requests.post(
            f"{self.url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns response field with generated text
        return data.get("response", "")

    def embed(self, texts: list, model: str = "nomic-embed-text") -> list:
        resp = requests.post(
            f"{self.url}/api/embed",
            json={"model": model, "input": texts},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns embeddings array
        return data.get("embeddings", [data])

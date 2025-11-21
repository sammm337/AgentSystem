from shared.utils.config import settings
from typing import List, Dict, Any
import requests
import json

class QdrantClientWrapper:
    def __init__(self, url: str = None):
        self.url = (url or settings.QDRANT_URL).rstrip('/')
        self.created_collections = set()

    def _ensure_collection(self, collection_name: str, vector_size: int = 384):
        """Create collection if it doesn't exist"""
        if collection_name in self.created_collections:
            return
        try:
            # Try to get collection info first
            resp = requests.get(f"{self.url}/collections/{collection_name}", timeout=10)
            if resp.status_code == 200:
                self.created_collections.add(collection_name)
                return
        except:
            pass
        
        # Create collection if it doesn't exist
        create_url = f"{self.url}/collections/{collection_name}"
        create_payload = {
            "vectors": {
                "size": vector_size,
                "distance": "Cosine"
            }
        }
        try:
            resp = requests.put(create_url, json=create_payload, timeout=20)
            resp.raise_for_status()
            self.created_collections.add(collection_name)
        except Exception as e:
            print(f"[Warn] Failed to create collection {collection_name}: {e}")

    def upsert(self, collection_name: str, vectors: List[Dict[str, Any]]):
        # vectors: list of {"id": str, "vector": [...], "payload": {...}}
        self._ensure_collection(collection_name, vector_size=len(vectors[0]["vector"]) if vectors else 384)
        url = f"{self.url}/collections/{collection_name}/points?wait=true"
        data = {"points": vectors}
        resp = requests.put(url, json=data, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def search(self, collection_name: str, vector: List[float], top: int = 10, filter=None):
        self._ensure_collection(collection_name, vector_size=len(vector))
        url = f"{self.url}/collections/{collection_name}/points/search"
        payload = {"vector": vector, "limit": top}
        if filter:
            payload["filter"] = filter
        resp = requests.post(url, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()

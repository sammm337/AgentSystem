# services/vector_client.py

import os
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter
from sentence_transformers import SentenceTransformer

# -----------------------------------------------------
# 1. Embedding model (local)
# -----------------------------------------------------
EMBED_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def get_embedding(text: str):
    return EMBED_MODEL.encode(text).tolist()


# -----------------------------------------------------
# 2. Initialize Qdrant client
# -----------------------------------------------------
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

qdrant = QdrantClient(url=QDRANT_URL)


# -----------------------------------------------------
# 3. COLLECTIONS
# -----------------------------------------------------
LISTINGS_COLLECTION = "travel_listings"
EVENTS_COLLECTION = "events"

# Create collections if not exist
def init_vector_collections():
    try:
        qdrant.get_collection(LISTINGS_COLLECTION)
    except:
        qdrant.create_collection(
            LISTINGS_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    try:
        qdrant.get_collection(EVENTS_COLLECTION)
    except:
        qdrant.create_collection(
            EVENTS_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )


# -----------------------------------------------------
# 4. INSERT DATA INTO QDRANT
# -----------------------------------------------------
def upsert_listing_vector(id: str, text: str, metadata: dict):
    embedding = get_embedding(text)
    qdrant.upsert(
        collection_name=LISTINGS_COLLECTION,
        points=[PointStruct(id=id, vector=embedding, payload=metadata)],
    )


def upsert_event_vector(id: str, text: str, metadata: dict):
    embedding = get_embedding(text)
    qdrant.upsert(
        collection_name=EVENTS_COLLECTION,
        points=[PointStruct(id=id, vector=embedding, payload=metadata)],
    )


# -----------------------------------------------------
# 5. SEARCH FUNCTIONS
# -----------------------------------------------------
def search_listings_vector(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    embedding = get_embedding(query)
    results = qdrant.search(
        collection_name=LISTINGS_COLLECTION,
        query_vector=embedding,
        limit=top_k,
    )
    return [r.payload for r in results]


def search_events_vector(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    embedding = get_embedding(query)
    results = qdrant.search(
        collection_name=EVENTS_COLLECTION,
        query_vector=embedding,
        limit=top_k,
    )
    return [r.payload for r in results]


# -----------------------------------------------------
# 6. INITIALIZE ON IMPORT
# -----------------------------------------------------
init_vector_collections()

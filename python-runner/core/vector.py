"""
Vector Store Manager
core/vector.py

Handles interaction with Qdrant for RAG.
"""
import os
import logging
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from core.llm import llm_client

logger = logging.getLogger(__name__)

COLLECTION_NAME = "notes"
VECTOR_SIZE = 1536 # For text-embedding-3-small

class VectorStore:
    def __init__(self):
        self._host = "qdrant" # Docker service name
        self._port = 6333
        self._client = None
        
        try:
            self._client = QdrantClient(host=self._host, port=self._port)
            self._init_collection()
            logger.info("Connected to Qdrant successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")

    def _init_collection(self):
        """Creates the collection if it doesn't exist."""
        if not self._client: return
        
        try:
            if not self._client.collection_exists(COLLECTION_NAME):
                logger.info(f"Creating collection '{COLLECTION_NAME}'...")
                self._client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=models.VectorParams(
                        size=VECTOR_SIZE,
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Collection init failed: {e}")

    def upsert_note(self, note_id: str, content: str, metadata: Dict[str, Any] = {}):
        """Generates embedding and saves to Qdrant."""
        if not self._client: return

        try:
            # 1. Generate Embedding
            embedding = self._get_embedding(content)
            if not embedding: return

            # 2. Upload Point
            self._client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=note_id, # Must be valid UUID or int
                        vector=embedding,
                        payload={
                            "content": content,
                            **metadata
                        }
                    )
                ]
            )
            logger.info(f"Note '{note_id}' vectorised.")
            
        except Exception as e:
            logger.error(f"Upsert failed: {e}")

    def search(self, query_text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Searches for relevant notes."""
        if not self._client: return []

        try:
            # 1. Embed Query
            query_vector = self._get_embedding(query_text)
            if not query_vector: return []

            # 2. Search
            # Use query_points for newer client versions
            hits = self._client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=limit
            ).points
            
            return [hit.payload for hit in hits]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Calls LLM Provider to get vector."""
        if not llm_client.is_ready(): return None
        
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        
        try:
            response = llm_client._client.embeddings.create(
                input=text,
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None

vector_store = VectorStore()

import os
from typing import List, Dict, Optional
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from dotenv import load_dotenv

load_dotenv()

_client: ClientAPI | None = None
_collection: Collection | None = None


class VectorStore:
    def __init__(self, collection_name: str = "knowledge_vault"):
        global _client, _collection

        if _client is None:
            _client = chromadb.CloudClient(
                api_key=os.getenv("CHROMA_API_KEY"),
                tenant=os.getenv("CHROMA_TENANT"),
                database=os.getenv("CHROMA_DATABASE"),
            )

        if _collection is None:
            _collection = _client.get_or_create_collection(
                name=collection_name
            )

        self.client = _client
        self.collection = _collection

    def add(
        self,
        embeddings: List[List[float]],
        metadatas: List[Dict],
        documents: List[str],
    ):
        ids = [
            f"doc_{i}"
            for i in range(
                self.collection.count(),
                self.collection.count() + len(embeddings)
            )
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

    # In vector_store.py
    def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        source_filter: Optional[str] = None,
    ) -> List[Dict]:
        
        where = None
        if source_filter:
            # Standardize the filename (remove paths/URL encoding)
            clean_name = os.path.basename(source_filter)
            where = {"source": {"$eq": clean_name}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=["metadatas", "documents", "distances"] # Explicitly ask for distances to debug
        )

        # If the first ID is empty, we found nothing
        if not results["ids"] or not results["ids"][0]:
            print(f"DEBUG: Retrieval failed for filter: {where}")
            return []

        return [
            {**meta, "text": doc}
            for meta, doc in zip(results["metadatas"][0], results["documents"][0])
        ]

import os
import uuid
from typing import List, Dict, Optional

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from dotenv import load_dotenv

load_dotenv()

_client: ClientAPI | None = None
_collections: Dict[str, Collection] = {}


class VectorStore:
    """
    Handles vector storage for Knowledge Vault.
    Supports:
    - Multi-file ingestion
    - Metadata-based filtering
    - Similarity-aware retrieval
    """

    def __init__(self, collection_name: str = "knowledge_vault_chunks"):
        global _client, _collections

        if _client is None:
            _client = chromadb.CloudClient(
                api_key=os.getenv("CHROMA_API_KEY"),
                tenant=os.getenv("CHROMA_TENANT"),
                database=os.getenv("CHROMA_DATABASE"),
            )

        if collection_name not in _collections:
            _collections[collection_name] = _client.get_or_create_collection(
                name=collection_name
            )

        self.client = _client
        self.collection = _collections[collection_name]

    def add(
        self,
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict],
    ) -> None:
        """
        Add document chunks to the vector store.
        Each chunk gets a globally unique ID.
        """

        ids = [str(uuid.uuid4()) for _ in embeddings]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        file_name: Optional[str] = None,
        similarity_threshold: Optional[float] = None,
    ) -> List[Dict]:
        """
        Search for relevant chunks.

        Args:
            query_embedding: Embedded query
            k: Top-K results
            file_name: Optional file-level filter
            similarity_threshold: Optional max distance threshold
        """

        where = None
        if file_name:
            clean_name = os.path.basename(file_name)
            where = {"file_name": {"$eq": clean_name}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        if not results["ids"] or not results["ids"][0]:
            return []

        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            if similarity_threshold is not None and dist > similarity_threshold:
                continue

            hits.append(
                {
                    "text": doc,
                    "distance": dist,
                    **meta,
                }
            )

        return hits

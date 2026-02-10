# summaries.py
from typing import List

from embeddings import embed_texts
from vector_store import VectorStore
from llm import generate_summary


class DocumentSummaryStore:
    """
    Stores and retrieves document-level summaries.
    """

    def __init__(self):
        self.store = VectorStore(collection_name="knowledge_vault_summaries")

    def add_summary(self, doc_id: str, file_name: str, full_text: str):
        summary = generate_summary(full_text)
        embedding = embed_texts([summary])[0]

        metadata = {
            "doc_id": doc_id,
            "file_name": file_name,
            "source": file_name,
        }

        self.store.add(
            embeddings=[embedding],
            documents=[summary],
            metadatas=[metadata],
        )

    # 🔹 GLOBAL SUMMARY SEARCH (SEMANTIC)
    def search(self, query_embedding, k: int = 3):
        return self.store.search(
            query_embedding=query_embedding,
            k=k,
        )

    # 🔹 FILE-SPECIFIC SUMMARY SEARCH (DETERMINISTIC)
    def search_by_file(self, file_name: str):
        """
        Retrieve summary for a specific file using metadata filtering.
        No semantic search.
        """

        results = self.store.collection.get(
            where={"file_name": {"$eq": file_name}},
            include=["documents", "metadatas"]
        )

        if not results or not results.get("documents"):
            return []

        return [
            {
                "file_name": meta["file_name"],
                "text": doc,
            }
            for doc, meta in zip(results["documents"], results["metadatas"])
        ]

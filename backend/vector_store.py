import faiss
import numpy as np
import os
import pickle

INDEX_PATH = "data/faiss_index/index.faiss"
META_PATH = "data/faiss_index/meta.pkl"


class VectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.metadata = []

        if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
            self.load()

    def add(self, embeddings, metadatas):
        embeddings = np.array(embeddings).astype("float32")

        self.index.add(embeddings)
        self.metadata.extend(metadatas)

        self.save()

    def search(self, query_embedding, k=5, source_filter=None):
        if self.index.ntotal == 0 or not self.metadata:
            return []

        query_embedding = np.array([query_embedding]).astype("float32")

        # Over-fetch to allow filtering
        search_k = min(self.index.ntotal, k * 5)

        distances, indices = self.index.search(query_embedding, search_k)

        results = []

        for idx in indices[0]:
            # 🚫 HARD SAFETY CHECK
            if idx < 0 or idx >= len(self.metadata):
                continue

            meta = self.metadata[idx]

            if source_filter:
                if not meta["source"].endswith(source_filter):
                    continue

            results.append(meta)

            if len(results) >= k:
                break

        return results

    def save(self):
        os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
        faiss.write_index(self.index, INDEX_PATH)

        with open(META_PATH, "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        self.index = faiss.read_index(INDEX_PATH)

        with open(META_PATH, "rb") as f:
            self.metadata = pickle.load(f)

        # 🚨 AUTO-HEAL: trim index if corrupted
        if self.index.ntotal != len(self.metadata):
            print(
                f"[WARN] FAISS index ({self.index.ntotal}) "
                f"and metadata ({len(self.metadata)}) out of sync. "
                f"Rebuilding index."
            )
            self.rebuild_index()

    def rebuild_index(self):
        self.index = faiss.IndexFlatL2(self.dim)

        embeddings = []
        for meta in self.metadata:
            embeddings.append(meta["embedding"])

        if embeddings:
            self.index.add(np.array(embeddings).astype("float32"))

        self.save()

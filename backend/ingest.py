import os
import uuid
from typing import List

from embeddings import embed_texts
from vector_store import VectorStore
from summaries import DocumentSummaryStore
from loaders import load_file   # ✅ NEW


# -------- TEXT CHUNKING --------
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    text = text.replace("\x00", "").strip()

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# -------- GENERIC FILE INGESTION --------
def ingest_file(path: str) -> None:
    if not os.path.exists(path):
        print(f"[ERROR] File not found: {path}")
        return

    try:
        full_text = load_file(path)   # ✅ GENERIC LOADER
    except Exception as e:
        print(f"[ERROR] Failed to read {path}: {e}")
        return

    if len(full_text.strip()) < 50:
        print(f"[WARN] {os.path.basename(path)} has very little text. Skipping.")
        return

    chunks = chunk_text(full_text)
    if not chunks:
        return

    doc_id = str(uuid.uuid4())
    file_name = os.path.basename(path)

    embeddings = embed_texts(chunks)
    store = VectorStore()

    metadatas = [
        {
            "doc_id": doc_id,
            "file_name": file_name,
            "source": file_name,
            "chunk_id": i,
        }
        for i in range(len(chunks))
    ]

    store.add(
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    summary_store = DocumentSummaryStore()
    summary_store.add_summary(
        doc_id=doc_id,
        file_name=file_name,
        full_text=full_text,
    )

    print(f"[INFO] Ingested {len(chunks)} chunks from {file_name}")


# -------- MULTI-FILE INGESTION --------
def ingest_files(paths: List[str]) -> None:
    for path in paths:
        ingest_file(path)

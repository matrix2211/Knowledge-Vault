from pypdf import PdfReader
from embeddings import embed_texts
from vector_store import VectorStore
import os


# -------- TEXT CHUNKING --------
def chunk_text(text, chunk_size=500, overlap=100):
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


# -------- PDF INGESTION --------
def ingest_pdf(path: str):
    if not os.path.exists(path):
        print(f"[ERROR] File not found: {path}")
        return

    try:
        reader = PdfReader(path)
    except Exception as e:
        print(f"[ERROR] Failed to read PDF {path}: {e}")
        return

    full_text = ""

    for page in reader.pages:
        try:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
        except Exception:
            continue

    # 🚫 HARD GUARD: scanned / junk PDFs
    if len(full_text.strip()) < 50:
        print(f"[WARN] {path} has very little extractable text. Skipping ingestion.")
        return

    chunks = chunk_text(full_text)

    if not chunks:
        print(f"[WARN] No valid chunks created for {path}")
        return

    embeddings = embed_texts(chunks)

    store = VectorStore(dim=len(embeddings[0]))

    metadatas = [
        {
            "text": chunk,
            "source": path.replace("\\", "/"),
            "embedding": emb.tolist()
        }
        for chunk, emb in zip(chunks, embeddings)
    ]   


    store.add(embeddings, metadatas)

    print(f"[INFO] Ingested {len(chunks)} chunks from {os.path.basename(path)}")

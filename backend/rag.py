from embeddings import embed_texts
from vector_store import VectorStore
from llm import generate_answer

def ask_question(question: str, file: str | None = None):
    query_embedding = embed_texts([question])[0]
    store = VectorStore(dim=len(query_embedding))

    results = store.search(
        query_embedding,
        k=6,
        source_filter=file
    )

    # 🚫 HARD GUARDRAIL
    if not results or sum(len(r["text"].strip()) for r in results) < 300:
        return {
            "answer": "I don't know. The selected file does not contain enough readable information.",
            "sources": []
        }

    context = "\n\n".join(r["text"] for r in results)

    prompt = f"""
You are a document assistant.
Answer ONLY using the provided context.
If the context does not contain the answer, say "I don't know".

Context:
{context}

Question:
{question}
"""

    answer = generate_answer(prompt)

    return {
        "answer": answer.strip(),
        "sources": list(set(r["source"].split("/")[-1] for r in results))
    }

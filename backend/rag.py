import os
from typing import Optional, Dict, Any, List
from sentence_transformers import SentenceTransformer
from vector_store import VectorStore
from llm import generate_answer
from summaries import DocumentSummaryStore

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

SIMILARITY_THRESHOLD = 1.2

summary_store = DocumentSummaryStore()

BAD_WORDS = [
    "kill", "suicide","terrorist", "bomb", "weapon", "hack"
]

def contains_bad_words(text: str) -> bool:
    text = text.lower()
    return any(bad in text for bad in BAD_WORDS)

def clean_output(answer: str) -> str:
    for bad in BAD_WORDS:
        if bad in answer.lower():
            return "The generated response was filtered for safety."
    return answer

def extract_file_reference(question: str, available_files: list[str]) -> str | None:
    q = question.lower()
    print("DEBUG available_files:", available_files)
    print("DEBUG question_lower:", q)

    for file in available_files:
        file_lower = file.lower()
        stem = os.path.splitext(file_lower)[0]  # employee_data

        if stem in q or file_lower in q:
            return file

    return None


def detect_intent(question: str) -> str:
    q = question.lower()

    if any(k in q for k in ["summary", "summarize", "overview", "summaries"]):
        return "SUMMARY"

    if any(k in q for k in ["compare", "difference", "vs"]):
        return "COMPARISON"

    if any(k in q for k in ["what files", "documents uploaded", "which files"]):
        return "META"

    if len(q.split()) < 4:
        return "VAGUE"

    return "FACTUAL"

def expand_query(question: str, summaries: list[str]) -> str:
    """
    Expand vague queries using document summaries instead of hardcoded keywords.
    """
    context_hint = " ".join(summaries[:3])  # limit to top summaries
    return f"{question}. Context: {context_hint}"


def ask_question(question: str):
    """
    Central RAG controller.
    Handles intent detection, routing, retrieval, and guardrails.
    """

    # -------- Normalize question --------
    original_question = question
    question = question.strip()
    question_lower = question.lower()

    store = VectorStore()
    print("DEBUG: Collection count =", store.collection.count())

    if contains_bad_words(question):
        return {
            "answer": "This question violates content guidelines.",
            "sources": [],
            "confidence": 0.0,
        }

    if len(question.strip()) < 3:
        return {
            "answer": "Please ask a more meaningful question.",
            "sources": [],
            "confidence": 0.0,
        }
    
    # -------- 1️⃣ Intent Detection --------
    intent = detect_intent(question_lower)

    # -------- 2️⃣ Route based on intent --------

    # 🔹 SUMMARY / OVERVIEW QUESTIONS
    if intent == "SUMMARY":
        print("DEBUG: SUMMARY intent entered")

        query_embedding = embedding_model.encode(question_lower).tolist()

        # Get list of available files from metadata
        summary_metas = summary_store.store.collection.get(include=["metadatas"])["metadatas"]

        available_files = list(
            {
                os.path.basename(meta["file_name"])
                for meta in summary_metas
                if "file_name" in meta
            }
        )

        # Detect if user asked for a specific file
        target_file = extract_file_reference(question_lower, available_files)

        # 🔹 FILE-SPECIFIC SUMMARY
        if target_file:
            summaries = summary_store.search_by_file(file_name=target_file)
            
            print("DEBUG summaries returned:", [s["file_name"] for s in summaries])

            if not summaries:
                return {
                    "answer": f"No summary available for {target_file}.",
                    "sources": [],
                    "confidence": 0.0,
                }

            context = f"[{summaries[0]['file_name']}]\n{summaries[0]['text']}"

            prompt = f"""
    Provide a concise summary of the document using ONLY the context below.

    Context:
    {context}

    Answer:
    """.strip()

            answer = generate_answer(prompt)

            return {
                "answer": answer,
                "sources": [target_file],
                "confidence": 0.95,
            }

        # 🔹 GLOBAL SUMMARY (ALL FILES)
        else:
            print("DEBUG: GLOBAL SUMMARY EXECUTED")

            summaries = summary_store.search(query_embedding, k=10)

            if not summaries:
                return {
                    "answer": "No document summaries available.",
                    "sources": [],
                    "confidence": 0.0,
                }

            context = "\n\n".join(
                f"[{s['file_name']}]\n{s['text']}"
                for s in summaries
            )

            prompt = f"""
        You are a Knowledge Vault assistant.

        List each file and provide its summary.
        Use ONLY the context below.

        Context:
        {context}

        Answer:
        """.strip()

            answer = generate_answer(prompt)
            sources = list(set(s["file_name"] for s in summaries))

            return {
                "answer": answer,
                "sources": sources,
                "confidence": 0.9,
            }


    # 🔹 META QUESTIONS (LIST DOCUMENTS)
    if intent == "META":
        files = set()
        for meta in store.collection.get(include=["metadatas"])["metadatas"]:
            files.add(meta.get("file_name"))

        if not files:
            return {
                "answer": "No documents are available in the Knowledge Vault.",
                "sources": [],
                "confidence": 0.0,
            }

        answer = "The Knowledge Vault contains the following documents:\n" + "\n".join(
            f"- {f}" for f in sorted(files)
        )

        return {
            "answer": answer,
            "sources": list(files),
            "confidence": 1.0,
        }


    # 🔹 COMPARISON QUESTIONS (SUMMARY-FIRST ROUTING)
    if intent == "COMPARISON":
        query_embedding = embedding_model.encode(question_lower).tolist()

        summaries = summary_store.search(
            query_embedding=query_embedding,
            k=5
        )

        if not summaries:
            return {
                "answer": "Not found in Knowledge Vault.",
                "sources": [],
                "confidence": 0.0,
            }

        context = "\n\n".join(
            f"[{s['file_name']}]\n{s['text']}"
            for s in summaries
        )

        prompt = f"""
    Compare the concepts using ONLY the context below.
    Highlight similarities and differences clearly.

    Context:
    {context}

    Question:
    {original_question}

    Answer:
    """.strip()

        answer = generate_answer(prompt)
        sources = list(set(s["file_name"] for s in summaries))

        return {
            "answer": answer,
            "sources": sources,
            "confidence": 0.85,
        }

    # 🔹 VAGUE QUESTIONS (AUTO QUERY EXPANSION)
    if intent == "VAGUE":
        summary_hits = summary_store.search(
        query_embedding=embedding_model.encode(question_lower).tolist(),
        k=3
        )
        if summary_hits:
            summaries_text = [s["text"] for s in summary_hits]
            question = expand_query(question, summaries_text)

    # -------- 3️⃣ FACTUAL / DEFAULT RAG --------
    query_embedding = embedding_model.encode(question).tolist()

    results = store.search(
        query_embedding=query_embedding,
        k=5,
        similarity_threshold=SIMILARITY_THRESHOLD,
    )

    # -------- Guardrail --------
    if not results:
        return {
            "answer": "Not found in Knowledge Vault.",
            "sources": [],
            "confidence": 0.0,
        }

    # -------- Context Construction --------
    context = "\n\n".join(
        f"[{r['file_name']}] {r['text']}"
        for r in results
    )

    prompt = f"""
Answer ONLY using the context below.
If the answer is not present, say "Not found in Knowledge Vault."

Context:
{context}

Question:
{original_question}

Answer:
""".strip()

    answer = generate_answer(prompt)

    sources = list(set(r["file_name"] for r in results))
    confidence = round(
        max(0.0, 1 - sum(r["distance"] for r in results) / len(results)),
        2
    )

    answer = clean_output(answer)
    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
    }
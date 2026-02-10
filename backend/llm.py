import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _call_gemini(prompt: str) -> str:
    """
    Internal Gemini call with safety fallback.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )

        if response and response.text:
            return response.text.strip()

        return "Not found in Knowledge Vault."

    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return "Not found in Knowledge Vault."


def generate_answer(prompt: str) -> str:
    """
    Generate a grounded answer for RAG.
    """
    return _call_gemini(prompt)


def generate_summary(text: str) -> str:
    """
    Generate a concise document summary.
    Used for document-level retrieval.
    """
    prompt = f"""
Summarize the following document content in 5–7 bullet points.
Focus on key topics and definitions.
Do NOT add information not present in the text.

Document:
----------------
{text}
----------------

Summary:
""".strip()

    return _call_gemini(prompt)

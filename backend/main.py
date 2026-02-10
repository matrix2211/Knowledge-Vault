from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ingest import ingest_files
from rag import ask_question
import shutil
import os
from typing import Optional

app = FastAPI(title="Knowledge Vault API")

# ✅ CORS (DEV ONLY — restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOCS_DIR = "data/documents"
os.makedirs(DOCS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".csv"}

@app.get("/")
def root():
    return {"status": "Knowledge Vault API running"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Basic validation

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    path = os.path.join(DOCS_DIR, file.filename)

    try:
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    ingest_files([path])

    return {
        "status": "uploaded and indexed",
        "filename": file.filename
    }


@app.get("/ask")
def ask(q: str):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    return ask_question(q)


@app.get("/files")
def list_files():
    if not os.path.exists(DOCS_DIR):
        return []

    return [
        f for f in os.listdir(DOCS_DIR)
        if os.path.isfile(os.path.join(DOCS_DIR, f))
        and os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
    ]


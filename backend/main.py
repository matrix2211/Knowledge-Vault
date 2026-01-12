from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from ingest import ingest_pdf
from rag import ask_question
import shutil
import os

app = FastAPI()

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOCS_DIR = "data/documents"
os.makedirs(DOCS_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"status": "Knowledge Vault API running"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    path = os.path.join(DOCS_DIR, file.filename)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    ingest_pdf(path)
    return {"status": "uploaded and indexed"}

@app.get("/ask")
def ask(q: str, file: str | None = None):
    return ask_question(q, file)


@app.get("/files")
def list_files():
    if not os.path.exists(DOCS_DIR):
        return []

    return [
        f for f in os.listdir(DOCS_DIR)
        if os.path.isfile(os.path.join(DOCS_DIR, f))
    ]

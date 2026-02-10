import os
import pandas as pd
from docx import Document
from pypdf import PdfReader


def load_pdf(path: str) -> str:
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text


def load_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def load_excel(path: str) -> str:
    sheets = pd.read_excel(path, sheet_name=None)
    text = ""
    for sheet_name, df in sheets.items():
        text += f"\nSheet: {sheet_name}\n"
        text += df.astype(str).to_string(index=False)
    return text


def load_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return load_pdf(path)
    if ext == ".docx":
        return load_docx(path)
    if ext in [".xlsx", ".xls"]:
        return load_excel(path)

    raise ValueError(f"Unsupported file type: {ext}")

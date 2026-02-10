# 📚 Knowledge Vault — RAG-Powered Document Q&A

A **Retrieval-Augmented Generation (RAG) application** that allows users to upload documents and ask questions **strictly grounded in their content**. This has been updated was previously a local application running on **LLaMA** but now on **Google Gemini**.

Built with **FastAPI + ChromaDB (Cloud) + Google Gemini**, this project focuses on **correct RAG architecture, file-scoped retrieval, and production-grade guardrails** — not just a toy demo.

---

## ✨ Features

- 📂 Upload and manage multiple PDF documents  
- 🔍 Ask natural language questions grounded **only in selected files**  
- 🧠 Retrieval-Augmented Generation (RAG) using vector similarity search  
- 🗂️ File-scoped querying (no cross-document leakage)  
- 🧾 Source attribution per answer  
- 🚫 Hallucination guardrails for weak or unreadable PDFs  
- 💬 ChatGPT-style UI (sidebar + chat + fixed input)  
- ☁️ Cloud-backed vector storage using **ChromaDB Cloud**

---

## 🏗️ Architecture Overview

```text
Frontend (HTML / CSS / JS)
↓
FastAPI Backend
↓
Google Gemini Embeddings (embedding-001)
↓
ChromaDB Cloud (Vector Store)
↓
Google Gemini LLM (gemini-pro)

```

### RAG Flow
1. User uploads a PDF
2. Text is extracted, chunked, embedded
3. Embeddings + metadata stored in ChromaDB Cloud
4. User selects a file + asks a question
5. Retrieval happens **only within that file**
6. Gemini generates an answer strictly from retrieved context

---

## 📁 Project Structure

```text

backend/
├── embeddings.py
├── ingest.py
├── llm.py
├── main.py
├── rag.py
├── vector_store.py
└── init.py

frontend/
├── index.html
├── style.css
└── app.js

requirements.txt
README.md

```

## Website UI Preview

![ui](images/ui2.png)

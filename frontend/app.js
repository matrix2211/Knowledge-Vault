const API_BASE = "http://127.0.0.1:8000";

// DOM refs
const chatContainer = document.getElementById("chatContainer");
const questionInput = document.getElementById("questionInput");
const uploadStatus = document.getElementById("uploadStatus");
const fileList = document.getElementById("fileList");

/* -----------------------------
   FILE SIDEBAR (READ-ONLY)
--------------------------------*/

async function fetchFiles() {
  try {
    const res = await fetch(`${API_BASE}/files`);
    const files = await res.json();
    renderFiles(files);
  } catch {
    fileList.innerHTML = `<div class="file muted">Failed to load files</div>`;
  }
}

function renderFiles(files) {
  fileList.innerHTML = "";

  if (!files.length) {
    fileList.innerHTML = `<div class="file muted">No files uploaded</div>`;
    return;
  }

  files.forEach((file) => {
    const div = document.createElement("div");
    div.className = "file";
    div.textContent = file;
    fileList.appendChild(div);
  });
}

/* -----------------------------
   UPLOAD (MULTI-FILE READY)
--------------------------------*/

async function uploadFile() {
  const fileInput = document.getElementById("fileInput");
  if (!fileInput.files.length) return;

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  uploadStatus.textContent = "Uploading & indexing...";

  try {
    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    if (!res.ok) {
      uploadStatus.textContent = "Upload failed";
      return;
    }


    await fetchFiles();
  } catch {
    uploadStatus.textContent = "Upload failed";
  }
}

/* -----------------------------
   CHAT (GLOBAL SEARCH)
--------------------------------*/

function addMessage(text, type, sources = []) {
  const msg = document.createElement("div");
  msg.className = `message ${type}`;
  msg.textContent = text;

  if (sources.length) {
    const src = document.createElement("div");
    src.className = "sources";
    src.textContent = "Sources: " + sources.join(", ");
    msg.appendChild(src);
  }

  chatContainer.appendChild(msg);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function askQuestion() {
  const q = questionInput.value.trim();
  if (!q) return;

  addMessage(q, "user");
  questionInput.value = "";

  const thinking = document.createElement("div");
  thinking.className = "message ai";
  thinking.textContent = "Thinking...";
  chatContainer.appendChild(thinking);

  try {
    const url = `${API_BASE}/ask?q=${encodeURIComponent(q)}`;

    const res = await fetch(url);
    const data = await res.json();

    chatContainer.removeChild(thinking);
    addMessage(data.answer, "ai", data.sources || []);
  } catch {
    chatContainer.removeChild(thinking);
    addMessage("Error contacting server.", "ai");
  }
}

function handleEnter(e) {
  if (e.key === "Enter") askQuestion();
}

/* -----------------------------
   INIT
--------------------------------*/

fetchFiles();

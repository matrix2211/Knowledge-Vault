const API_BASE = "http://127.0.0.1:8000";

// DOM refs
const chatContainer = document.getElementById("chatContainer");
const questionInput = document.getElementById("questionInput");
const uploadStatus = document.getElementById("uploadStatus");
const fileList = document.getElementById("fileList");
const selectedFileBar = document.querySelector(
  "#selectedFileBar .file-name"
);


let selectedFile = null;

/* -----------------------------
   FILE SIDEBAR
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

  files.forEach(file => {
    const div = document.createElement("div");
    div.className = "file";
    div.textContent = file;

    if (file === selectedFile) {
      div.classList.add("active");
    }

    div.onclick = () => {
        selectedFile = file;
        selectedFileBar.textContent = file;   // ✅ update top bar
        renderFiles(files);
    };


    fileList.appendChild(div);
  });
}

/* -----------------------------
   UPLOAD
--------------------------------*/

async function uploadFile() {
  const fileInput = document.getElementById("fileInput");
  if (!fileInput.files.length) return;

  const uploadedFileName = fileInput.files[0].name;

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  uploadStatus.textContent = "Uploading & indexing...";

  try {
    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    uploadStatus.textContent = data.status || "Uploaded";

    // ✅ auto-select uploaded file
    selectedFile = uploadedFileName;
    selectedFileBar.textContent = uploadedFileName;
    await fetchFiles();
  } catch {
    uploadStatus.textContent = "Upload failed";
  }
}

/* -----------------------------
   CHAT
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
    let url = `${API_BASE}/ask?q=${encodeURIComponent(q)}`;
    if (selectedFile) {
      url += `&file=${encodeURIComponent(selectedFile)}`;
    }

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

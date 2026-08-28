# 📚 RAG Chatbot – PDF Question Answering System

An enterprise-grade, fully functional academic project implementing **Retrieval-Augmented Generation (RAG)** to answer natural language questions strictly from uploaded PDF documents using **LangChain**, **FAISS Vector Store**, **Sentence Transformers**, and local **Ollama LLM** (`llama3.1:8b`).

---

## 🌟 Key Features

- 📑 **Multi-PDF Drag & Drop Ingestion**: Upload single or multiple research papers, technical manuals, or corporate guidelines with real-time text extraction and validation.
- ✂️ **Recursive Text Chunking**: Intelligent splitting using LangChain `RecursiveCharacterTextSplitter` (1000 characters, 200 overlap) preserving page and document metadata.
- 🔍 **FAISS Vector Indexing**: High-performance semantic vector database using `all-MiniLM-L6-v2` embeddings with on-disk index persistence.
- 🛡️ **Anti-Hallucination Prompting**: Strict system prompt enforcing responses solely from retrieved context. If absent, explicitly indicates *"The requested information was not found in the uploaded documents."*
- 🏷️ **Verified Source Citations**: Every answer displays the exact source PDF filename, page number, and similarity score snippet.
- 💬 **Multi-Conversation Management**: Create, switch, clear, and delete chat threads persisted in SQLite.
- 📊 **Executive Analytics Dashboard**: Live counters for total documents, pages, chunks, queries, and conversations.
- 🩺 **System Diagnostics & Health Check**: Real-time monitoring of FAISS vector status, embedding dimensions, database health, and Ollama connectivity.
- 🚀 **Smart Offline Demo Fallback**: Built-in heuristic RAG engine ensuring seamless demonstration even without an active GPU or Ollama server.

---

## 🏗️ System Architecture

```
User Uploads PDF
       ↓
PDF Text Extraction (pypdf)
       ↓
Text Cleaning & Metadata Tagging (Page numbers & Document IDs)
       ↓
Recursive Character Chunking (1000 size, 200 overlap)
       ↓
Vector Embedding Generation (Sentence Transformers: all-MiniLM-L6-v2)
       ↓
FAISS Vector Store (Disk Persistence)
       ↓
User Asks Question
       ↓
Similarity Search in FAISS (Top-K Chunks)
       ↓
LangChain RAG Pipeline (Anti-Hallucination Prompt + Retrieved Context)
       ↓
Ollama LLM (llama3.1:8b) / Smart Demo Engine
       ↓
Grounded Answer + Page Citations + SQLite Persistence
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Python 3.10+, Flask 3.0 |
| **RAG Orchestration** | LangChain, LangChain Community |
| **Vector Database** | FAISS (`faiss-cpu`) |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) |
| **Local LLM** | Ollama (`llama3.1:8b`) |
| **Relational Database** | SQLite, SQLAlchemy (Flask-SQLAlchemy) |
| **PDF Parsing** | `pypdf` |
| **Frontend UI** | HTML5, CSS3 (Custom Glassmorphism), JavaScript, Bootstrap 5 |
| **Testing** | Pytest |

---

## 📂 Project Structure

```
Rag_chatbot/
├── app.py                      # Flask application factory and runner
├── config.py                   # Centralized configuration and environment settings
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment variables
├── .gitignore                  # Git ignore rules
├── README.md                   # Comprehensive project documentation
├── database/
│   ├── __init__.py             # SQLAlchemy instance
│   ├── models.py               # Document, Conversation, and Message models
│   └── seed.py                 # Initial database seeding with sample ML paper
├── services/
│   ├── __init__.py
│   ├── pdf_service.py          # PDF text extraction and validation
│   ├── chunking_service.py     # Recursive text splitter
│   ├── embedding_service.py    # Sentence Transformers embedding manager
│   ├── vector_store.py         # FAISS vector store manager (create, search, persist)
│   ├── llm_service.py          # Ollama integration & smart demo engine
│   ├── rag_service.py          # LangChain RAG pipeline & prompt template
│   └── health_service.py       # Live diagnostics for DB, FAISS, LLM
├── routes/
│   ├── __init__.py
│   ├── api.py                  # REST API endpoints (/api/documents, /api/chat, etc.)
│   └── views.py                # Web page routes (Dashboard, Chat, Documents, Health)
├── templates/
│   ├── base.html               # Base template with responsive sidebar and navbar
│   ├── dashboard.html          # Stats and quick upload dashboard
│   ├── chat.html               # Real-time RAG chatbot interface
│   ├── documents.html          # Document management interface
│   └── health.html             # System diagnostics interface
├── static/
│   ├── css/
│   │   └── style.css           # Modern SaaS stylesheet
│   └── js/
│       ├── app.js              # Global utilities and markdown parser
│       ├── chat.js             # Chat client logic and source rendering
│       └── documents.js        # Drag-and-drop file upload handler
├── tests/
│   ├── __init__.py
│   ├── test_pdf_processing.py  # Tests for PDF parsing and chunking
│   ├── test_vector_store.py    # Tests for FAISS indexing and retrieval
│   ├── test_rag_pipeline.py    # Tests for RAG answers and anti-hallucination
│   └── test_api.py             # Integration tests for REST APIs
└── instance/
    ├── uploads/                # Uploaded PDF storage
    ├── faiss_index/            # Persisted FAISS vector index
    └── rag_chatbot.db          # SQLite database
```

---

## ⚡ Quick Start & Installation

### 1. Prerequisites
- Python 3.10 or higher
- Optional: [Ollama](https://ollama.ai) installed with `llama3.1:8b` model

### 2. Setup Virtual Environment
```powershell
# Navigate to the project directory
cd "d:\DIGICOMPETE ASSIGN\Rag_chatbot"

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 3. (Optional) Setup Ollama LLM
If you want to use the live Ollama LLM:
```powershell
# Pull and start llama3.1:8b
ollama run llama3.1:8b
```
*(Note: If Ollama is not running, the application automatically activates **Smart Demo Mode** for testing.)*

### 4. Run the Application
```powershell
python app.py
```
Open your browser and navigate to: **[http://127.0.0.1:5001](http://127.0.0.1:5001)**

---

## 🧪 Running Automated Tests

Run the complete pytest suite to verify document extraction, FAISS vector search, and API endpoints:
```powershell
pytest tests/ -v
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/documents` | `GET` | Retrieve list of all indexed documents |
| `/api/upload` | `POST` | Upload and vectorize single/multiple PDF files |
| `/api/documents/<id>` | `DELETE` | Delete a document and rebuild FAISS index |
| `/api/documents/<id>/reprocess` | `POST` | Re-extract and re-index an existing document |
| `/api/chat` | `POST` | Ask a question and receive grounded RAG answer + citations |
| `/api/conversations` | `GET` | Retrieve list of all chat sessions |
| `/api/conversations/<id>` | `GET` | Retrieve full message history of a chat session |
| `/api/conversations/<id>` | `DELETE` | Delete a chat session |
| `/api/dashboard/stats` | `GET` | Retrieve aggregated counters and recent questions |
| `/api/health` | `GET` | Retrieve component status for FAISS, DB, Embeddings, LLM |

---

## 👨‍💻 Author & Attribution

- **Developed by**: Shashank S C
- **Project**: MCA / Academic Capstone – RAG Chatbot PDF Question Answering System
- **Year**: 2026

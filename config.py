import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'rag_chatbot_super_secret_key_2026'
    
    # Base and Storage Directories
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    UPLOAD_FOLDER = os.path.join(INSTANCE_DIR, 'uploads')
    FAISS_INDEX_DIR = os.path.join(INSTANCE_DIR, 'faiss_index')
    
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    
    # SQLite Database Configuration (Normalized for Windows)
    db_path = os.path.join(INSTANCE_DIR, 'rag_chatbot.db').replace('\\', '/')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload Limits
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # RAG Chunking Parameters
    CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', 1000))
    CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', 200))
    TOP_K_RESULTS = int(os.environ.get('TOP_K_RESULTS', 4))
    
    # Embedding Model
    EMBEDDING_MODEL_NAME = os.environ.get('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')
    
    # Ollama LLM Configuration
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b')
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Demo / Fallback Mode (Defaults to True for instant testing)
    DEMO_MODE = os.environ.get('DEMO_MODE', 'true').lower() in ['true', '1', 'yes', 't']

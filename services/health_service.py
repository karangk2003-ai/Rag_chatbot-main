import os
from database import db
from database.models import Document
from services.vector_store import VectorStoreService
from services.llm_service import LLMService
from services.embedding_service import EmbeddingService
from config import Config

class HealthService:
    @classmethod
    def get_system_health(cls):
        """Checks status of all system components"""
        # 1. Database
        db_status = "Healthy"
        db_error = None
        doc_count = 0
        try:
            doc_count = Document.query.count()
        except Exception as e:
            db_status = "Error"
            db_error = str(e)

        # 2. FAISS Vector Store
        vector_stats = VectorStoreService.get_stats()

        # 3. Embedding Model
        embeddings_status = "Ready"
        try:
            EmbeddingService.get_embeddings()
        except Exception as e:
            embeddings_status = f"Error: {e}"

        # 4. Ollama LLM
        ollama_connected = LLMService.is_ollama_available()
        ollama_status = "Connected" if ollama_connected else "Offline (Demo Fallback Active)"

        return {
            "overall_status": "Operational" if db_status == "Healthy" else "Degraded",
            "database": {
                "status": db_status,
                "type": "SQLite / SQLAlchemy",
                "document_count": doc_count,
                "error": db_error
            },
            "vector_store": {
                "engine": "FAISS (CPU)",
                "status": vector_stats.get("status"),
                "total_vectors": vector_stats.get("total_vectors"),
                "dimension": vector_stats.get("dimension")
            },
            "embedding_model": {
                "name": Config.EMBEDDING_MODEL_NAME,
                "status": embeddings_status,
                "dimension": 384
            },
            "llm": {
                "provider": "Ollama (Local)" if not Config.DEMO_MODE else "Smart Demo RAG Engine",
                "model": Config.OLLAMA_MODEL,
                "endpoint": Config.OLLAMA_BASE_URL,
                "status": ollama_status,
                "demo_mode": Config.DEMO_MODE
            }
        }

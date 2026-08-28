import os
import shutil
from langchain_community.vectorstores import FAISS
from services.embedding_service import EmbeddingService
from config import Config

class VectorStoreService:
    _instance = None

    @classmethod
    def get_index_path(cls):
        return Config.FAISS_INDEX_DIR

    @classmethod
    def load_index(cls):
        """Loads FAISS index from disk if present"""
        index_dir = cls.get_index_path()
        index_file = os.path.join(index_dir, "index.faiss")
        if os.path.exists(index_file):
            try:
                embeddings = EmbeddingService.get_embeddings()
                return FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                print(f"[VectorStoreService] Error loading FAISS index: {e}")
                return None
        return None

    @classmethod
    def add_chunks(cls, chunks):
        """
        Adds a list of LangChain Document chunks into FAISS vector store.
        Persists index immediately to disk.
        """
        if not chunks:
            return None

        embeddings = EmbeddingService.get_embeddings()
        vector_store = cls.load_index()

        if vector_store is None:
            vector_store = FAISS.from_documents(chunks, embeddings)
        else:
            vector_store.add_documents(chunks)

        vector_store.save_local(cls.get_index_path())
        return vector_store

    @classmethod
    def search(cls, query, k=None, filter_doc_ids=None):
        """
        Performs similarity search with relevance scores.
        Returns: list of (doc, score) tuples
        """
        k = k or Config.TOP_K_RESULTS
        vector_store = cls.load_index()
        if vector_store is None:
            return []

        try:
            # LangChain FAISS returns L2 distance (lower = closer)
            results_with_scores = vector_store.similarity_search_with_score(query, k=k*2)
            
            filtered_results = []
            for doc, score in results_with_scores:
                # Optional filtering by document_id
                if filter_doc_ids and doc.metadata.get("document_id") not in filter_doc_ids:
                    continue
                filtered_results.append((doc, float(score)))
                if len(filtered_results) >= k:
                    break

            return filtered_results
        except Exception as e:
            print(f"[VectorStoreService] Similarity search error: {e}")
            return []

    @classmethod
    def clear_index(cls):
        """Removes the FAISS index files on disk"""
        index_dir = cls.get_index_path()
        if os.path.exists(index_dir):
            for file_name in os.listdir(index_dir):
                file_path = os.path.join(index_dir, file_name)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"[VectorStoreService] Failed to delete {file_path}: {e}")

    @classmethod
    def rebuild_index(cls, all_chunks):
        """Clears index and rebuilds freshly from all active chunks"""
        cls.clear_index()
        if all_chunks:
            return cls.add_chunks(all_chunks)
        return None

    @classmethod
    def get_stats(cls):
        """Returns metadata stats about the current vector index"""
        index = cls.load_index()
        if index is None:
            return {
                "status": "Not Initialized",
                "total_vectors": 0,
                "dimension": 384,
                "path": cls.get_index_path()
            }
        try:
            total = index.index.ntotal
            dim = index.index.d
            return {
                "status": "Ready",
                "total_vectors": total,
                "dimension": dim,
                "path": cls.get_index_path()
            }
        except Exception:
            return {
                "status": "Ready",
                "total_vectors": "Active",
                "dimension": 384,
                "path": cls.get_index_path()
            }

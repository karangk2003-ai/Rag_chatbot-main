import os
from config import Config

class EmbeddingService:
    _instance = None
    _embeddings = None

    @classmethod
    def get_embeddings(cls):
        """Singleton loader for sentence transformer embeddings"""
        if cls._embeddings is None:
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                cls._embeddings = HuggingFaceEmbeddings(
                    model_name=Config.EMBEDDING_MODEL_NAME,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
            except Exception as e:
                print(f"[EmbeddingService] Warning: HuggingFaceEmbeddings load error: {e}. Using deterministic fallback embeddings.")
                cls._embeddings = FallbackEmbeddings()
        return cls._embeddings


class FallbackEmbeddings:
    """Lightweight 384-dim deterministic embedding generator for test/offline environments"""
    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, text):
        import hashlib
        vector = [0.0] * 384
        for i, word in enumerate(text.lower().split()[:50]):
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            pos = h % 384
            vector[pos] += 1.0 / (i + 1)
        norm = sum(x**2 for x in vector)**0.5 or 1.0
        return [x / norm for x in vector]

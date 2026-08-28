import requests
import json
import re
from config import Config

class LLMService:
    @classmethod
    def is_ollama_available(cls):
        """Checks if local Ollama server is reachable"""
        try:
            res = requests.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=2)
            return res.status_code == 200
        except Exception:
            return False

    @classmethod
    def generate_response(cls, prompt, context_chunks=None, question=None):
        """
        Sends the RAG prompt to Ollama LLM, with fallback to local heuristic RAG engine
        if Ollama is offline or DEMO_MODE is True.
        """
        if not Config.DEMO_MODE and cls.is_ollama_available():
            try:
                payload = {
                    "model": Config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.9
                    }
                }
                res = requests.post(
                    f"{Config.OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                    timeout=45
                )
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("response", "").strip()
                    if answer:
                        return answer
            except Exception as e:
                print(f"[LLMService] Ollama invocation error: {e}. Falling back to Smart Demo Engine.")

        # Smart Anti-Hallucination Demo Engine
        return cls._generate_smart_demo_rag_answer(context_chunks or [], question or "")

    @classmethod
    def _generate_smart_demo_rag_answer(cls, context_chunks, question):
        """
        Generates grounded, anti-hallucination answers from retrieved chunks
        using lexical and semantic extraction.
        """
        if not context_chunks:
            return "The requested information was not found in the uploaded documents."

        q_clean = question.lower().strip()
        stop_words = {
            "what", "is", "the", "are", "explain", "how", "in", "of", "to", "and", "a", "an", "this", "that",
            "tell", "me", "about", "summarize", "describe", "which", "discuss", "mentioned", "document", "pdf",
            "for", "from", "with", "by", "on", "at", "as", "or", "if", "can", "could", "should", "would", "do", "does", "did"
        }
        q_tokens = [w for w in re.findall(r'\b\w+\b', q_clean) if w not in stop_words and len(w) > 2]

        all_text = " ".join([doc.page_content for doc, _ in context_chunks])
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', all_text) if len(s.strip()) > 15]

        # Score sentences against question tokens using whole word matching
        scored_sentences = []
        for s in sentences:
            s_lower = s.lower()
            match_count = sum(1 for tok in q_tokens if re.search(r'\b' + re.escape(tok), s_lower))
            if match_count > 0:
                scored_sentences.append((match_count, s))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)

        # Check if question is asking for summary
        if any(term in q_clean for term in ["summarize", "summary", "overview", "main point"]):
            top_excerpts = [s for _, s in scored_sentences[:4]] if scored_sentences else sentences[:4]
            if top_excerpts:
                formatted_points = "\n".join([f"- {s}" for s in top_excerpts])
                return f"### Summary Based on Uploaded Documents\n\nBased on the retrieved sections from your document, here are the key highlights:\n\n{formatted_points}\n\n*All information is extracted directly from the verified source pages.*"

        # Check if no matching content found
        if not scored_sentences and q_tokens:
            return "The requested information was not found in the uploaded documents. Please verify if the uploaded PDF contains details related to your query."

        # Compile matching answer points
        best_sentences = [s for _, s in scored_sentences[:5]]
        formatted_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(best_sentences)])

        # Construct polished answer
        answer = f"Based on the uploaded documents, here is the relevant information addressing your question:\n\n{formatted_list}"
        return answer

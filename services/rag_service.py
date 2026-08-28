from langchain.prompts import PromptTemplate
from services.vector_store import VectorStoreService
from services.llm_service import LLMService
from config import Config

RAG_PROMPT_TEMPLATE = """You are an expert Academic AI Research Assistant specializing in PDF document question answering.

Your goal is to provide accurate, comprehensive, and grounded answers strictly and solely based on the retrieved context below.

RULES:
1. Rely strictly on the information in the provided Context.
2. If the answer cannot be determined or is not contained within the Context, respond explicitly with: "The requested information was not found in the uploaded documents." Do not speculate or invent facts.
3. Cite the relevant document and page number whenever discussing specific findings.
4. Structure your response clearly using bullet points, numbered lists, or concise paragraphs.

Context:
{context}

User Question:
{question}

Answer:"""

class RAGService:
    @classmethod
    def answer_question(cls, question, filter_doc_ids=None, top_k=None):
        """
        Executes full RAG workflow:
        1. Query similarity search in FAISS vector store
        2. Format retrieved context chunks
        3. Construct anti-hallucination prompt
        4. Query LLM / Demo engine
        5. Extract source citations with page numbers
        """
        top_k = top_k or Config.TOP_K_RESULTS
        
        # 1. Similarity search
        retrieved_results = VectorStoreService.search(
            query=question,
            k=top_k,
            filter_doc_ids=filter_doc_ids
        )

        if not retrieved_results:
            return {
                "answer": "The requested information was not found in the uploaded documents. Please ensure documents have been uploaded and processed.",
                "sources": [],
                "chunks_used": 0
            }

        # 2. Format Context and collect Sources
        context_parts = []
        sources = []
        seen_sources = set()

        for idx, (doc, score) in enumerate(retrieved_results, start=1):
            source_name = doc.metadata.get("source", "Document.pdf")
            page_num = doc.metadata.get("page", 1)
            content = doc.page_content.strip()

            context_parts.append(f"--- [Document: {source_name} | Page: {page_num}] ---\n{content}")

            source_key = f"{source_name}_p{page_num}"
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                # Create a concise snippet
                snippet = content[:220].replace('\n', ' ') + ("..." if len(content) > 220 else "")
                sources.append({
                    "filename": source_name,
                    "page": page_num,
                    "snippet": snippet,
                    "score": round(score, 3)
                })

        formatted_context = "\n\n".join(context_parts)

        # 3. Construct Prompt
        prompt = RAG_PROMPT_TEMPLATE.format(
            context=formatted_context,
            question=question
        )

        # 4. Generate Answer via LLM
        answer = LLMService.generate_response(
            prompt=prompt,
            context_chunks=retrieved_results,
            question=question
        )

        return {
            "answer": answer,
            "sources": sources,
            "chunks_used": len(retrieved_results)
        }

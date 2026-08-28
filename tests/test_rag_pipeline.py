import pytest
from langchain.docstore.document import Document as LangChainDocument
from services.rag_service import RAGService
from services.vector_store import VectorStoreService

@pytest.fixture(autouse=True)
def setup_rag_index():
    chunks = [
        LangChainDocument(
            page_content="The key advantages of deep learning are automatic feature extraction and high scalability with compute clusters.",
            metadata={"document_id": 1, "source": "paper.pdf", "page": 2}
        ),
        LangChainDocument(
            page_content="Supervised learning algorithms include Support Vector Machines, Random Forests, and XGBoost.",
            metadata={"document_id": 1, "source": "paper.pdf", "page": 1}
        )
    ]
    VectorStoreService.rebuild_index(chunks)

def test_rag_service_valid_query():
    result = RAGService.answer_question("What are the advantages of deep learning?")
    assert "answer" in result
    assert "sources" in result
    assert result["chunks_used"] > 0
    assert len(result["sources"]) > 0
    assert result["sources"][0]["filename"] == "paper.pdf"

def test_rag_service_anti_hallucination():
    result = RAGService.answer_question("What is the recipe for chocolate chip cookies in this document?")
    assert "not found in the uploaded documents" in result["answer"].lower()

import pytest
from langchain.docstore.document import Document as LangChainDocument
from services.vector_store import VectorStoreService

def test_vector_store_add_and_search():
    chunks = [
        LangChainDocument(
            page_content="Supervised learning uses labeled training examples such as classification and regression.",
            metadata={"document_id": 1, "source": "ml.pdf", "page": 1}
        ),
        LangChainDocument(
            page_content="Convolutional Neural Networks are designed for 2D spatial image data.",
            metadata={"document_id": 1, "source": "ml.pdf", "page": 2}
        ),
        LangChainDocument(
            page_content="Database normalization minimizes data redundancy in relational systems.",
            metadata={"document_id": 2, "source": "db.pdf", "page": 1}
        )
    ]
    
    VectorStoreService.rebuild_index(chunks)
    
    # Query for machine learning
    results = VectorStoreService.search("What is supervised learning?", k=2)
    assert len(results) > 0
    top_doc, score = results[0]
    assert "supervised learning" in top_doc.page_content.lower() or "neural" in top_doc.page_content.lower()

def test_vector_store_filtering():
    # Filter by doc_id 2 only
    results = VectorStoreService.search("Tell me about database normalization", k=2, filter_doc_ids=[2])
    assert len(results) > 0
    for doc, _ in results:
        assert doc.metadata["document_id"] == 2

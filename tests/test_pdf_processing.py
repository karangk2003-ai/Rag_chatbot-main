import os
import pytest
from services.pdf_service import PDFService
from services.chunking_service import ChunkingService
from database.seed import generate_minimal_pdf

@pytest.fixture
def sample_pdf_path(tmp_path):
    pdf_file = tmp_path / "test_document.pdf"
    pages = [
        "Page 1: Artificial Intelligence and Machine Learning paradigms overview.",
        "Page 2: Deep Learning uses multiple layers of neural networks for representation learning.",
        "Page 3: Limitations include high computational complexity and data hunger."
    ]
    generate_minimal_pdf(str(pdf_file), pages)
    return str(pdf_file)

def test_pdf_allowed_file():
    assert PDFService.is_allowed_file("document.pdf") is True
    assert PDFService.is_allowed_file("DOCUMENT.PDF") is True
    assert PDFService.is_allowed_file("document.docx") is False
    assert PDFService.is_allowed_file("script.py") is False

def test_pdf_extraction(sample_pdf_path):
    total_pages, pages_data = PDFService.extract_from_filepath(
        sample_pdf_path,
        document_id=1,
        filename="test_document.pdf"
    )
    assert total_pages == 3
    assert len(pages_data) == 3
    assert "Artificial Intelligence" in pages_data[0]["text"]
    assert pages_data[0]["page_number"] == 1
    assert pages_data[1]["page_number"] == 2

def test_chunking_service(sample_pdf_path):
    total_pages, pages_data = PDFService.extract_from_filepath(
        sample_pdf_path,
        document_id=1,
        filename="test_document.pdf"
    )
    chunker = ChunkingService(chunk_size=100, chunk_overlap=20)
    chunks = chunker.split_pages_into_chunks(pages_data)
    
    assert len(chunks) >= 3
    assert hasattr(chunks[0], "page_content")
    assert hasattr(chunks[0], "metadata")
    assert chunks[0].metadata["document_id"] == 1
    assert "source" in chunks[0].metadata

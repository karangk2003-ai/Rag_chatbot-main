from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangChainDocument
from config import Config

class ChunkingService:
    def __init__(self, chunk_size=None, chunk_overlap=None):
        self.chunk_size = chunk_size or Config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def split_pages_into_chunks(self, pages_data):
        """
        Takes a list of page dicts: [{"page_number": 1, "text": "...", "source": "paper.pdf", "document_id": 1}]
        Returns a list of LangChain Document objects with rich metadata.
        """
        chunks = []
        for page in pages_data:
            text = page.get("text", "")
            if not text:
                continue

            page_chunks = self.splitter.split_text(text)
            for chunk_idx, chunk_text in enumerate(page_chunks):
                doc = LangChainDocument(
                    page_content=chunk_text,
                    metadata={
                        "document_id": page.get("document_id"),
                        "source": page.get("source"),
                        "page": page.get("page_number"),
                        "chunk_index": chunk_idx
                    }
                )
                chunks.append(doc)

        return chunks

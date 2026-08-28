import os
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from config import Config

class PDFService:
    @staticmethod
    def is_allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

    @staticmethod
    def save_and_extract(file_storage, document_id):
        """
        Saves uploaded file and extracts text page by page with metadata.
        Returns: (filepath, total_pages, file_size, list of page dicts)
        """
        original_filename = secure_filename(file_storage.filename)
        # Ensure unique stored filename
        stored_filename = f"{document_id}_{original_filename}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, stored_filename)
        
        file_storage.save(filepath)
        file_size = os.path.getsize(filepath)

        # Extract text page-by-page
        pages_data = []
        try:
            reader = PdfReader(filepath)
            total_pages = len(reader.pages)

            for page_idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                # Clean extra spaces & null bytes
                text = text.replace('\x00', ' ').strip()
                if text:
                    pages_data.append({
                        "page_number": page_idx,
                        "text": text,
                        "source": original_filename,
                        "document_id": document_id
                    })
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {str(e)}")

        return filepath, total_pages, file_size, pages_data

    @staticmethod
    def extract_from_filepath(filepath, document_id, filename):
        """Extracts text from an existing PDF file on disk"""
        pages_data = []
        reader = PdfReader(filepath)
        total_pages = len(reader.pages)

        for page_idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.replace('\x00', ' ').strip()
            if text:
                pages_data.append({
                    "page_number": page_idx,
                    "text": text,
                    "source": filename,
                    "document_id": document_id
                })
        return total_pages, pages_data

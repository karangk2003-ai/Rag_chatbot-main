import os
import json
from datetime import datetime
from database import db
from database.models import Document, Conversation, Message
from services.pdf_service import PDFService
from services.chunking_service import ChunkingService
from services.vector_store import VectorStoreService
from config import Config

SAMPLE_PDF_TEXT_PAGE1 = """
MAC501: ADVANCED MACHINE LEARNING & ARTIFICIAL INTELLIGENCE
CHAPTER 1: INTRODUCTION TO MACHINE LEARNING PARADIGMS

1.1 Overview
Machine Learning (ML) is a core subfield of artificial intelligence focused on developing algorithms that can learn patterns from empirical data and make informed predictions without being explicitly programmed for every scenario. 

1.2 Supervised Learning
Supervised learning involves training a model on a labeled dataset where each training example is paired with an output label. 
Key algorithms include:
1. Linear and Logistic Regression
2. Support Vector Machines (SVM)
3. Decision Trees and Random Forests
4. Gradient Boosted Trees (XGBoost)

Applications of supervised learning include spam detection, medical diagnosis, loan default risk assessment, and optical character recognition.
"""

SAMPLE_PDF_TEXT_PAGE2 = """
CHAPTER 2: DEEP LEARNING & NEURAL NETWORK ARCHITECTURES

2.1 Deep Neural Networks (DNN)
Deep learning extends standard neural networks by utilizing multiple hierarchical layers of artificial neurons to automatically learn feature representations at increasing levels of abstraction.

2.2 Core Architectures
- Convolutional Neural Networks (CNNs): Specialized for grid-structured topological data such as image classification, object detection, and medical imaging.
- Recurrent Neural Networks (RNNs) and LSTMs: Designed for sequential and temporal data such as time-series forecasting and natural language processing.
- Transformer Models: Utilize self-attention mechanisms to process input tokens in parallel, serving as the foundation for modern Large Language Models (LLMs).

2.3 Key Advantages
1. Automatic feature extraction eliminating the need for manual feature engineering.
2. High scalability with large datasets and compute clusters.
3. Superior accuracy on complex perceptual tasks including vision, speech, and translation.
"""

SAMPLE_PDF_TEXT_PAGE3 = """
CHAPTER 3: METHODOLOGY, LIMITATIONS, AND CONCLUSION

3.1 Research Methodology
The experimental methodology evaluates models using stratified 5-fold cross-validation. Performance metrics include Accuracy, Precision, Recall, F1-Score, and Area Under the ROC Curve (AUC-ROC).

3.2 Limitations of Deep Learning
1. Extreme data hunger requiring millions of labeled training instances.
2. High computational complexity demanding modern GPU/TPU infrastructure.
3. "Black-Box" opacity leading to poor interpretability in critical safety and healthcare domains.
4. Vulnerability to adversarial attacks and input distribution shifts.

3.3 Conclusion
While deep neural networks achieve state-of-the-art results across perceptual domains, combining them with symbolic knowledge graphs and Retrieval-Augmented Generation (RAG) offers a viable path toward transparent, grounded, and reliable AI systems.
"""

def generate_minimal_pdf(filepath, pages_text):
    """
    Generates a valid, readable PDF file without external heavy dependencies.
    """
    def escape_pdf_text(t):
        return t.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    objects = []
    
    # 1. Catalog
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    
    # 2. Pages object (placeholder, will fill kids)
    kids_refs = []
    
    # Fonts object
    font_obj_idx = 3
    objects.append("<< /Type /Font /Subtype /Type1 /Name /F1 /BaseFont /Helvetica >>")

    page_obj_indices = []
    content_obj_indices = []

    current_idx = 4
    for p_idx, text in enumerate(pages_text):
        page_obj_idx = current_idx
        content_obj_idx = current_idx + 1
        current_idx += 2
        
        page_obj_indices.append(page_obj_idx)
        content_obj_indices.append(content_obj_idx)
        kids_refs.append(f"{page_obj_idx} 0 R")
        
        # Build stream text
        stream_lines = ["BT", "/F1 11 Tf", "50 750 Td", "14 TL"]
        for line in text.strip().split('\n'):
            clean_line = escape_pdf_text(line.strip())
            if clean_line:
                stream_lines.append(f"({clean_line}) '")
            else:
                stream_lines.append("T*")
        stream_lines.append("ET")
        stream_content = "\n".join(stream_lines)
        
        # Page object
        objects.append(f"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 3 0 R >> >> /MediaBox [0 0 612 792] /Contents {content_obj_idx} 0 R >>")
        # Content object
        objects.append(f"<< /Length {len(stream_content.encode('latin1'))} >>\nstream\n{stream_content}\nendstream")

    # Insert actual Pages object at index 1 (object 2)
    pages_obj = f"<< /Type /Pages /Kids [ {' '.join(kids_refs)} ] /Count {len(pages_text)} >>"
    objects.insert(1, pages_obj)

    # Write PDF file
    with open(filepath, 'wb') as f:
        f.write(b"%PDF-1.4\n")
        offsets = []
        for i, obj in enumerate(objects, start=1):
            offsets.append(f.tell())
            f.write(f"{i} 0 obj\n{obj}\nendobj\n".encode('latin1'))
        
        xref_offset = f.tell()
        f.write(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode('latin1'))
        for off in offsets:
            f.write(f"{off:010d} 00000 n \n".encode('latin1'))
        f.write(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode('latin1'))


def init_db(app):
    with app.app_context():
        db.create_all()
        if not Document.query.first():
            print("[RAG-Chatbot] Seeding initial academic paper and demo conversation...")
            seed_initial_data()

def seed_initial_data():
    filename = "Machine_Learning_Foundations.pdf"
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    
    # 1. Generate academic PDF
    pages_text = [SAMPLE_PDF_TEXT_PAGE1, SAMPLE_PDF_TEXT_PAGE2, SAMPLE_PDF_TEXT_PAGE3]
    generate_minimal_pdf(filepath, pages_text)
    file_size = os.path.getsize(filepath)

    # 2. Extract & Chunk
    total_pages, pages_data = PDFService.extract_from_filepath(filepath, document_id=1, filename=filename)
    chunking_service = ChunkingService()
    chunks = chunking_service.split_pages_into_chunks(pages_data)

    # 3. Create Document Record
    doc = Document(
        id=1,
        filename=filename,
        filepath=filepath,
        pages=total_pages,
        file_size=file_size,
        chunk_count=len(chunks),
        status="Processed",
        uploaded_at=datetime.utcnow()
    )
    db.session.add(doc)
    db.session.commit()

    # 4. Embed into FAISS
    VectorStoreService.add_chunks(chunks)

    # 5. Create Sample Conversation
    conv = Conversation(
        id=1,
        title="Introduction to ML & Deep Learning",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(conv)
    db.session.commit()

    # Sample Messages
    m1 = Message(
        conversation_id=conv.id,
        role="user",
        content="What are the key advantages of deep learning mentioned in the document?",
        created_at=datetime.utcnow()
    )
    m2 = Message(
        conversation_id=conv.id,
        role="assistant",
        content="""Based on the uploaded document (**Machine_Learning_Foundations.pdf**, Page 2), the key advantages of deep learning are:

1. **Automatic Feature Extraction**: Eliminates the need for manual feature engineering.
2. **High Scalability**: Scales effectively with large datasets and compute clusters.
3. **Superior Perceptual Accuracy**: Delivers state-of-the-art accuracy across vision, speech, and translation tasks.""",
        sources=json.dumps([{
            "filename": "Machine_Learning_Foundations.pdf",
            "page": 2,
            "snippet": "2.3 Key Advantages: 1. Automatic feature extraction eliminating the need for manual feature engineering. 2. High scalability with large datasets...",
            "score": 0.28
        }]),
        created_at=datetime.utcnow()
    )
    db.session.add_all([m1, m2])
    db.session.commit()

    print("[RAG-Chatbot] Seeding completed successfully.")

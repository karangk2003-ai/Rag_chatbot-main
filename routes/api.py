import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from database import db
from database.models import Document, Conversation, Message
from services.pdf_service import PDFService
from services.chunking_service import ChunkingService
from services.vector_store import VectorStoreService
from services.rag_service import RAGService
from services.health_service import HealthService
from config import Config

api_bp = Blueprint('api', __name__)

# --- DOCUMENT MANAGEMENT APIS ---

@api_bp.route('/documents', methods=['GET'])
def get_documents():
    """Retrieve all uploaded documents"""
    docs = Document.query.order_by(Document.uploaded_at.desc()).all()
    return jsonify([d.to_dict() for d in docs])


@api_bp.route('/upload', methods=['POST'])
def upload_documents():
    """
    Handles single or multiple PDF uploads.
    Extracts text, creates chunks, and indexes into FAISS.
    """
    if 'files' not in request.files and 'file' not in request.files:
        return jsonify({"error": "No files provided in request."}), 400

    files = request.files.getlist('files') or [request.files.get('file')]
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "Empty filename provided."}), 400

    processed_docs = []
    chunking_service = ChunkingService()
    all_new_chunks = []

    for file in files:
        if not file or file.filename == '':
            continue

        if not PDFService.is_allowed_file(file.filename):
            return jsonify({"error": f"Invalid file type for '{file.filename}'. Only .pdf files are allowed."}), 400

        try:
            # 1. Create preliminary Document DB entry
            doc_record = Document(
                filename=file.filename,
                filepath="",
                status="Processing",
                uploaded_at=datetime.utcnow()
            )
            db.session.add(doc_record)
            db.session.commit()

            # 2. Save & Extract text page-by-page
            filepath, total_pages, file_size, pages_data = PDFService.save_and_extract(file, doc_record.id)

            # 3. Chunk text
            chunks = chunking_service.split_pages_into_chunks(pages_data)

            # 4. Update Document Record
            doc_record.filepath = filepath
            doc_record.pages = total_pages
            doc_record.file_size = file_size
            doc_record.chunk_count = len(chunks)
            doc_record.status = "Processed"
            db.session.commit()

            all_new_chunks.extend(chunks)
            processed_docs.append(doc_record.to_dict())

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Error processing '{file.filename}': {str(e)}"}), 500

    # 5. Index new chunks into FAISS vector store
    if all_new_chunks:
        try:
            VectorStoreService.add_chunks(all_new_chunks)
        except Exception as e:
            print(f"[API Upload] Vector store indexing error: {e}")

    return jsonify({
        "message": f"Successfully processed {len(processed_docs)} document(s).",
        "documents": processed_docs,
        "total_chunks_created": len(all_new_chunks)
    }), 201


@api_bp.route('/documents/<int:id>', methods=['DELETE'])
def delete_document(id):
    """
    Deletes a document and its file on disk, then rebuilds the FAISS index.
    """
    doc = Document.query.get_or_404(id)
    filepath = doc.filepath

    try:
        # Delete file from disk
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

        db.session.delete(doc)
        db.session.commit()

        # Rebuild FAISS index from remaining documents
        all_remaining_docs = Document.query.filter_by(status='Processed').all()
        chunking_service = ChunkingService()
        remaining_chunks = []

        for remaining_doc in all_remaining_docs:
            if os.path.exists(remaining_doc.filepath):
                _, pages_data = PDFService.extract_from_filepath(
                    remaining_doc.filepath,
                    remaining_doc.id,
                    remaining_doc.filename
                )
                remaining_chunks.extend(chunking_service.split_pages_into_chunks(pages_data))

        VectorStoreService.rebuild_index(remaining_chunks)

        return jsonify({"message": f"Document '{doc.filename}' deleted successfully and index updated."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete document: {str(e)}"}), 500


@api_bp.route('/documents/<int:id>/reprocess', methods=['POST'])
def reprocess_document(id):
    """Reprocesses an existing document on disk"""
    doc = Document.query.get_or_404(id)
    if not os.path.exists(doc.filepath):
        return jsonify({"error": "File not found on storage."}), 404

    try:
        total_pages, pages_data = PDFService.extract_from_filepath(doc.filepath, doc.id, doc.filename)
        chunking_service = ChunkingService()
        chunks = chunking_service.split_pages_into_chunks(pages_data)

        doc.pages = total_pages
        doc.chunk_count = len(chunks)
        doc.status = "Processed"
        db.session.commit()

        # Rebuild index
        all_docs = Document.query.filter_by(status='Processed').all()
        all_chunks = []
        for d in all_docs:
            if os.path.exists(d.filepath):
                _, pdata = PDFService.extract_from_filepath(d.filepath, d.id, d.filename)
                all_chunks.extend(chunking_service.split_pages_into_chunks(pdata))

        VectorStoreService.rebuild_index(all_chunks)
        return jsonify({"message": f"Document '{doc.filename}' reprocessed successfully.", "document": doc.to_dict()})
    except Exception as e:
        return jsonify({"error": f"Reprocessing error: {str(e)}"}), 500


# --- CHAT & CONVERSATION APIS ---

@api_bp.route('/chat', methods=['POST'])
def chat():
    """
    Main RAG Chatbot endpoint.
    Accepts: { "message": "...", "conversation_id": optional int, "document_ids": optional list }
    """
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')
    document_ids = data.get('document_ids')  # optional filtering by specific documents

    if not user_message:
        return jsonify({"error": "Message content cannot be empty."}), 400

    # 1. Manage Conversation Session
    if conversation_id:
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            conversation = Conversation(title=user_message[:45] + ("..." if len(user_message) > 45 else ""))
            db.session.add(conversation)
            db.session.commit()
    else:
        title = user_message[:45] + ("..." if len(user_message) > 45 else "")
        conversation = Conversation(title=title)
        db.session.add(conversation)
        db.session.commit()

    # 2. Save User Message
    user_msg_record = Message(
        conversation_id=conversation.id,
        role="user",
        content=user_message,
        created_at=datetime.utcnow()
    )
    db.session.add(user_msg_record)
    conversation.updated_at = datetime.utcnow()
    db.session.commit()

    # 3. Query RAG Service
    rag_result = RAGService.answer_question(
        question=user_message,
        filter_doc_ids=document_ids
    )

    answer_text = rag_result.get("answer", "")
    sources = rag_result.get("sources", [])
    chunks_used = rag_result.get("chunks_used", 0)

    # 4. Save Assistant Response
    assistant_msg_record = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer_text,
        sources=json.dumps(sources),
        created_at=datetime.utcnow()
    )
    db.session.add(assistant_msg_record)
    db.session.commit()

    return jsonify({
        "conversation_id": conversation.id,
        "conversation_title": conversation.title,
        "message_id": assistant_msg_record.id,
        "answer": answer_text,
        "sources": sources,
        "chunks_used": chunks_used
    }), 200


@api_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Retrieve all conversations sorted by latest updated"""
    conversations = Conversation.query.order_by(Conversation.updated_at.desc()).all()
    return jsonify([c.to_dict() for c in conversations])


@api_bp.route('/conversations/<int:id>', methods=['GET'])
def get_conversation(id):
    """Retrieve conversation details and full message history"""
    conversation = Conversation.query.get_or_404(id)
    messages = Message.query.filter_by(conversation_id=id).order_by(Message.created_at.asc()).all()
    
    return jsonify({
        "conversation": conversation.to_dict(),
        "messages": [m.to_dict() for m in messages]
    })


@api_bp.route('/conversations/<int:id>', methods=['DELETE'])
def delete_conversation(id):
    """Delete a conversation thread"""
    conversation = Conversation.query.get_or_404(id)
    db.session.delete(conversation)
    db.session.commit()
    return jsonify({"message": "Conversation deleted successfully."})


# --- DASHBOARD & HEALTH APIS ---

@api_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Returns aggregated stats for dashboard counters & charts"""
    total_docs = Document.query.count()
    
    # Calculate sum of pages and chunks
    from sqlalchemy import func
    total_pages = db.session.query(func.sum(Document.pages)).scalar() or 0
    total_chunks = db.session.query(func.sum(Document.chunk_count)).scalar() or 0
    
    total_questions = Message.query.filter_by(role='user').count()
    total_conversations = Conversation.query.count()

    recent_docs = Document.query.order_by(Document.uploaded_at.desc()).limit(5).all()
    recent_msgs = Message.query.filter_by(role='user').order_by(Message.created_at.desc()).limit(5).all()

    vector_stats = VectorStoreService.get_stats()
    health = HealthService.get_system_health()

    return jsonify({
        "total_documents": total_docs,
        "total_pages": int(total_pages),
        "total_chunks": int(total_chunks),
        "total_questions": total_questions,
        "total_conversations": total_conversations,
        "recent_documents": [d.to_dict() for d in recent_docs],
        "recent_questions": [{
            "id": m.id,
            "conversation_id": m.conversation_id,
            "content": m.content,
            "created_at": m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else None
        } for m in recent_msgs],
        "vector_status": vector_stats.get("status"),
        "total_vectors": vector_stats.get("total_vectors"),
        "health": health
    })


@api_bp.route('/health', methods=['GET'])
def get_health():
    """System diagnostic health endpoint"""
    return jsonify(HealthService.get_system_health())

from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Dashboard homepage"""
    return render_template('dashboard.html')

@views_bp.route('/chat')
@views_bp.route('/chat/<int:conversation_id>')
def chat(conversation_id=None):
    """RAG Chatbot Interface"""
    return render_template('chat.html', active_conversation_id=conversation_id)

@views_bp.route('/documents')
def documents():
    """Document Management & PDF Upload Page"""
    return render_template('documents.html')

@views_bp.route('/health')
def health():
    """System Health & Diagnostics Page"""
    return render_template('health.html')

import pytest
import io
from app import create_app
from database import db
from database.models import Document, Conversation, Message
from database.seed import generate_minimal_pdf

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Seed test doc
        d = Document(filename="test.pdf", filepath="test.pdf", pages=2, file_size=1024, chunk_count=4, status="Processed")
        db.session.add(d)
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_documents_api(client):
    res = client.get('/api/documents')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) >= 1
    assert data[0]["filename"] == "test.pdf"

def test_dashboard_stats_api(client):
    res = client.get('/api/dashboard/stats')
    assert res.status_code == 200
    data = res.get_json()
    assert "total_documents" in data
    assert "total_pages" in data
    assert data["total_documents"] >= 1

def test_health_api(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert "database" in data
    assert "vector_store" in data

def test_chat_api(client):
    res = client.post('/api/chat', json={
        "message": "What is machine learning?"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "answer" in data
    assert "conversation_id" in data

def test_conversations_api(client):
    # 1. Create a conversation via chat
    chat_res = client.post('/api/chat', json={"message": "First query"})
    conv_id = chat_res.get_json()["conversation_id"]

    # 2. Get conversations list
    res = client.get('/api/conversations')
    assert res.status_code == 200
    assert len(res.get_json()) >= 1

    # 3. Get single conversation
    detail_res = client.get(f'/api/conversations/{conv_id}')
    assert detail_res.status_code == 200
    assert len(detail_res.get_json()["messages"]) == 2  # user + assistant

    # 4. Delete conversation
    del_res = client.delete(f'/api/conversations/{conv_id}')
    assert del_res.status_code == 200

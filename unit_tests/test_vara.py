# type: ignore
import sys, os
from unittest.mock import patch, MagicMock
import pytest

with patch('llama_cpp.Llama', autospec=True):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
    from app import app, get_db
    from database import Base, engine, SessionLocal, Conversation, Message
    from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def override_get_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    def _override():
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = _override
    try:
        yield db
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_search_endpoint():
    mock_result = {
        "title": "Title",
        "body": "Очень длинное тело результата, чтобы пройти фильтр по длине и попасть в sources",
        "href": "http://example.com"
    }
    with patch("app.generate_text_response", return_value="Результаты поиска"), \
         patch("app.DDGS") as mock_ddgs:
        mock_instance = MagicMock()
        mock_instance.text.return_value = [mock_result]
        mock_ddgs.return_value.__enter__.return_value = mock_instance
        response = client.post("/search", json={
            "query": "погода",
            "temperature": 0.7,
            "system_prompt": "test",
            "max_tokens": 200
        })
    assert response.status_code == 200
    data = response.json()
    assert data["assistant_message"] == "Результаты поиска"
    assert len(data["sources"]) == 1

def test_search_no_results_fallback():
    with patch("app.generate_text_response", return_value="Извините, не найдено"), \
         patch("app.DDGS") as mock_ddgs:
        mock_instance = MagicMock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value.__enter__.return_value = mock_instance
        response = client.post("/search", json={
            "query": "невозможный_запрос",
            "temperature": 0.7,
            "system_prompt": "test",
            "max_tokens": 200
        })
    assert response.status_code == 200
    data = response.json()
    assert data["assistant_message"] == "Извините, не найдено"

def test_create_conversation():
    db = SessionLocal()
    conv = Conversation(title="Test Chat")
    db.add(conv)
    db.commit()
    assert conv.id is not None
    assert conv.title == "Test Chat"
    assert conv.created_at is not None
    db.close()

def test_default_title():
    db = SessionLocal()
    conv = Conversation()
    db.add(conv)
    db.commit()
    assert conv.title == "Новый чат"
    db.close()

def test_conversation_has_messages():
    db = SessionLocal()
    conv = Conversation(title="Chat with messages")
    db.add(conv)
    db.flush()
    msg1 = Message(conversation_id=conv.id, role="user", content="Hello")
    msg2 = Message(conversation_id=conv.id, role="assistant", content="Hi!")
    db.add_all([msg1, msg2])
    db.commit()
    assert len(conv.messages) == 2
    assert conv.messages[0].content == "Hello"
    db.close()

def test_message_role():
    db = SessionLocal()
    conv = Conversation()
    db.add(conv)
    db.flush()
    msg = Message(conversation_id=conv.id, role="user", content="test")
    db.add(msg)
    db.commit()
    assert msg.role == "user"
    db.close()

def test_delete_conversation_db():
    db = SessionLocal()
    conv = Conversation(title="To delete")
    db.add(conv)
    db.flush()
    msg = Message(conversation_id=conv.id, role="user", content="text")
    db.add(msg)
    db.commit()

    db.delete(msg)
    db.delete(conv)
    db.commit()
    assert db.query(Conversation).count() == 0
    assert db.query(Message).count() == 0
    db.close()

def test_file_attachment_as_text():
    file_content = "print('Hello, World!')"
    message_with_file = f"Содержимое файла code.py:\n```\n{file_content}\n```"
    with patch("app.generate_text_response", return_value="Проанализировал код"):
        response = client.post("/chat", json={
            "message": message_with_file,
            "temperature": 0.5,
            "system_prompt": "test",
            "max_tokens": 100
        })
    assert response.status_code == 200
    data = response.json()
    assert data["assistant_message"] == "Проанализировал код"

def test_large_content_truncation():
    long_message = "A" * 10000
    with patch("app.generate_text_response", return_value="ok") as mock_gen:
        client.post("/chat", json={
            "message": long_message,
            "system_prompt": "test",
            "max_tokens": 10,
            "temperature": 0.5
        })
        args, _ = mock_gen.call_args
        messages = args[0]
        assert len(messages) <= 21

def test_message_image_base64_stored():
    db = SessionLocal()
    conv = Conversation()
    db.add(conv)
    db.flush()
    test_base64 = "iVBORw0KGgoAAAANSUhEUgAA..."
    msg = Message(conversation_id=conv.id, role="user", content="image", image_base64=test_base64)
    db.add(msg)
    db.commit()
    assert msg.image_base64 == test_base64
    db.close()

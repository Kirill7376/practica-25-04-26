# type: ignore
import sys, os
from unittest.mock import patch, MagicMock
import pytest

with patch('llama_cpp.Llama', autospec=True):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
    from app import app, get_db
    from database import Base, engine, SessionLocal
    from model import _clean, TOKENS
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

def test_list_conversations():
    with patch("app.generate_text_response", return_value="ok"):
        client.post("/chat", json={"message": "A"})
        client.post("/chat", json={"message": "B"})
    response = client.get("/conversations")
    assert response.status_code == 200
    convs = response.json()
    assert len(convs) == 2

def test_get_conversation():
    with patch("app.generate_text_response", return_value="ok"):
        resp = client.post("/chat", json={"message": "Hi"})
        conv_id = resp.json()["conversation_id"]
    response = client.get(f"/conversations/{conv_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conv_id
    assert len(data["messages"]) == 2

def test_get_conversation_404():
    response = client.get("/conversations/9999")
    assert response.status_code == 404

def test_delete_conversation():
    with patch("app.generate_text_response", return_value="ok"):
        resp = client.post("/chat", json={"message": "to delete"})
        conv_id = resp.json()["conversation_id"]
    del_resp = client.delete(f"/conversations/{conv_id}")
    assert del_resp.status_code == 200
    get_resp = client.get(f"/conversations/{conv_id}")
    assert get_resp.status_code == 404

def test_clean_removes_end_of_turn():
    assert _clean("Привет!<|end_of_turn|>") == "Привет!"

def test_clean_removes_multiple_tokens():
    assert _clean("Ответ<|assistant|>пользователь<|user|>конец") == "Ответ"

def test_clean_no_tokens():
    text = "Просто текст без токенов"
    assert _clean(text) == text

def test_clean_preserves_russian():
    assert _clean("Привет!<|end|>") == "Привет!"

def test_tokens_structure():
    assert isinstance(TOKENS, list)
    assert "<|end_of_turn|>" in TOKENS
    assert "<|start_of_turn|>" in TOKENS

def test_invalid_json_request():
    response = client.post("/chat", data="not a json",
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 422
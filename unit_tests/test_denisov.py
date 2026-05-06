# type: ignore
import sys, os
from unittest.mock import patch, MagicMock
import pytest

with patch('llama_cpp.Llama', autospec=True):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
    from app import app, get_db, build_messages_from_db
    from database import Base, engine, SessionLocal, Conversation, Message
    from model import generate_text_response, llm
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

def test_generate_text_response_mocked():
    with patch('model.llm.create_chat_completion') as mock_create:
        mock_create.return_value = {
            "choices": [{"message": {"content": "Привет! Как дела?"}}]
        }
        result = generate_text_response([{"role": "user", "content": "Hi"}])
        assert result == "Привет! Как дела?"
        mock_create.assert_called_once()

def test_generate_text_response_with_tokens():
    with patch('model.llm.create_chat_completion') as mock_create:
        mock_create.return_value = {
            "choices": [{"message": {"content": "Ответ<|end_of_turn|>лишнее"}}]
        }
        result = generate_text_response([{"role": "user", "content": "Q"}])
        assert result == "Ответ"

def test_generate_text_response_error_handling():
    with patch('model.llm.create_chat_completion') as mock_create:
        mock_create.side_effect = Exception("Model failed")
        try:
            generate_text_response([{"role": "user", "content": "Hi"}])
            assert False, "Should have raised"
        except Exception as e:
            assert "Model failed" in str(e)

def test_chat_new_conversation():
    with patch("app.generate_text_response", return_value="Ответ бота"):
        response = client.post("/chat", json={
            "message": "Привет",
            "temperature": 0.7,
            "system_prompt": "Тестовый промпт",
            "max_tokens": 100,
            "assistant_name": "Bot"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["user_message"] == "Привет"
    assert data["assistant_message"] == "Ответ бота"
    assert data["conversation_id"] is not None

def test_chat_existing_conversation():
    with patch("app.generate_text_response", side_effect=["Первый ответ", "Второй ответ"]):
        resp1 = client.post("/chat", json={"message": "Первое", "system_prompt": "Ты - помощник"})
        conv_id = resp1.json()["conversation_id"]
        resp2 = client.post("/chat", json={
            "message": "Второе",
            "conversation_id": conv_id,
            "temperature": 0.5,
            "system_prompt": "Ты - помощник",
            "max_tokens": 100,
            "assistant_name": "Bot"
        })
    assert resp2.status_code == 200
    assert resp2.json()["conversation_id"] == conv_id

def test_chat_nonexistent_conversation():
    response = client.post("/chat", json={
        "message": "Test",
        "conversation_id": 9999,
        "temperature": 0.7,
        "system_prompt": "test",
        "max_tokens": 100,
        "assistant_name": "Bot"
    })
    assert response.status_code == 404

def test_system_prompt_passed_to_model():
    with patch("app.generate_text_response") as mock_gen:
        mock_gen.return_value = "Ответ Ок"
        client.post("/chat", json={
            "message": "Привет",
            "system_prompt": "Ты - тестовый ассистент",
            "temperature": 0.7,
            "max_tokens": 100,
        })
        args, kwargs = mock_gen.call_args
        messages = args[0]
        system_msg = next((m for m in messages if m["role"] == "system"), None)
        assert system_msg is not None
        assert system_msg["content"] == "Ты - тестовый ассистент"

def test_chat_with_search_trigger():
    with patch("app.generate_text_response") as mock_gen:
        mock_gen.side_effect = ["SEARCH: погода", "Результат поиска: солнечно"]
        with patch("app.perform_search", return_value=("snippets", ["url"])):
            response = client.post("/chat", json={
                "message": "Какая погода?",
                "temperature": 0.5,
                "system_prompt": "test",
                "max_tokens": 100
            })
    assert response.status_code == 200
    data = response.json()
    assert data["assistant_message"] == "Результат поиска: солнечно"
    assert mock_gen.call_count == 2

def test_build_messages_truncation():
    db = SessionLocal()
    try:
        conv = Conversation(title="Truncation Test")
        db.add(conv)
        db.commit()
        for i in range(25):
            msg = Message(conversation_id=conv.id, role="user", content=f"message {i}")
            db.add(msg)
        db.commit()

        messages = build_messages_from_db(conv.id, "system prompt", db)
        assert len(messages) <= 21  # 1 system + максимум 20 последних
    finally:
        db.close()

def test_context_limit_settings():
    assert llm.n_ctx == 16384

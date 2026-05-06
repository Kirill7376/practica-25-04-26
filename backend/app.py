from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, Conversation, Message
from model import generate_text_response # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from duckduckgo_search import DDGS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str
    temperature: float = 0.7
    system_prompt: str = (
        "Ты — полезный ассистент. Если ты не знаешь точного ответа или не уверен, "
        "вместо ответа напиши SEARCH: короткий запрос для поиска информации. "
        "После того как получишь результаты поиска, ответь пользователю."
    )
    max_tokens: int = 150
    assistant_name: str = "Assistant"

class ChatResponse(BaseModel):
    conversation_id: int
    user_message: str
    assistant_message: str

class SearchRequest(BaseModel):
    query: str
    conversation_id: int | None = None
    temperature: float = 0.7
    system_prompt: str = "Ты — полезный ассистент. На основе результатов поиска дай развёрнутый ответ."
    max_tokens: int = 300

class SearchResponse(BaseModel):
    conversation_id: int
    user_query: str
    assistant_message: str
    sources: list[str]

def perform_search(query: str) -> tuple[str, list[str]]:
    """Выполняет поиск и возвращает (сниппеты, источники)."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
    good_results = [r for r in results if len(r.get('body', '')) > 80]
    if not good_results:
        good_results = [r for r in results if len(r.get('body', '')) > 30]
    snippets = "\n".join([f"- {r['title']}: {r['body']}" for r in good_results])
    sources = [r['href'] for r in good_results]
    return snippets, sources

def build_messages_from_db(conv_id: int, system_prompt: str, db: Session, last_n: int = 20):
    """Собирает список сообщений из истории диалога."""
    history = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.id).all()
    recent = history[-last_n:] if len(history) > last_n else history
    messages = [{"role": "system", "content": system_prompt}]
    for msg in recent:
        role = "user" if msg.role == "user" else "assistant" # type: ignore
        messages.append({"role": role, "content": msg.content}) # type: ignore
    return messages

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    if req.conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404)
    else:
        conv = Conversation(title=req.message[:30] + "..." if len(req.message) > 30 else req.message)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
    db.add(user_msg)
    db.commit()

    messages = build_messages_from_db(conv.id, req.system_prompt, db) # type: ignore
    if not messages or messages[-1]["content"] != req.message:
        messages.append({"role": "user", "content": req.message})

    assistant_text = generate_text_response(
        messages=messages,
        temperature=req.temperature,
        max_tokens=req.max_tokens
    )

    if assistant_text.strip().upper().startswith("SEARCH:"):
        query = assistant_text[len("SEARCH:"):].strip()
        if not query:
            query = req.message   # fallback
        snippets, sources = perform_search(query) # type: ignore
        messages.insert(1, {
            "role": "system",
            "content": f"Результаты поиска по запросу '{query}':\n{snippets}\n\nОтветь пользователю на основе этих данных."
        })
        assistant_text = generate_text_response(
            messages=messages,
            temperature=req.temperature,
            max_tokens=req.max_tokens
        )

    for token in ["<|end_of_turn|>", "<|user|>", "<|assistant|>"]:
        if token in assistant_text:
            assistant_text = assistant_text.split(token)[0].strip()

    assistant_msg = Message(conversation_id=conv.id, role="assistant", content=assistant_text)
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        conversation_id=conv.id, # type: ignore
        user_message=req.message,
        assistant_message=assistant_text
    )

@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest, db: Session = Depends(get_db)):
    with DDGS() as ddgs:
        results = list(ddgs.text(req.query, max_results=5))
    
    good_results = [r for r in results if len(r.get('body', '')) > 80]
    if not good_results:
        good_results = [r for r in results if len(r.get('body', '')) > 30]
    sources = [r['href'] for r in good_results]

    if good_results:
        snippets = "\n".join([f"- {r['title']}: {r['body']}" for r in good_results])
        user_prompt = (
            f"Запрос пользователя: {req.query}\n\n"
            f"Результаты поиска:\n{snippets}\n\n"
            "Ответь кратко на русском, используя только эти данные."
        )
        system_prompt = (
            "Ты — полезный ассистент. Отвечай строго на основе предоставленных результатов поиска. "
            "Не добавляй ничего от себя. Если информации недостаточно, так и скажи."
        )
    else:
        user_prompt = f"Запрос пользователя: {req.query}\n\nОтветь на русском кратко."
        system_prompt = (
            "Ты — полезный ассистент. Ответь на вопрос пользователя, используя свои знания. "
            "Предупреди, что информация не найдена в поиске, и дай краткий общий ответ."
        )

    if req.conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404)
    else:
        conv = Conversation(title=req.query[:30])
        db.add(conv)
        db.commit()
        db.refresh(conv)

    user_msg = Message(conversation_id=conv.id, role="user", content=f"/search {req.query}")
    db.add(user_msg)
    db.commit()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    assistant_text = generate_text_response(
        messages=messages,
        temperature=req.temperature,
        max_tokens=req.max_tokens
    )
    for token in ["<|end_of_turn|>", "<|user|>", "<|assistant|>"]:
        if token in assistant_text:
            assistant_text = assistant_text.split(token)[0].strip()

    assistant_msg = Message(conversation_id=conv.id, role="assistant", content=assistant_text)
    db.add(assistant_msg)
    db.commit()

    return SearchResponse(
        conversation_id=conv.id, # type: ignore
        user_query=req.query,
        assistant_message=assistant_text,
        sources=sources
    )

@app.get("/conversations")
def list_conversations(db: Session = Depends(get_db)): # type: ignore
    convs = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
    result = []
    for c in convs:
        first_msg = db.query(Message).filter(Message.conversation_id == c.id, Message.role == "user").first()
        title = first_msg.content[:50] + "..." if first_msg and len(first_msg.content) > 50 else (first_msg.content if first_msg else c.title) # type: ignore
        result.append({ # type: ignore
            "id": c.id,
            "title": title,
            "created_at": c.created_at.isoformat()
        })
    return result # type: ignore

@app.get("/conversations/{conv_id}")
def get_conversation(conv_id: int, db: Session = Depends(get_db)): # type: ignore
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404)
    messages = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.id).all()
    return {
        "id": conv.id, # type: ignore
        "messages": [{
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp.isoformat()
        } for m in messages]
    }

@app.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404)
    db.delete(conv)
    db.commit()
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

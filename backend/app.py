from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from model import generate_text_response, _clean
from pydantic import BaseModel, field_validator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversations = {}
next_id = 1

class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None
    temperature: float = 0.7
    system_prompt: str = "Ты — полезный ассистент."
    max_tokens: int = 150

    @field_validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Сообщение не может быть пустым')
        return v

class ChatResponse(BaseModel):
    conversation_id: int
    user_message: str
    assistant_message: str
    

def build_messages(conv_id: int, system_prompt: str):
    history = conversations.get(conv_id, [])
    messages = [{"role": "system", "content": system_prompt}]
    for user_msg, assistant_msg in history[-20:]:
        messages.append({"role": "user", "content": user_msg})
        if assistant_msg:
            messages.append({"role": "assistant", "content": assistant_msg})
    return messages

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    global next_id
    if req.conversation_id and req.conversation_id in conversations:
        conv_id = req.conversation_id
    else:
        conv_id = next_id
        next_id += 1
        conversations[conv_id] = []

    messages = build_messages(conv_id, req.system_prompt)
    messages.append({"role": "user", "content": req.message})

    assistant_text = generate_text_response(
        messages=messages,
        temperature=req.temperature,
        max_tokens=req.max_tokens
    )
    assistant_text = _clean(assistant_text)
    conversations[conv_id].append((req.message, assistant_text))
    return ChatResponse(
        conversation_id=conv_id,
        user_message=req.message,
        assistant_message=assistant_text
    )

@app.get("/conversations")
def get_conversation(conv_id: int):
    if conv_id not in conversations:
        raise HTTPException(status_code=404)
    history = conversations[conv_id]
    messages = []
    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if assistant_msg:
            messages.append({"role": "assistant", "content": assistant_msg})
    return {"id": conv_id, "messages": messages}
    
@app.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: int):
    if conv_id not in conversations:
        raise HTTPException(status_code=404)
    del conversations[conv_id]
    return {"ok": True}

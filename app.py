from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from model import generate_text_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    temperature: float = 0.7
    system_prompt: str = "Ты — полезный ассистент."
    max_tokens: int = 150

class ChatResponse(BaseModel):
    user_message: str
    assistant_message: str

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    messages = [
        {"role": "system", "content": req.system_prompt},
        {"role": "user", "content": req.message}
    ]
    assistant_text = generate_text_response(
        messages=messages,
        temperature=req.temperature,
        max_tokens=req.max_tokens
    )
    return ChatResponse(
        user_message=req.message,
        assistant_message=assistant_text
    )

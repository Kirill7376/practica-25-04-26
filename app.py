from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

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

class ChatResponse(BaseModel):
    user_message: str
    assistant_message: str

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return ChatResponse(
        user_message=req.message,
        assistant_message="эхо: " + req.message
    )

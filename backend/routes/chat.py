from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.chatbot_engine import chat_reply

router = APIRouter()


class ChatHistoryItem(BaseModel):
    role: str
    content: str | None = None
    text: str | None = None


class ChatRequest(BaseModel):
    message: str
    analysis: dict[str, Any] | None = None
    history: list[ChatHistoryItem] = Field(default_factory=list)


@router.post("/chat")
def chat(body: ChatRequest):
    message = body.message.strip()
    if not message:
        return {
            "success": True,
            "reply": "Sorunu yaz; ürünü fiyat, yorum, kullanım amacı veya alternatifler açısından değerlendirebilirim.",
            "intent": "unknown",
            "preferences": {},
        }

    result = chat_reply(
        message=message,
        history=[item.model_dump() for item in body.history[-12:]],
        analysis=body.analysis,
    )
    return {
        "success": True,
        "reply": result["reply"],
        "intent": result["intent"],
        "preferences": result["preferences"],
    }

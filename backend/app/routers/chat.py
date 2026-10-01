from fastapi import APIRouter
from pydantic import BaseModel
from uuid import UUID
from app.services.ai_assistant import ask_assistant

router = APIRouter(prefix="/chat", tags=["AI Assistant"])


class ChatRequest(BaseModel):
    zone_id: UUID
    question: str


@router.post("")
def chat(request: ChatRequest):
    answer = ask_assistant(request.zone_id, request.question)
    return {"zone_id": request.zone_id, "question": request.question, "answer": answer}

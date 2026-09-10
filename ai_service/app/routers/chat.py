from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.llm.prompt_builder import format_sample_questions
from app.services.qa_service import QAService

router = APIRouter(prefix="/chat", tags=["AI Assistant"])

# One shared QAService instance. It holds no per-user state itself —
# per-conversation state lives inside qa_service._sessions, keyed by
# conversation_id — so this is safe across concurrent requests.
qa_service = QAService()


class ChatMessage(BaseModel):
    message: str
    case_id: Optional[int] = None
    conversation_id: str = "default"


class QuestionRequest(BaseModel):
    question: str
    case_id: Optional[int] = None


@router.post("/")
async def chat(req: ChatMessage):
    """Multi-turn chat with conversation memory."""
    return await qa_service.chat(req.message, req.conversation_id, req.case_id)


@router.post("/ask")
async def ask_question(req: QuestionRequest):
    """Single question -> answer, no history. Simplest path for a quick demo."""
    return await qa_service.answer_question(req.question, req.case_id)


@router.post("/reset")
def reset_chat(conversation_id: str = "default"):
    qa_service.reset_conversation(conversation_id)
    return {"message": f"Conversation '{conversation_id}' reset."}


@router.get("/sample-questions")
def get_sample_questions():
    return {"sample_questions": format_sample_questions()}

"""Chat endpoint: returns an answer with structured citations."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services.qa import answer_question

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    result = answer_question(db, question=payload.question, top_k=payload.top_k)
    return ChatResponse(answer=result.answer, citations=result.citations)

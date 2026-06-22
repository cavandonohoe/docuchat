"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    num_chunks: int
    created_at: datetime


class Citation(BaseModel):
    marker: int = Field(description="The [n] marker used in the answer text.")
    chunk_id: int
    document_id: int
    filename: str
    page: int | None = None
    score: float
    snippet: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str

"""End-to-end QA orchestration test using fakes for embedder, generator, retriever."""

from __future__ import annotations

from app.rag.retriever import RetrievedChunk
from app.services import qa as qa_module
from app.services.qa import answer_question


class FakeEmbedder:
    def embed(self, texts):
        return [[0.0] * 8 for _ in texts]

    def embed_one(self, text):
        return [0.0] * 8


class FakeGenerator:
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_user_prompt: str | None = None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.last_user_prompt = user_prompt
        return self.response


def test_answer_question_returns_cited_answer(monkeypatch):
    chunks = [
        RetrievedChunk(
            chunk_id=1,
            document_id=10,
            filename="a.pdf",
            ordinal=0,
            page=2,
            text="Photosynthesis converts light into chemical energy.",
            score=0.92,
        ),
        RetrievedChunk(
            chunk_id=2,
            document_id=10,
            filename="a.pdf",
            ordinal=1,
            page=3,
            text="Chlorophyll absorbs primarily red and blue light.",
            score=0.81,
        ),
    ]
    monkeypatch.setattr(qa_module, "retrieve", lambda db, vec, top_k=None: chunks)

    gen = FakeGenerator("Plants convert light into energy [1]. Chlorophyll absorbs light [2].")
    result = answer_question(
        db=None,
        question="How do plants get energy?",
        embedder=FakeEmbedder(),
        generator=gen,
    )

    assert "Plants convert light" in result.answer
    assert [c.marker for c in result.citations] == [1, 2]
    assert result.citations[0].chunk_id == 1
    assert result.citations[1].page == 3
    assert "Photosynthesis" in gen.last_user_prompt  # context is wired through


def test_answer_question_abstains_with_no_retrievals(monkeypatch):
    monkeypatch.setattr(qa_module, "retrieve", lambda db, vec, top_k=None: [])
    result = answer_question(
        db=None,
        question="anything?",
        embedder=FakeEmbedder(),
        generator=FakeGenerator("should not be called"),
    )
    assert "don't have enough information" in result.answer
    assert result.citations == []

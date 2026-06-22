"""Tests for the eval metric implementations."""

from __future__ import annotations

from app.evals.metrics import (
    citation_score,
    faithfulness_score,
    retrieval_score,
)
from app.rag.retriever import RetrievedChunk


def _chunk(filename: str, idx: int = 1) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=idx,
        document_id=1,
        filename=filename,
        ordinal=0,
        page=None,
        text=f"chunk {idx} text",
        score=0.9,
    )


def test_retrieval_score_hit_returns_first_rank():
    retrieved = [_chunk("other.pdf", 1), _chunk("docuchat_overview.txt", 2)]
    score = retrieval_score("docuchat_overview.txt", retrieved)
    assert score.hit is True
    assert score.rank == 2


def test_retrieval_score_miss():
    retrieved = [_chunk("other.pdf", 1)]
    score = retrieval_score("missing.pdf", retrieved)
    assert score.hit is False
    assert score.rank is None


def test_citation_score_counts_valid_markers():
    retrieved = [_chunk("a.txt", 1), _chunk("b.txt", 2)]
    score = citation_score("Foo [1] bar [2] baz [9].", retrieved)
    assert score.total == 3
    assert score.valid == 2
    assert score.validity == 2 / 3


def test_citation_score_no_markers_is_perfect():
    score = citation_score("no markers here", [_chunk("a.txt", 1)])
    assert score.total == 0
    assert score.validity == 1.0


class _Judge:
    def __init__(self, verdict: str) -> None:
        self.verdict = verdict

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return self.verdict


def test_faithfulness_score_yes():
    assert (
        faithfulness_score(
            answer="x", retrieved=[_chunk("a.txt", 1)], judge=_Judge("YES")
        )
        is True
    )


def test_faithfulness_score_no():
    assert (
        faithfulness_score(
            answer="x", retrieved=[_chunk("a.txt", 1)], judge=_Judge("no")
        )
        is False
    )

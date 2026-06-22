"""Tests for citation extraction and answer assembly."""

from __future__ import annotations

from app.rag.retriever import RetrievedChunk
from app.services.qa import _build_citations


def _chunk(i: int) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=100 + i,
        document_id=1,
        filename="doc.pdf",
        ordinal=i,
        page=i,
        text=f"context chunk {i} body text",
        score=0.9 - 0.1 * i,
    )


def test_valid_citations_are_extracted_once():
    retrieved = [_chunk(1), _chunk(2), _chunk(3)]
    answer = "Foo [1] bar [2]. Also [1] again."
    citations = _build_citations(answer, retrieved)
    markers = [c.marker for c in citations]
    assert markers == [1, 2]
    assert citations[0].chunk_id == 101
    assert citations[1].chunk_id == 102


def test_invalid_citation_markers_are_ignored():
    retrieved = [_chunk(1)]
    answer = "Only one source [1], but model invented [7]."
    citations = _build_citations(answer, retrieved)
    assert [c.marker for c in citations] == [1]


def test_no_citations_when_answer_has_none():
    retrieved = [_chunk(1)]
    assert _build_citations("plain answer", retrieved) == []

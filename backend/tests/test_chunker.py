"""Tests for the recursive character chunker."""

from __future__ import annotations

from app.ingestion.chunker import chunk_text


def test_short_text_yields_single_chunk():
    chunks = chunk_text("hello world", page=1, chunk_size=100, chunk_overlap=10)
    assert len(chunks) == 1
    assert chunks[0].text == "hello world"
    assert chunks[0].page == 1
    assert chunks[0].ordinal == 0


def test_long_text_splits_with_overlap_and_ordinals():
    text = "A. " * 200  # ~600 chars
    chunks = chunk_text(text, page=None, chunk_size=120, chunk_overlap=20, start_ordinal=5)
    assert len(chunks) > 1
    assert [c.ordinal for c in chunks] == list(range(5, 5 + len(chunks)))
    assert all(len(c.text) <= 120 + 20 for c in chunks)


def test_invalid_overlap_raises():
    import pytest

    with pytest.raises(ValueError):
        chunk_text("abc", page=None, chunk_size=10, chunk_overlap=10)


def test_empty_input_returns_empty():
    assert chunk_text("", page=None, chunk_size=100, chunk_overlap=10) == []

"""Tests for ingestion loaders (CSV and text; PDF integration is covered elsewhere)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.exceptions import UnsupportedFileType
from app.ingestion.loaders import load


def test_load_text(tmp_path: Path):
    p = tmp_path / "notes.txt"
    p.write_text("hello\nworld", encoding="utf-8")
    segments = load(p, "text/plain")
    assert segments == [(None, "hello\nworld")]


def test_load_csv(tmp_path: Path):
    p = tmp_path / "data.csv"
    p.write_text("name,age\nada,36\ngrace,85\n", encoding="utf-8")
    segments = load(p, "text/csv")
    assert len(segments) == 1
    page, text = segments[0]
    assert page is None
    assert "name: ada" in text and "age: 36" in text
    assert "name: grace" in text and "age: 85" in text


def test_unsupported_type(tmp_path: Path):
    p = tmp_path / "blob.xyz"
    p.write_text("...", encoding="utf-8")
    with pytest.raises(UnsupportedFileType):
        load(p, "application/x-weird")

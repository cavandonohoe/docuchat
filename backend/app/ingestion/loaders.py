"""File loaders that yield ``(page, text)`` segments per document.

``page`` is ``None`` for formats without a natural page concept.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from pathlib import Path

from pypdf import PdfReader

from app.core.exceptions import UnsupportedFileType

Segment = tuple[int | None, str]

PDF_TYPES = {"application/pdf"}
CSV_TYPES = {"text/csv", "application/csv"}
TEXT_TYPES = {"text/plain", "text/markdown", "application/octet-stream"}


def load(path: Path, content_type: str) -> list[Segment]:
    """Dispatch to a format-specific loader based on content type."""
    ct = (content_type or "").lower()
    if ct in PDF_TYPES or path.suffix.lower() == ".pdf":
        return list(_load_pdf(path))
    if ct in CSV_TYPES or path.suffix.lower() == ".csv":
        return list(_load_csv(path))
    if ct in TEXT_TYPES or path.suffix.lower() in {".txt", ".md"}:
        return list(_load_text(path))
    raise UnsupportedFileType(f"Unsupported content type: {content_type!r}")


def _load_pdf(path: Path) -> Iterable[Segment]:
    reader = PdfReader(str(path))
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            yield i, text


def _load_csv(path: Path) -> Iterable[Segment]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    if not rows:
        return
    header = rows[0]
    buf = io.StringIO()
    for row in rows[1:]:
        pairs = (f"{h}: {v}" for h, v in zip(header, row, strict=False) if v)
        buf.write(" | ".join(pairs))
        buf.write("\n")
    text = buf.getvalue().strip()
    if text:
        yield None, text


def _load_text(path: Path) -> Iterable[Segment]:
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if text:
        yield None, text

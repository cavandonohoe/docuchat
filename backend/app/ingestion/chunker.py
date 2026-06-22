"""Character-based recursive chunker.

Splits on paragraph, sentence, and word boundaries before falling back to
hard character cuts. Cheap, predictable, and dependency-free. Adequate as
a baseline for English text; a structure-aware splitter would be the next
upgrade.
"""

from __future__ import annotations

from dataclasses import dataclass

_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass(slots=True)
class Chunk:
    text: str
    page: int | None
    ordinal: int


def chunk_text(
    text: str,
    page: int | None,
    chunk_size: int,
    chunk_overlap: int,
    start_ordinal: int = 0,
) -> list[Chunk]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    pieces = _recursive_split(text, chunk_size, _SEPARATORS)
    merged = _merge(pieces, chunk_size, chunk_overlap)
    return [Chunk(text=t, page=page, ordinal=start_ordinal + i) for i, t in enumerate(merged)]


def _recursive_split(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    if len(text) <= chunk_size or not separators:
        return [text] if text else []
    sep, rest = separators[0], separators[1:]
    parts = text.split(sep) if sep else list(text)
    out: list[str] = []
    for part in parts:
        if len(part) <= chunk_size:
            out.append(part)
        else:
            out.extend(_recursive_split(part, chunk_size, rest))
    return out


def _merge(pieces: list[str], chunk_size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if not piece:
            continue
        candidate = (current + " " + piece).strip() if current else piece
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = (tail + " " + piece).strip() if tail else piece
        else:
            current = piece
    if current:
        chunks.append(current)
    return [c.strip() for c in chunks if c.strip()]

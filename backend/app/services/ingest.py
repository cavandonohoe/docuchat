"""End-to-end document ingestion: parse, chunk, embed, persist."""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ingestion.chunker import Chunk, chunk_text
from app.ingestion.loaders import load
from app.models import Chunk as ChunkModel
from app.models import Document
from app.rag.embedder import Embedder, OpenAIEmbedder

logger = logging.getLogger(__name__)

_EMBED_BATCH = 64


def ingest_document(
    db: Session,
    *,
    path: Path,
    filename: str,
    content_type: str,
    embedder: Embedder | None = None,
) -> Document:
    settings = get_settings()
    emb = embedder or OpenAIEmbedder()

    segments = load(path, content_type)
    chunks: list[Chunk] = []
    ordinal = 0
    for page, text in segments:
        produced = chunk_text(
            text=text,
            page=page,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            start_ordinal=ordinal,
        )
        chunks.extend(produced)
        ordinal += len(produced)

    if not chunks:
        raise ValueError("Document produced zero chunks (empty or unparseable).")

    vectors: list[list[float]] = []
    for i in range(0, len(chunks), _EMBED_BATCH):
        batch = chunks[i : i + _EMBED_BATCH]
        vectors.extend(emb.embed([c.text for c in batch]))

    document = Document(filename=filename, content_type=content_type, num_chunks=len(chunks))
    db.add(document)
    db.flush()

    db.add_all(
        ChunkModel(
            document_id=document.id,
            ordinal=c.ordinal,
            text=c.text,
            page=c.page,
            embedding=v,
        )
        for c, v in zip(chunks, vectors, strict=True)
    )
    db.commit()
    db.refresh(document)
    logger.info("Ingested %s -> %d chunks (doc_id=%d)", filename, len(chunks), document.id)
    return document

"""Vector retrieval over the ``chunks`` table using pgvector cosine distance."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.core.config import get_settings


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: int
    document_id: int
    filename: str
    ordinal: int
    page: int | None
    text: str
    score: float


def retrieve(db: Session, query_embedding: list[float], top_k: int | None = None) -> list[RetrievedChunk]:
    """Return the top-k most similar chunks for a query vector.

    The score is cosine similarity in [0, 1], higher is better. We compute
    it from pgvector's cosine *distance* (``<=>``) as ``1 - distance``.
    """
    k = top_k or get_settings().top_k
    sql = text(
        """
        SELECT
            c.id            AS chunk_id,
            c.document_id   AS document_id,
            d.filename      AS filename,
            c.ordinal       AS ordinal,
            c.page          AS page,
            c.text          AS text,
            1 - (c.embedding <=> CAST(:emb AS vector)) AS score
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        ORDER BY c.embedding <=> CAST(:emb AS vector) ASC
        LIMIT :k
        """
    ).bindparams(bindparam("emb"), bindparam("k"))
    rows = db.execute(sql, {"emb": _pgvector_literal(query_embedding), "k": k}).mappings().all()
    return [RetrievedChunk(**dict(row)) for row in rows]


def _pgvector_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{v:.8f}" for v in vec) + "]"

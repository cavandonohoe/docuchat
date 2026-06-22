"""Schema bootstrap: enable pgvector and create tables.

This intentionally avoids Alembic. The schema is small and stable, so a
single ``init_db`` call at startup is enough for a portfolio repo.
Production would use migrations.
"""

from __future__ import annotations

import logging

from sqlalchemy import text

from app.db.session import Base, engine

logger = logging.getLogger(__name__)


def init_db() -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    # Import models so they register with Base.metadata before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_vector_index()
    logger.info("Database initialized")


def _ensure_vector_index() -> None:
    """Create an HNSW cosine index on chunks.embedding if not present."""
    sql = """
    CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops)
    """
    with engine.begin() as conn:
        conn.execute(text(sql))

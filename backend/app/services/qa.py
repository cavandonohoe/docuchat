"""Question answering orchestration: embed query, retrieve, generate, cite."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.rag.embedder import Embedder, OpenAIEmbedder
from app.rag.generator import Generator, OpenAIGenerator
from app.rag.prompts import SYSTEM_PROMPT, build_user_prompt
from app.rag.retriever import RetrievedChunk, retrieve
from app.schemas import Citation

logger = logging.getLogger(__name__)

_CITATION_RX = re.compile(r"\[(\d+)\]")
_SNIPPET_LEN = 240


@dataclass(slots=True)
class AnswerResult:
    answer: str
    citations: list[Citation]
    retrieved: list[RetrievedChunk]


def answer_question(
    db: Session,
    *,
    question: str,
    top_k: int | None = None,
    embedder: Embedder | None = None,
    generator: Generator | None = None,
) -> AnswerResult:
    emb = embedder or OpenAIEmbedder()
    gen = generator or OpenAIGenerator()

    query_vec = emb.embed_one(question)
    retrieved = retrieve(db, query_vec, top_k=top_k)

    if not retrieved:
        return AnswerResult(
            answer="I don't have enough information in the provided documents to answer.",
            citations=[],
            retrieved=[],
        )

    user_prompt = build_user_prompt(question, retrieved)
    answer = gen.generate(SYSTEM_PROMPT, user_prompt)
    citations = _build_citations(answer, retrieved)
    return AnswerResult(answer=answer, citations=citations, retrieved=retrieved)


def _build_citations(answer: str, retrieved: list[RetrievedChunk]) -> list[Citation]:
    """Return a citation entry for every valid [n] referenced by the answer."""
    seen: set[int] = set()
    out: list[Citation] = []
    for match in _CITATION_RX.finditer(answer):
        marker = int(match.group(1))
        if marker in seen:
            continue
        if marker < 1 or marker > len(retrieved):
            continue
        seen.add(marker)
        rc = retrieved[marker - 1]
        snippet = rc.text.strip().replace("\n", " ")
        if len(snippet) > _SNIPPET_LEN:
            snippet = snippet[:_SNIPPET_LEN].rstrip() + "…"
        out.append(
            Citation(
                marker=marker,
                chunk_id=rc.chunk_id,
                document_id=rc.document_id,
                filename=rc.filename,
                page=rc.page,
                score=round(rc.score, 4),
                snippet=snippet,
            )
        )
    return out

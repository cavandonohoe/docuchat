"""Prompt templates for the RAG pipeline.

Kept in a single module so eval and serving share the exact same wording.
"""

from __future__ import annotations

from app.rag.retriever import RetrievedChunk

SYSTEM_PROMPT = (
    "You are a precise research assistant. Answer the user's question using "
    "ONLY the provided context. Cite supporting context with bracketed "
    "numeric markers like [1], [2] that correspond to the numbered sources "
    "below. If the answer cannot be derived from the context, reply exactly: "
    "\"I don't have enough information in the provided documents to answer.\" "
    "Do not invent citations."
)


def build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    sources = "\n\n".join(
        f"[{i}] (source: {c.filename}"
        + (f", page {c.page}" if c.page else "")
        + f")\n{c.text}"
        for i, c in enumerate(chunks, start=1)
    )
    return (
        f"Question: {question}\n\n"
        f"Context:\n{sources}\n\n"
        "Answer concisely with inline citations like [1]."
    )

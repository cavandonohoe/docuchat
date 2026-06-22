"""Metric implementations for the RAG eval harness.

Three lightweight metrics:

* ``retrieval_hit``: did any retrieved chunk come from the expected source
  file? Returned alongside the rank of the first hit.
* ``faithfulness``: an LLM-as-judge yes/no on whether the answer is supported
  by the retrieved context.
* ``citation_validity``: ratio of in-answer ``[n]`` markers that correspond
  to a real retrieved chunk.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.rag.generator import Generator
from app.rag.retriever import RetrievedChunk

_CITATION_RX = re.compile(r"\[(\d+)\]")

JUDGE_SYSTEM = (
    "You are a strict grader. Decide if the candidate ANSWER is fully "
    "supported by the provided CONTEXT. Respond with exactly one word: YES or NO."
)


@dataclass(slots=True)
class RetrievalScore:
    hit: bool
    rank: int | None  # 1-based rank of the first hit, or None if missed


@dataclass(slots=True)
class CitationScore:
    total: int
    valid: int

    @property
    def validity(self) -> float:
        return 1.0 if self.total == 0 else self.valid / self.total


def retrieval_score(expected_source: str, retrieved: list[RetrievedChunk]) -> RetrievalScore:
    norm = expected_source.strip().lower()
    for i, rc in enumerate(retrieved, start=1):
        if norm in rc.filename.strip().lower():
            return RetrievalScore(hit=True, rank=i)
    return RetrievalScore(hit=False, rank=None)


def citation_score(answer: str, retrieved: list[RetrievedChunk]) -> CitationScore:
    markers = [int(m.group(1)) for m in _CITATION_RX.finditer(answer)]
    if not markers:
        return CitationScore(total=0, valid=0)
    n = len(retrieved)
    valid = sum(1 for m in markers if 1 <= m <= n)
    return CitationScore(total=len(markers), valid=valid)


def faithfulness_score(
    *,
    answer: str,
    retrieved: list[RetrievedChunk],
    judge: Generator,
) -> bool:
    """LLM-as-judge faithfulness check. Returns True if the judge says YES."""
    context = "\n\n".join(f"[{i}] {c.text}" for i, c in enumerate(retrieved, start=1))
    user = f"CONTEXT:\n{context}\n\nANSWER:\n{answer}\n\nIs the answer fully supported?"
    verdict = judge.generate(JUDGE_SYSTEM, user).strip().upper()
    return verdict.startswith("YES")

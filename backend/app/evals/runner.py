"""Eval runner: executes each case end-to-end and aggregates metrics."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass

from sqlalchemy.orm import Session

from app.evals.dataset import EvalCase
from app.evals.metrics import (
    CitationScore,
    RetrievalScore,
    citation_score,
    faithfulness_score,
    retrieval_score,
)
from app.rag.generator import Generator
from app.services.qa import answer_question

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CaseResult:
    id: str
    question: str
    answer: str
    expected_answer: str
    source_file: str
    retrieval: RetrievalScore
    citation: CitationScore
    faithful: bool
    must_include_pass: bool

    def to_dict(self) -> dict:
        d = asdict(self)
        d["retrieval"] = {"hit": self.retrieval.hit, "rank": self.retrieval.rank}
        d["citation"] = {
            "total": self.citation.total,
            "valid": self.citation.valid,
            "validity": round(self.citation.validity, 4),
        }
        return d


@dataclass(slots=True)
class Summary:
    n: int
    retrieval_hit_rate: float
    mean_citation_validity: float
    faithfulness_rate: float
    must_include_pass_rate: float


def run_cases(
    db: Session,
    cases: list[EvalCase],
    *,
    top_k: int | None = None,
    judge: Generator,
) -> list[CaseResult]:
    results: list[CaseResult] = []
    for case in cases:
        result = answer_question(db, question=case.question, top_k=top_k)
        retrieval = retrieval_score(case.source_file, result.retrieved)
        citation = citation_score(result.answer, result.retrieved)
        faithful = faithfulness_score(
            answer=result.answer, retrieved=result.retrieved, judge=judge
        )
        must_include_pass = all(
            phrase.lower() in result.answer.lower() for phrase in case.must_include
        )
        results.append(
            CaseResult(
                id=case.id,
                question=case.question,
                answer=result.answer,
                expected_answer=case.expected_answer,
                source_file=case.source_file,
                retrieval=retrieval,
                citation=citation,
                faithful=faithful,
                must_include_pass=must_include_pass,
            )
        )
    return results


def summarize(results: list[CaseResult]) -> Summary:
    n = len(results)
    if n == 0:
        return Summary(0, 0.0, 0.0, 0.0, 0.0)
    return Summary(
        n=n,
        retrieval_hit_rate=sum(1 for r in results if r.retrieval.hit) / n,
        mean_citation_validity=sum(r.citation.validity for r in results) / n,
        faithfulness_rate=sum(1 for r in results if r.faithful) / n,
        must_include_pass_rate=sum(1 for r in results if r.must_include_pass) / n,
    )

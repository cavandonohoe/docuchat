"""Tests for the eval reporter."""

from __future__ import annotations

import json
from pathlib import Path

from app.evals.metrics import CitationScore, RetrievalScore
from app.evals.reporter import write_reports
from app.evals.runner import CaseResult, Summary


def _result(case_id: str, hit: bool, valid: int, total: int, faithful: bool) -> CaseResult:
    return CaseResult(
        id=case_id,
        question="q?",
        answer="a",
        expected_answer="e",
        source_file="s.txt",
        retrieval=RetrievalScore(hit=hit, rank=1 if hit else None),
        citation=CitationScore(total=total, valid=valid),
        faithful=faithful,
        must_include_pass=True,
    )


def test_write_reports_creates_json_and_markdown(tmp_path: Path):
    results = [
        _result("c1", True, 1, 1, True),
        _result("c2", False, 0, 0, False),
    ]
    summary = Summary(
        n=2,
        retrieval_hit_rate=0.5,
        mean_citation_validity=1.0,
        faithfulness_rate=0.5,
        must_include_pass_rate=1.0,
    )
    json_path, md_path = write_reports(
        tmp_path, dataset_name="smoke.json", results=results, summary=summary
    )
    assert json_path.exists() and md_path.exists()

    payload = json.loads(json_path.read_text())
    assert payload["summary"]["n"] == 2
    assert payload["summary"]["retrieval_hit_rate"] == 0.5
    assert len(payload["results"]) == 2

    md = md_path.read_text()
    assert "RAG Evaluation Report" in md
    assert "| c1 |" in md and "| c2 |" in md

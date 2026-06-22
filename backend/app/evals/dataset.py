"""Dataset loader for RAG evaluation cases."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class EvalCase:
    id: str
    question: str
    expected_answer: str
    source_file: str
    must_include: list[str]


def load_dataset(path: Path) -> list[EvalCase]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases: list[EvalCase] = []
    for i, item in enumerate(raw):
        cases.append(
            EvalCase(
                id=item.get("id", f"case-{i:03d}"),
                question=item["question"],
                expected_answer=item["expected_answer"],
                source_file=item["source_file"],
                must_include=list(item.get("must_include", [])),
            )
        )
    return cases

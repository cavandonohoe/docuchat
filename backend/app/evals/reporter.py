"""Markdown + JSON reporting for eval runs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.evals.runner import CaseResult, Summary


def write_reports(
    output_dir: Path,
    *,
    dataset_name: str,
    results: list[CaseResult],
    summary: Summary,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = output_dir / f"report-{ts}.json"
    md_path = output_dir / "REPORT.md"

    payload = {
        "dataset": dataset_name,
        "generated_at": ts,
        "summary": {
            "n": summary.n,
            "retrieval_hit_rate": round(summary.retrieval_hit_rate, 4),
            "mean_citation_validity": round(summary.mean_citation_validity, 4),
            "faithfulness_rate": round(summary.faithfulness_rate, 4),
            "must_include_pass_rate": round(summary.must_include_pass_rate, 4),
        },
        "results": [r.to_dict() for r in results],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(dataset_name, ts, results, summary), encoding="utf-8")
    return json_path, md_path


def _render_markdown(
    dataset_name: str, ts: str, results: list[CaseResult], summary: Summary
) -> str:
    lines: list[str] = []
    lines.append("# RAG Evaluation Report")
    lines.append("")
    lines.append(f"- **Dataset**: `{dataset_name}`")
    lines.append(f"- **Generated**: {ts}")
    lines.append(f"- **Cases**: {summary.n}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Retrieval hit rate | {summary.retrieval_hit_rate:.1%} |")
    lines.append(f"| Mean citation validity | {summary.mean_citation_validity:.1%} |")
    lines.append(f"| Faithfulness (LLM judge) | {summary.faithfulness_rate:.1%} |")
    lines.append(f"| Must-include phrase pass | {summary.must_include_pass_rate:.1%} |")
    lines.append("")
    lines.append("## Per-case results")
    lines.append("")
    lines.append("| ID | Hit | Rank | Citations valid | Faithful | Must-include |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for r in results:
        lines.append(
            "| {id} | {hit} | {rank} | {cv} | {f} | {mi} |".format(
                id=r.id,
                hit="✓" if r.retrieval.hit else "✗",
                rank=r.retrieval.rank if r.retrieval.rank else "-",
                cv=f"{r.citation.valid}/{r.citation.total}",
                f="✓" if r.faithful else "✗",
                mi="✓" if r.must_include_pass else "✗",
            )
        )
    lines.append("")
    return "\n".join(lines)

"""CLI entry point for the eval harness.

Usage::

    python -m app.evals.cli --dataset ../evals/datasets/smoke.json
"""

from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.evals.dataset import load_dataset
from app.evals.reporter import write_reports
from app.evals.runner import run_cases, summarize
from app.rag.generator import OpenAIGenerator

console = Console()
app = typer.Typer(add_completion=False, help="Run RAG evaluations against the live backend.")


@app.command()
def run(
    dataset: Path = typer.Option(..., exists=True, readable=True, help="Path to dataset JSON."),
    reports_dir: Path = typer.Option(
        Path("../evals/reports"), help="Where to write JSON + markdown reports."
    ),
    top_k: int | None = typer.Option(None, help="Override retrieval top_k."),
) -> None:
    configure_logging("INFO")
    cases = load_dataset(dataset)
    console.print(f"[bold]Loaded[/bold] {len(cases)} cases from {dataset}")

    judge = OpenAIGenerator()
    with SessionLocal() as db:
        results = run_cases(db, cases, top_k=top_k, judge=judge)
    summary = summarize(results)
    json_path, md_path = write_reports(
        reports_dir, dataset_name=dataset.name, results=results, summary=summary
    )

    table = Table(title="Eval Summary")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Cases", str(summary.n))
    table.add_row("Retrieval hit rate", f"{summary.retrieval_hit_rate:.1%}")
    table.add_row("Mean citation validity", f"{summary.mean_citation_validity:.1%}")
    table.add_row("Faithfulness rate", f"{summary.faithfulness_rate:.1%}")
    table.add_row("Must-include pass rate", f"{summary.must_include_pass_rate:.1%}")
    console.print(table)
    console.print(f"[green]JSON[/green]     -> {json_path}")
    console.print(f"[green]Markdown[/green] -> {md_path}")


def main() -> None:  # pragma: no cover - thin wrapper
    app()


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    main()

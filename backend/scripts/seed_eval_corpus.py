"""Helper script: upload every file in ``evals/datasets/sources/`` to a
running backend. Useful before running ``python -m app.evals.cli``.

Usage::

    python scripts/seed_eval_corpus.py --api http://localhost:8000 \
        --sources ../evals/datasets/sources
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--sources", type=Path, default=Path("../evals/datasets/sources"))
    args = parser.parse_args()

    sources: Path = args.sources
    if not sources.exists():
        print(f"sources directory not found: {sources}", file=sys.stderr)
        return 2

    files = sorted(p for p in sources.iterdir() if p.is_file())
    if not files:
        print("no source files to upload", file=sys.stderr)
        return 0

    with httpx.Client(base_url=args.api, timeout=120.0) as client:
        for path in files:
            with path.open("rb") as fh:
                resp = client.post(
                    "/documents",
                    files={"file": (path.name, fh, _guess_type(path))},
                )
            if resp.status_code >= 300:
                print(f"FAILED {path.name}: {resp.status_code} {resp.text}", file=sys.stderr)
                return 1
            doc = resp.json()
            print(f"OK  {path.name}  -> doc id {doc['id']}, {doc['num_chunks']} chunks")
    return 0


def _guess_type(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".csv": "text/csv",
        ".md": "text/markdown",
        ".txt": "text/plain",
    }.get(ext, "application/octet-stream")


if __name__ == "__main__":
    raise SystemExit(main())

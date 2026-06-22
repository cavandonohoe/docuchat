# docuchat

> Production-quality RAG application. Upload PDFs, CSVs, and text files; ask
> questions; get answers with verifiable citations back to the source.

This project is a portfolio piece. It is intentionally narrow in feature scope
and deep in engineering: a clean FastAPI backend, a small Next.js frontend,
`pgvector` for retrieval, a pytest suite, a Dockerized dev stack, GitHub
Actions CI, and a RAG evaluation harness with retrieval, faithfulness, and
citation-accuracy metrics.

See the full write-up below for architecture, tradeoffs, and how to run it.

## Quickstart

```bash
cp .env.example .env       # fill in OPENAI_API_KEY
docker compose up --build
# backend  -> http://localhost:8000/docs
# frontend -> http://localhost:3000
```

Run tests:

```bash
cd backend && pytest
```

Run RAG evals:

```bash
cd backend && python -m app.evals.cli --dataset ../evals/datasets/smoke.json
```

See the architecture, design tradeoffs, and roadmap further below. This README
is rewritten in detail at the end of the build.

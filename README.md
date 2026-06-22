# docuchat

> Retrieval-augmented document Q&A with verifiable citations.
> FastAPI · PostgreSQL + pgvector · OpenAI · Next.js · Docker · pytest · GitHub Actions.

`docuchat` is a small, production-shaped RAG application. Upload PDFs, CSVs,
or text files; ask questions; get answers with bracketed `[n]` citations
that map back to specific chunks of specific source files. The goal of the
repo is not to add features — it is to show a clean cut through an
end-to-end AI engineering stack: ingestion, embeddings, vector search,
generation, evaluation, API, frontend, tests, CI, and a Dockerized dev
environment.

---

## Highlights

- **RAG pipeline** with explicit, testable seams: loaders → chunker →
  embedder → retriever → generator → citation builder.
- **`pgvector` retrieval** with an HNSW cosine index. One database for
  metadata and vectors keeps the topology simple and transactional.
- **Cited answers**: every `[n]` in the response is validated against the
  retrieved set; invalid markers are dropped. The frontend renders each
  citation with filename, page, similarity score, and a snippet.
- **Evaluation harness** measuring retrieval hit-rate, LLM-as-judge
  faithfulness, and citation validity. Outputs JSON + a markdown report.
- **API-first**: typed FastAPI endpoints with Pydantic models; OpenAPI at
  `/docs`.
- **Tests** for the chunker, loaders, citation assembly, the QA pipeline
  end-to-end, and every eval metric — using fakes for OpenAI and the
  retriever to keep the suite hermetic.
- **CI** runs `ruff` + `pytest` for the backend and Next.js lint + build
  for the frontend on every push.
- **Docker Compose** runs `pgvector`, the FastAPI backend, and the Next.js
  frontend with a single command.

---

## Architecture

```
┌──────────────┐     POST /documents      ┌────────────────────────────┐
│  Next.js UI  │ ───────────────────────▶ │  FastAPI                   │
│              │ ◀──────── JSON ───────── │  • parse + chunk           │
└──────────────┘   POST /chat             │  • embed (OpenAI)          │
                                          │  • retrieve (pgvector)     │
                                          │  • generate + cite         │
                                          └─────────────┬──────────────┘
                                                        │ SQL
                                                  ┌─────▼──────┐
                                                  │ Postgres + │
                                                  │  pgvector  │
                                                  └────────────┘
```

### Data model

| Table       | Key columns                                                           |
| ----------- | --------------------------------------------------------------------- |
| `documents` | `id`, `filename`, `content_type`, `num_chunks`, `created_at`          |
| `chunks`    | `id`, `document_id`, `ordinal`, `text`, `page`, `embedding vector(1536)` |

A single HNSW index on `chunks.embedding` (cosine) backs retrieval.

### Backend layout

```
backend/app/
  api/         routers: documents, chat, health
  core/        config, logging, exceptions
  db/          engine, session, init_db (pgvector + tables + HNSW index)
  ingestion/   loaders (pdf/csv/text), recursive chunker
  rag/         embedder, retriever, generator, prompts
  services/    ingest_document, answer_question
  evals/       dataset, metrics, runner, reporter, CLI
  models.py    SQLAlchemy ORM
  schemas.py   Pydantic API models
  main.py      app factory + lifespan
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the long version.

---

## Quickstart

### With Docker (recommended)

```bash
cp .env.example .env          # fill in OPENAI_API_KEY
docker compose up --build
```

- API:      <http://localhost:8000/docs>
- Frontend: <http://localhost:3000>

### Local dev (backend only)

```bash
# Start just Postgres + pgvector
docker compose up -d db

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

export DATABASE_URL='postgresql+psycopg://docuchat:docuchat@localhost:5432/docuchat'
export OPENAI_API_KEY='sk-...'
uvicorn app.main:app --reload
```

### API

```http
POST /documents       multipart/form-data; field name "file"
GET  /documents       list documents
DELETE /documents/{id}
POST /chat            { "question": "...", "top_k": 5 }
GET  /health
```

Chat response shape:

```json
{
  "answer": "Plants convert light into energy [1].",
  "citations": [
    {
      "marker": 1,
      "chunk_id": 42,
      "document_id": 3,
      "filename": "biology.pdf",
      "page": 12,
      "score": 0.91,
      "snippet": "Photosynthesis converts light into chemical energy …"
    }
  ]
}
```

---

## Testing

```bash
cd backend
pytest                          # full suite
pytest --cov=app -q             # with coverage
ruff check app tests            # lint
```

The suite avoids network and database dependencies:

- The chunker, loaders, citation builder, and eval metrics are pure-Python
  unit tests.
- The QA pipeline test injects fake `Embedder` and `Generator` objects and
  monkey-patches the retriever, exercising the full prompt and citation
  flow without hitting OpenAI or Postgres.
- The health endpoint test exercises the FastAPI app with the in-process
  test client.

---

## Evaluation

The eval harness lives at `backend/app/evals/` and ships with a small smoke
dataset under `evals/datasets/`. It measures three things per case:

| Metric | What it measures | How |
| --- | --- | --- |
| **Retrieval hit-rate** | Did the expected source file appear in the top-k chunks? | Filename match against retrieved chunks, with rank. |
| **Faithfulness** | Is the answer grounded in the retrieved context? | LLM-as-judge: `YES`/`NO` on `(context, answer)`. |
| **Citation validity** | Are all `[n]` markers in the answer real? | Marker IDs are checked against the retrieved set. |

A `must_include` list per case provides a cheap deterministic backstop
(simple substring check) so regressions surface even without the LLM judge.

Run it:

```bash
# 1. Seed the live backend with the eval corpus
cd backend
python scripts/seed_eval_corpus.py --api http://localhost:8000 \
    --sources ../evals/datasets/sources

# 2. Run the evals
python -m app.evals.cli --dataset ../evals/datasets/smoke.json
```

Outputs:

- `evals/reports/REPORT.md` — human-readable summary + per-case table.
- `evals/reports/report-<timestamp>.json` — raw payload for tracking deltas.

---

## Design tradeoffs

| Choice | Why | When I'd change it |
| --- | --- | --- |
| `pgvector` + a single Postgres | One service, transactional with metadata, fast enough at this scale | Tens of millions of vectors, multi-tenant filters, or hybrid search at scale → a dedicated vector DB |
| Recursive character splitter | Dependency-light and predictable baseline | Tables / structured PDFs → a structure-aware splitter |
| Single embedding model, no reranker | Predictable cost and latency | When recall@k starts dominating error analysis → add a cross-encoder reranker |
| Synchronous ingestion in the request | Trivial to reason about and test | Files > a few MB or batches of files → a worker queue (Celery/RQ/Arq) with a `processing` document state |
| `init_db` on startup, no Alembic | Tiny, stable schema | The moment the schema needs to evolve without dropping data |
| LLM-as-judge faithfulness | Cheap signal, easy to wire | Add reference-based metrics (BLEURT/Ragas) once a labelled set exists |

---

## Roadmap

- Cross-encoder reranker for the top-k retrieved chunks.
- Hybrid retrieval (BM25 + vector) with score fusion.
- Streaming chat responses.
- Per-document delete cascades verified by an integration test against a real Postgres.
- Replace `init_db` with Alembic migrations.
- Per-tenant scoping and auth (FastAPI dependency + row-level filters).

---

## Repository layout

```
docuchat/
  backend/                FastAPI app + tests + eval CLI
    app/                  application code
    tests/                pytest suite (hermetic, no network)
    scripts/              dev utilities (eval corpus seeder)
    Dockerfile
    pyproject.toml
  frontend/               Next.js (App Router) upload + chat UI
    app/
    Dockerfile
  evals/
    datasets/             eval corpora (JSON + source files)
    reports/              generated REPORT.md + JSON snapshots
  docker-compose.yml      pgvector + backend + frontend
  .github/workflows/      CI
  ARCHITECTURE.md
  README.md
```

---

## License

MIT — see [LICENSE](LICENSE).

# Architecture

This document describes how docuchat is built.

## System overview

```
┌──────────────┐     POST /documents      ┌────────────────────────────┐
│  Next.js UI  │ ───────────────────────▶ │  FastAPI                   │
│              │ ◀─── stream / json ───── │  - upload + parse          │
└──────────────┘   POST /chat             │  - chunk + embed           │
                                          │  - retrieve (pgvector)     │
                                          │  - generate (OpenAI)       │
                                          └─────────────┬──────────────┘
                                                        │ SQL
                                                  ┌─────▼──────┐
                                                  │ Postgres + │
                                                  │  pgvector  │
                                                  └────────────┘
```

## Backend layout

```
backend/
  app/
    api/         FastAPI routers (documents, chat, health)
    core/        config, logging, exceptions
    db/          engine, session, base, migrations bootstrap
    ingestion/   loaders (pdf/csv/text), chunkers
    rag/         embedder, retriever, generator, prompts
    services/    orchestration (ingest_document, answer_question)
    evals/       dataset loaders, metrics, CLI, reporter
    models.py    SQLAlchemy ORM (Document, Chunk)
    schemas.py   Pydantic request/response models
    main.py      app factory
  tests/         pytest tests with fakes for OpenAI + DB
```

## Data model

* `documents(id, filename, content_type, num_chunks, created_at)`
* `chunks(id, document_id, ordinal, text, embedding vector(1536),
         page, created_at)`

A single HNSW index on `chunks.embedding` (cosine) powers retrieval.

## Ingestion pipeline

1. Multipart upload arrives at `POST /documents`.
2. The file is persisted to `UPLOAD_DIR`.
3. A loader dispatches by content type:
   * PDF → `pypdf` page-by-page extraction.
   * CSV → row-wise stringified records.
   * Text/markdown → raw read.
4. A recursive character splitter chunks the text with configurable
   `CHUNK_SIZE` and `CHUNK_OVERLAP`.
5. Chunks are embedded in batches via `text-embedding-3-small`.
6. Chunks + vectors are persisted in a single transaction.

## Retrieval + generation

* Query → embed → cosine ANN search over `chunks.embedding`, `top_k`
  configurable (default 5).
* Retrieved chunks are formatted with stable `[n]` markers.
* The LLM is instructed to cite only those markers and to abstain when the
  context is insufficient.
* The API response includes both the answer and a structured list of
  citations (chunk id, document id, page, score, snippet).

## Tradeoffs

| Choice | Why | Tradeoff |
|---|---|---|
| `pgvector` instead of a dedicated vector DB | One service to run, transactional with metadata, plenty fast at this scale | Caps out around millions of vectors; would swap for a dedicated store at scale |
| Recursive character splitter | Simple, dependency-light, good baseline | Semantic / structural splitters can improve recall on PDFs with tables |
| Single embedding model | Predictable cost + latency | No reranker; left as a documented roadmap item |
| Synchronous ingestion | Easy to reason about and test | Larger files would benefit from a worker queue |
| Plain SQL ORM, no Alembic | Schema is tiny; `init_db` is enough for a portfolio repo | Real production would use migrations |

## Evaluation

The eval harness in `app/evals/` ingests a YAML/JSON dataset of
`(question, expected_answer, source_file)` cases, runs each through the live
RAG pipeline, and reports:

* **Retrieval hit@k** — did the expected source file appear in the retrieved
  chunks?
* **Faithfulness** — LLM-as-judge check that the answer is grounded in the
  retrieved context.
* **Citation validity** — every `[n]` cited in the answer maps to a real
  retrieved chunk.

Results are written as both JSON and a markdown report in `evals/reports/`.

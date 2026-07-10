# PROMPT — Scaffold the `smoky-rag` module in the `smoky` repository

You are working inside the `smoky` GitHub repository (Kallitests — autonomous
Claude smoke-test agent). Your task is to create a new `rag/` subfolder that
implements **Smoky-RAG**, the Retrieval-Augmented Generation module that
enriches Smoky's Cypress spec generation with context pulled from PRDs, User
Stories, existing Test Cases, API docs, Jira tickets, Confluence pages,
Release Notes, and Requirements.

Follow the technical spec below exactly. Do not invent architecture that
isn't described here — if something is ambiguous, add a `# TODO:` comment
instead of guessing.

## 1. Context you must respect

- Smoky-RAG is **not** a standalone agent. It is a retrieval layer called by
  `agent/spec_generator.py` right before Claude generates a Cypress spec
  (Step 2 of the existing Smoky flow). Do not build any autonomous
  decision loop, scheduler, or planning logic inside `rag/`.
- Steps 1 and 3-6 of the existing Smoky flow (Jira detection, GitHub
  Actions trigger, Dockerized Cypress execution, reporting, error handling)
  are **out of scope** and must not be modified.
- The generated Cypress spec must still be produced by Claude; Smoky-RAG's
  only job is to prepare and inject the "RETRIEVED CONTEXT" section of the
  prompt, and to make each context-derived claim traceable to its source.

## 2. Directory structure to create

Create exactly this structure under the repo root:

```
smoky/
├── rag/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── jira_ingest.py          # Sync resolved tickets -> chunks
│   │   ├── confluence_ingest.py    # Sync product/QA pages -> chunks
│   │   ├── cypress_spec_ingest.py  # Sync validated specs -> chunks
│   │   ├── openapi_ingest.py       # Swagger/OpenAPI parsing -> chunks
│   │   └── chunker.py              # Shared chunking + overlap logic
│   │
│   ├── retriever.py                # Vector search + reranking
│   ├── vector_store.py             # Qdrant/pgvector client wrapper
│   ├── embeddings.py               # Voyage AI / Claude Embeddings wrapper
│   └── prompt_context_builder.py   # Formats retrieved chunks for the prompt
│
├── prompts/
│   └── rag_context_template.txt    # Context injection template
│
├── evals/
│   └── ragas_eval.py               # Faithfulness / context precision eval
│
└── tests/
    └── rag/
        ├── test_chunker.py
        ├── test_retriever.py
        └── test_prompt_context_builder.py
```

If any of these paths already exist (e.g. `prompts/`, `evals/`, `tests/` from
Smoky v1.0), add the new files into the existing folders rather than
duplicating them.

## 3. Implementation requirements per file

### `rag/ingestion/chunker.py`
- Function `chunk_text(text: str, chunk_size: int = 400, overlap: int = 60) -> list[Chunk]`
- `Chunk` is a dataclass with fields: `content: str`, `source_type: str`,
  `source_id: str`, `module: str | None`, `last_updated: str`, `url: str`
- Split on logical sections first (markdown headers, Jira description
  blocks) before falling back to token-based splitting with the given
  overlap percentage.

### `rag/ingestion/jira_ingest.py`
- Pulls **resolved** Jira tickets and tickets labeled `smoky-ran-*` via the
  Jira API v3 (reuse the same auth pattern as the existing
  `agent/jira_watcher.py` if present in the repo).
- Produces `Chunk` objects with `source_type="jira"`.
- Sync interval: every 15 minutes (expose as a function that can be called
  by a scheduler, do not hardcode a blocking loop).

### `rag/ingestion/confluence_ingest.py`
- Pulls pages from the Confluence spaces listed in
  `CONFLUENCE_SPACE_KEYS` (comma-separated env var).
- Produces `Chunk` objects with `source_type="confluence"`.
- Sync interval: every hour.

### `rag/ingestion/cypress_spec_ingest.py`
- Reads `.cy.ts` files under `tests/generated/` (already-validated specs).
- Produces `Chunk` objects with `source_type="cypress_spec"`, extracting
  the selectors used (`data-test="..."`) into the chunk content so they
  can be reused by future generations.
- Designed to be triggered by a GitHub webhook on push to `tests/generated/`
  — write it as an importable function, not a server.

### `rag/ingestion/openapi_ingest.py`
- Parses the OpenAPI/Swagger spec at `OPENAPI_SPEC_URL` (YAML or JSON).
- Produces one `Chunk` per endpoint (`source_type="openapi"`), including
  method, path, and possible response codes/schemas.

### `rag/embeddings.py`
- Class `EmbeddingClient` with method `embed(texts: list[str]) -> list[list[float]]`.
- Default provider: Voyage AI (`voyage-3`, via `VOYAGE_API_KEY`).
- Keep the provider swappable (e.g. a `provider` constructor arg) since the
  spec also allows Claude Embeddings as an alternative.

### `rag/vector_store.py`
- Class `VectorStore` wrapping Qdrant (`QDRANT_URL`, `QDRANT_API_KEY`,
  `QDRANT_COLLECTION`).
- Methods: `upsert(chunks: list[Chunk], vectors: list[list[float]])`,
  `search(query_vector: list[float], top_k: int, filters: dict | None) -> list[Chunk]`.
- Store all `Chunk` metadata fields (`source_type`, `source_id`, `module`,
  `last_updated`, `url`) as Qdrant payload for filtering and citation.

### `rag/retriever.py`
- Function `retrieve(ticket: dict, top_k: int = 8, rerank_top_n: int = 4) -> list[Chunk]`
  1. Build a query from the ticket's summary + description + acceptance
     criteria.
  2. Embed the query, call `VectorStore.search` for `top_k` chunks.
  3. Rerank down to `rerank_top_n` (cross-encoder if available, otherwise
     a simple Claude-based rerank call — make this swappable).
  4. Return the reranked `Chunk` list.
- Read `RAG_TOP_K`, `RAG_RERANK_TOP_N` from env with the defaults above.

### `rag/prompt_context_builder.py`
- Function `build_context_block(chunks: list[Chunk]) -> str` that renders
  chunks into the exact format below (matching `prompts/rag_context_template.txt`):

  ```
  RETRIEVED CONTEXT (Smoky-RAG):
  [1] ({source_type} {source_id}, module: {module}) "{content}"
  [2] ...

  Use this context to enrich the spec if relevant to the ticket.
  If any context item contradicts the ticket, prioritize the ticket
  and flag the contradiction as a // RAG_CONFLICT comment.
  ```

### `prompts/rag_context_template.txt`
- Store the template shown above as a standalone file, with `{index}`,
  `{source_type}`, `{source_id}`, `{module}`, `{content}` placeholders.

### `evals/ragas_eval.py`
- Uses RAGAS to compute **faithfulness**, **context precision**, and
  **context recall** for a batch of (ticket, retrieved context, generated
  spec) triples.
- Expose a CLI entry point (`python -m evals.ragas_eval --input <path>`)
  that reads a JSONL file of triples and prints/exports scores.
- Thresholds to enforce (fail with non-zero exit code if not met, so this
  can gate CI): faithfulness ≥ 0.85, context precision ≥ 0.80, context
  recall ≥ 0.75.

### `tests/rag/*`
- Unit tests (pytest) for `chunker.py`, `retriever.py`, and
  `prompt_context_builder.py`, using mocked embeddings/vector store — no
  live API calls in tests.

## 4. Integration point (do not skip)

In `agent/spec_generator.py` (existing file — modify, don't duplicate),
insert a call to `rag.retriever.retrieve(ticket)` **before** the Claude
call that generates the Cypress spec, and pass
`rag.prompt_context_builder.build_context_block(chunks)` into the system
prompt as an additional "RETRIEVED CONTEXT" section, appended after the
existing Smoky system prompt rules. If `agent/spec_generator.py` does not
exist yet in the repo, create a `# TODO: wire into spec_generator.py once
Smoky v1.0 agent code lands` note in `rag/retriever.py` instead of
fabricating the integration.

## 5. Config and environment

Add a `rag:` section to `config.yml` (create the file if it doesn't exist)
with keys: `top_k`, `rerank_top_n`, `chunk_size`, `chunk_overlap`,
`sync_intervals` (per source, matching the frequencies in section 3).

Append the following to `.env.example` (create if missing):

```
# Embeddings
VOYAGE_API_KEY=pa-...
EMBEDDING_MODEL=voyage-3

# Vector store
QDRANT_URL=https://your-qdrant-instance:6333
QDRANT_API_KEY=...
QDRANT_COLLECTION=smoky_rag

# Confluence
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net/wiki
CONFLUENCE_EMAIL=you@company.com
CONFLUENCE_API_TOKEN=...
CONFLUENCE_SPACE_KEYS=PROD,QA

# OpenAPI
OPENAPI_SPEC_URL=https://your-api.com/openapi.json

# RAG tuning
RAG_TOP_K=8
RAG_RERANK_TOP_N=4
RAG_CHUNK_SIZE=400
RAG_CHUNK_OVERLAP=60
```

## 6. Dependencies

Add to `requirements.txt` (create entries only if missing): `qdrant-client`,
`voyageai`, `ragas`, `langchain`, `langgraph`, `pyyaml` (for OpenAPI
parsing), `pytest` (if not already present).

## 7. Documentation

Create `rag/README.md` summarizing: what Smoky-RAG does, the ingestion
sources and sync frequencies, how to run `evals/ragas_eval.py` locally, and
a link back to the full `smoky-rag-spec-v1-en.txt` design document (assume
it lives at `docs/architecture/smoky-rag-spec-v1.md` — copy the existing
spec there if it isn't already in the repo).

## 8. Acceptance checklist (verify before finishing)

- [ ] `rag/` folder created with all files listed in section 2
- [ ] Every ingestion module produces `Chunk` objects with the metadata
      fields listed in section 3 (no fewer)
- [ ] `retriever.py` respects `RAG_TOP_K` / `RAG_RERANK_TOP_N` from env
- [ ] `prompt_context_builder.py` output matches the exact template format
- [ ] `evals/ragas_eval.py` enforces the three thresholds and exits
      non-zero on failure
- [ ] No live network calls inside `tests/rag/*` (everything mocked)
- [ ] `agent/spec_generator.py` integration added, or a clear `# TODO`
      left if that file doesn't exist yet
- [ ] `.env.example`, `config.yml`, and `requirements.txt` updated
- [ ] `rag/README.md` created

Do not touch any file outside the scope above (no changes to Steps 1, 3-6
of the existing Smoky flow, no changes to `dashboard/`, `docker/`, or
`.github/workflows/smoky.yml`).

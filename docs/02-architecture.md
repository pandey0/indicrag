# 02 Architecture

## Components
1. **Ingest** (`src/ingest`): reads `data/corpus_manifest.csv`, fetches politely (rate limit, honour robots/terms), stores raw files under `data/raw/` (gitignored) with SHA-256.
2. **Parse/Clean** (`src/parse`): HTML -> text with structure (headings, lists, tables), PDF -> text (check scanned vs digital; OCR only if licence permits and quality justifies), Unicode normalisation for Devanagari/Kannada (NFC, ZWJ/ZWNJ handling), detection and handling of legacy non-Unicode fonts (Kruti Dev, Nudi/Baraha-style), language ID per section. Output carries `parser_version` and `parsed_sha256`; any parser change bumps the version.
3. **Chunk** (`src/chunk`): strategies: fixed(n tokens, overlap), recursive by headings, sentence-window. Every chunk keeps `doc_id, section_path, char_span, lang`. Chunk size is measured with the embedding model's tokenizer (Indic scripts tokenize inefficiently, so character counts and token counts diverge).
4. **Embed + Index** (`src/embed`): embedding model interface; batch embed; write to `chunks(embedding vector)` with HNSW/IVFFlat index; full-text index for lexical search. Postgres has no Hindi/Kannada stemmer: evaluate `simple` config vs character n-grams (pg_trgm) vs BGE-M3 sparse weights.
5. **Retrieve** (`src/retrieve`): dense, lexical, hybrid (RRF fusion), optional cross-encoder rerank.
6. **Generate** (`src/generate`): versioned prompt templates per language, citation format `[c12]` (ids not in context are rejected), refusal rule, provider interface (API model + open model) with timeouts, retries, fallback, response cache.
7. **API** (`src/api`): FastAPI: `POST /ask`, `POST /feedback`, `GET /docs/{id}`, `/healthz`, `/readyz`; OpenAPI spec committed. Middleware: PII scrubber, rate limiter, budget guard, request id, OpenTelemetry. Degrades to retrieval-only when the LLM is unavailable or budget is spent.
8. **Eval runner** (`src/evalrunner`): loads gold JSONL, runs a config over the pipeline, computes metrics, writes `eval/results/<run_id>/`.
9. **Agent** (`src/agent`, phase 3): tool registry, step loop with budget, trace logger, deterministic tool fixtures for tests.
10. **Web** (`web/`): minimal Next.js UI. Results report is a static page / Streamlit, not a custom dashboard.

## Data model (Postgres)
```
documents(id, source_id, url, title, lang, licence_note, fetched_at, sha256, version)
sections(id, document_id, path, text, lang)
chunks(id, section_id, text, lang, char_start, char_end, strategy, embedding vector(d), tsv tsvector)
qa_items(id, lang, register, variant_of, source_kind, question, answer_ref, evidence jsonb[doc_id, parsed_sha256, parser_version, char_start, char_end, quote], qtype, difficulty, writer, labeller, reviewed_by, dataset_version)
runs(id, config_hash, prompt_hash, started_at, git_sha, dataset_version, parser_version, params jsonb)
run_items(run_id, qa_id, retrieved_ids[], answer, citations[], scores jsonb, latency_ms, cost_usd)
feedback(id, question_scrubbed, answer_id, rating, reason, created_at)  -- auto-deleted after 30 days
```
Gold evidence is expressed against a stable `doc_id + char span` (not chunk id) so different chunking strategies can be scored fairly.

## Key design decisions
- Postgres + pgvector first (one system). Revisit a dedicated vector DB only if measurements justify.
- Evidence labelled at span level -> retrieval metrics are chunker-independent.
- LLM provider behind an interface so evaluation can compare models.
- All randomness seeded; results include git SHA and config hash.

## Cross-cutting concerns
Security, privacy, observability, CI and deployment controls: `docs/11-security-and-ops.md`.

## Scale demo: removed
The earlier Kafka/Spark idea is dropped: 30-60 documents do not justify it and it displaces evaluation work. Revisit only after v1.0 if a genuinely large corpus exists.

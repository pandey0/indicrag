# IndicRAG

Retrieval-augmented question answering over Indian citizen-service documents (schemes, pensions, ID, tax, insurance), in **Hindi and English**. It has an evaluation harness with span-level gold evidence, a cited-answer API and web UI, and a small eligibility agent compared against plain RAG.

The goal is to *measure* whether answers are correct, grounded and in the right language, and to report the numbers with their limits.

> **Status: working system, early measurements, dataset not yet released.** 97 pilot questions (57 English, 40 Hindi), validated by one author-reviewer; the last 22 were checked by a model reviewer whose decisions the author adopted. At this size most differences between retrieval methods are within noise or confounded by how the questions were written. See [Results](#results) before quoting any number.

## What is in the repo

| Component | Where | State |
|---|---|---|
| Polite ingestion (HTML, PDF, headless render, OCR), content-addressed storage, licence-aware manifest | `src/ingest`, `src/parse` | working, tested |
| Chunking (fixed / heading), OCR-noise gate, span-hit rule | `src/chunk` | working, tested |
| Retrieval: BM25 (word, char n-gram), dense (multilingual-e5-small, bge-m3), hybrid RRF | `src/retrieve`, `src/embed` | working, tested |
| Eval harness: gold validator, recall@k / MRR / nDCG, paired bootstrap, generation scoring | `src/evalrunner` | working, tested |
| Cited-answer generation with citation validation and refusal; PII scrubbing | `src/generate`, `src/security` | working, tested |
| FastAPI service (`/ask`, `/feedback`, `/docs/{id}`, health) with rate limit, budget cap, kill switch; Next.js UI | `src/api`, `web/` | working, browser smoke test |
| Eligibility agent: deterministic rules engine, validated read-only tools, budgeted loop with JSON traces | `src/agent` | working; no advantage over RAG measured |
| pgvector schema, Docker Compose, CI | `db/`, `docker-compose.yml`, `.github/` | working |

101 tests pass; `ruff` is clean.

## Design choices that matter
- **Gold evidence is a span, not a chunk id** (document hash, parsed-text hash, parser version, character offsets, verbatim quote). A retrieved chunk hits if it contains the span or overlaps it by at least half, so chunking strategies are compared fairly. The validator checks `quote == text[start:end]`.
- **Distractors:** the index holds the whole local corpus (about 2,400 chunks from roughly 400 documents), so every query competes against all documents.
- **Baselines next to RAG:** closed-book, and an oracle with the whole gold document in context. A true whole-corpus long-context run is not done (the corpus is about 1M tokens).
- **No same-family judge.** Generation is scored by number recall against the gold answer, which is objective but weak; faithfulness and fluency are not scored yet.
- **Paired statistics** (paired bootstrap) with the number of comparisons stated.
- **Documents are untrusted input:** 24 prompt-injection cases, PII scrubbing before logging, no personal data stored.

## Results
Full tables and caveats: [`eval/RESULTS.md`](eval/RESULTS.md). Headline, on 93 answerable items:

- **Retrieval:** all six configurations put the gold passage in the top 5 for 95-97% of items; recall@1 ranges from 0.62 to 0.77. e5-small dense is the consistent laggard (char-BM25 and both hybrids beat it with intervals excluding zero; word BM25 is ahead but not clearly); the others are not separated. Questions share vocabulary with their passages, which favours lexical matching, so this is not evidence that BM25 beats dense retrieval in general.
- **Generation (claude-haiku-5-5):** number recall 0.94 with retrieval vs 0.63 closed-book (paired difference +0.31, 95% CI +0.20 to +0.42). With the whole gold document in context: 0.94, so retrieval is not the bottleneck on these items. Abstention on four unanswerable questions: 4/4.
- **Hindi caveat:** closed-book Hindi recall is 0.83 because many items concern well-known national schemes, so the Hindi slice tests retrieval less than the English one.
- **Agent:** on 30 easy single-document eligibility tasks, plain RAG 29/30 vs agent 26/30 (all agent misses were the token budget). No advantage shown.
- **Injection:** 0-2 of 24 cases flagged by an upper-bound check; flagged answers read as reporting, not obeying, the injection.

Limits: one reviewer, no agreement statistic; questions were LLM-drafted from passages and then validated, so they share vocabulary with their evidence (this favours lexical retrieval); the Hindi corpus is mostly Wikipedia while English is mostly myScheme pages, so the languages are different kinds of test.

## Quick start
```
python3 -m venv .venv && .venv/bin/pip install -r requirements-api.txt
make ingest-myscheme            # fetch the corpus locally (not redistributed)
make chunk && make api          # retrieval-only unless ANTHROPIC_API_KEY is set
cd web && npm ci && npm run dev   # UI on :3000, proxies /api to :8000
make test
```
Dense retrieval needs `requirements-embed.txt`. `make results GOLD=...` reproduces the retrieval tables if you have a gold file. Docker: `CLIENT_SALT=$(openssl rand -hex 8) docker compose up --build`. The corpus is fetched under each source's terms and is never committed or baked into images.

## Data and licensing
- The raw corpus and the gold set stay local and gitignored. Nothing is published until each source's licence has been reviewed by a human (`docs/03-corpus-and-licensing.md`). Wikipedia text is CC BY-SA 4.0.
- Dataset card draft: `docs/17-dataset-card-draft.md`. Labelling guide: `docs/04-labelling-guide.md`.

## Limitations and responsible use
- A reference implementation, **not** a production service: no authentication, multi-tenancy or SLA.
- Not legal, financial or official eligibility advice. Rules change; answers carry the source's valid-as-of date, and some gold answers reflect an older version of a scheme.
- No model training, no voice, no collection of personal data.

## Scope decision: Kannada is out of v1
Kannada was an original goal. It is deferred because the project has no native Kannada reader to validate questions or answers. The fetched Kannada documents and the English-Kannada alignment tooling (`scripts/align_kn_candidates.py`, `src/evalrunner/align.py`) remain as groundwork. No result here covers Kannada.

## Docs
Design and plans live in `docs/`: scope (`01`), architecture (`02`), evaluation plan (`05`), security and ops (`11`), parse findings (`12`), chunking (`13`), retrieval (`14`), app (`15`), agent (`16`).

## Author
Arpit Pandey: data engineering, evaluation, backend, frontend and agents. Contributions welcome: label corrections, sources with clear licences, and Hindi reviewers. Open an issue.

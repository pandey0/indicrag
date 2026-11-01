# IndicRAG

**A Hindi / Kannada / English benchmark and reference system for retrieval-augmented question answering (RAG) over Indian citizen-service documents, with a tool-using agent layer.**

> **Status: pipeline implemented, dataset labelling in progress, no results yet.** Implemented and tested (CI): ingestion with OCR, chunking, BM25 / dense / hybrid retrieval, retrieval metrics with paired bootstrap, a gold-data validator, a cited-answer generator with refusal, PII scrubbing, and a FastAPI reference app with a minimal web UI, and an eligibility-focused agent core (deterministic rule engine, validated tools, budgeted loop with traces; untested against a real model). Not yet done: the human-validated gold set (the current bottleneck), LLM answer evaluation and the agent. Results will be added to `eval/RESULTS.md` only when they exist.

## Problem
Government portals, banks and support desks in India need assistants that answer in Hindi, Kannada and English. Teams building them struggle to *measure* whether answers are correct, grounded in sources, and in the right language. Most RAG demos ship with no measurements, and regional-language evaluation data is limited (to be confirmed by a literature review, see `docs/10-references.md`).

IndicRAG asks: *given real public-service documents, how well do different RAG designs work in three languages, and where do they fail?*

## What it delivers
1. **Dataset:** question / answer / evidence-span items in hi and en (target 150 per language, minimum 100) plus a Kannada slice derived from official kn/en parallel documents (aligned and partially native-verified, reported separately), including unanswerable, colloquial, romanized and code-mixed questions. Released with a dataset card.
2. **Evaluation harness:** reproducible runs from a YAML config; retrieval, faithfulness, citation, abstention, robustness and cost metrics, with paired statistics.
3. **Reference app:** FastAPI + Next.js. Every answer shows cited passages, the source's valid-as-of date and a "not official advice" notice.
4. **Agent layer:** tool-calling agent for eligibility / document-list tasks, evaluated on task success and tool-call accuracy against plain RAG.

## How it works
```
Public docs (HTML/PDF)                       Gold labels (QA + evidence spans)
      |                                                  |
 [Ingest] -> [Parse/Clean] -> [Chunk] -> [Embed] -> Postgres + pgvector
                                                       |            |
                                             [Eval runner] <-> [RAG service (FastAPI)]
                                                       |            |
                                          results + report     [Web UI (Next.js)]
                                                                    |
                                                             [Agent layer]
```
Design points that matter:
- **Span-level gold evidence** (with verbatim quote and parser/version hashes), so retrieval is scored fairly across different chunking strategies.
- **Distractor pool:** extra unlabelled documents in the index so retrieval is not trivially easy.
- **Honest baselines:** every table includes closed-book and long-context baselines, not just RAG variants.
- **Paired statistics + power check** instead of eyeballing small differences.
- **Per-language LLM-judge validation** against human labels; judge scores are never reported alone.
- **Controls for a public demo:** rate limits, budget cap, PII scrubbing, prompt-injection tests (`docs/11-security-and-ops.md`).

## Roadmap (12 weeks)
| Phase | Weeks | Deliverables |
|---|---|---|
| 1 Data + eval | 1-4 | corpus manifest with licence checks, parse-feasibility study, ingestion pipeline, dataset v0.1, baseline retrieval + generation metrics |
| 2 App | 5-8 | FastAPI service, minimal UI with citations and feedback, ablations, deployed demo, results report |
| 3 Agent + release | 9-12 | tool-calling agent and evaluation, dataset v1.0 on Hugging Face, write-up |
Details, gates and pivot criteria: `docs/06-roadmap-12-weeks.md`.

## Tech stack
Python 3.11+, FastAPI, Pydantic, Postgres + pgvector, multilingual open embedding models (e.g. BGE-M3, multilingual-e5), pluggable LLM providers (API + open model), Next.js + TypeScript, Docker Compose, GitHub Actions, OpenTelemetry. Model choices are verified at implementation time.

## Repository layout
```
docs/        design: scope, architecture, corpus & licensing, labelling guide, evaluation plan,
             roadmap, agent phase, risks & ethics, references, security & ops
data/        schema/, labelling template, corpus_manifest.csv (raw/processed gitignored; gold published)
eval/        config.example.yaml, results/ (summary tables only)
src/         ingest, parse, chunk, embed, retrieve, generate, security, api, evalrunner  (implemented); agent (planned)
web/         Next.js 16 / TypeScript UI (ask, cited sources, feedback, disclaimer); browser smoke test in web/e2e
```

## Run locally
```
pip install -r requirements-api.txt && make ingest-myscheme   # corpus stays local (not redistributed)
make chunk && make api                                        # retrieval-only unless ANTHROPIC_API_KEY is set
cd web && npm ci && npm run dev                               # UI on :3000, proxies /api to :8000
# or: CLIENT_SALT=$(openssl rand -hex 8) docker compose up --build
make test
```
The corpus is fetched by the ingest scripts under each source's terms and is never committed or baked into images.

## Results
Not available yet. Planned: retrieval and generation tables per language, baseline comparisons, failure taxonomy, judge-human agreement, latency and cost.

## Scope, limitations and responsible use
- Uses only public documents whose licence/terms permit it; the licence decision for each source is recorded in the manifest. Text is redistributed only where allowed; otherwise labels, spans and fetch scripts are released.
- A reference implementation with measured quality and basic abuse/privacy controls, **not** a production service (no authentication, multi-tenancy or SLA).
- Not legal, financial or official eligibility advice. Government rules change; answers carry the source's valid-as-of date.
- No model training, no voice, no collection of personal data.

## Author
Arpit Pandey: building this end to end (data engineering, evaluation, backend, frontend, agents). Each language's labels need a native-speaker annotator; who labelled and reviewed what will be credited in the dataset card (`docs/04-labelling-guide.md`).

## Contributing
Corrections to labels, new sources with clear licences, and Hindi/Kannada reviewers are welcome once the dataset is public; open an issue.

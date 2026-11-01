# 01 Scope and requirements

## Goals
G1. Release a labelled multilingual (hi, kn, en; >=100 items/language, target 150) QA-with-evidence dataset over public Indian citizen-service documents.
G2. Provide a reproducible harness that scores RAG variants (retrieval + generation) on that dataset.
G3. Provide a deployed reference app (citations, language handling, feedback).
G4. Provide an agent layer with tools, evaluated on tool-call and trajectory quality.
G5. Publish findings (results table, failure analysis, blog).

## Language coverage policy
The author reads/writes English and Hindi (to be confirmed per labelling session); no Kannada reader/writer is currently on the project. Therefore:
- **en, hi:** natively labelled by the author (hi: reviewed by a second Hindi reader on a sample).
- **kn (DEFERRED, decision 2026-11-01: out of v1; see below):** **aligned-parallel only**: Kannada items are derived from English items where an official Kannada/English parallel document exists, via cross-lingual span alignment, with automated consistency checks and a native-speaker check on a sample. Kannada results are always reported as a separate slice labelled "aligned, partially verified"; they are never described as natively authored. No native-register Kannada (colloquial, code-mixed, romanized) items unless a native annotator joins.

## Non-goals (v1)
Model training or fine-tuning; voice/ASR/TTS; user accounts or PII; legal/financial advice; scraping sources whose terms forbid it; claims of production usage.

## Functional requirements
FR1 Ingest documents from a manifest of sources (HTML/PDF), store raw + parsed text with provenance (URL, fetch date, licence note, language, hash).
FR2 Chunking strategies are pluggable (fixed, recursive/semantic, heading-aware) and recorded in each run.
FR3 Embedding + indexing in Postgres/pgvector with metadata filters (language, source, doc version).
FR4 Retrieval variants: dense, lexical (Postgres FTS with tested Indic tokenization), hybrid, optional reranker. Index includes a distractor pool of unlabelled docs.
FR4b Baselines in every report: closed-book and long-context in addition to RAG.
FR5 Answer generation with mandatory citations (chunk ids), refusal when evidence is missing, answer in the user's language.
FR6 Evaluation runner takes a YAML config and the gold set, outputs per-item and aggregate JSON + CSV summaries.
FR7 Web UI: ask question, see answer + cited passages, give thumbs up/down + reason, language selector.
FR8 Results report (static page or Streamlit): compare runs, per-language and per-question-type breakdown, failure list. No bespoke dashboard app.
FR9 Agent (phase 3): tools such as `search_docs`, `get_document_section`, `eligibility_checklist` (rule-based over extracted fields), `translate_check`; max steps and budget limits; full trace logging.

## Non-functional requirements
NFR1 Reproducibility: pinned dependencies, seed values, versioned dataset (semver), config hash in each result file.
NFR2 Cost control: per-run token/cost accounting; a small "smoke" eval (<=20 items) runs in CI cheaply.
NFR3 Latency targets (to be measured, not promised): report p50/p95.
NFR4 Privacy: PII scrubbing before any logging/storage, opt-in feedback, 30-day retention, no IDs/IPs stored (see docs/11).
NFR5 Safety: every answer shows sources, the document's valid-as-of date and a "not official advice" notice.
NFR6 Abuse/cost: provider spend limit, daily budget cap with retrieval-only degradation, per-client rate limit, input caps (docs/11).
NFR7 Observability: structured logs and OpenTelemetry traces with tokens/cost/prompt version.
NFR8 Security: documents treated as untrusted; read-only agent tools; injection test set with attack-success metric.
NFR9 Engineering hygiene: lint, types, golden parser tests, gold-set schema + span validation, CI smoke eval from cached responses.

## Positioning
Reference implementation with measured quality and basic abuse/privacy controls. NOT a production service (no auth, multi-tenancy, SLA).

## Acceptance criteria
- `make eval CONFIG=eval/configs/baseline.yaml` reproduces the published baseline table exactly with the response cache, and within measured variance without it.
- Dataset card documents sources, licences, labelling process, agreement score, known limits.
- Demo is reachable; README has architecture + results; blog post published.

## Decision log: Kannada out of v1 (2026-11-01)
The author does not want Kannada in v1 and no native Kannada checker is available. This triggers the pre-decided pivot in `docs/06` ("ship Hindi+English v1"). Consequences: v1 covers English and Hindi only; no Kannada gold, no Kannada results, no Kannada claims anywhere. Kannada corpus files and the alignment/native-check tooling stay as documented groundwork. Reinstating Kannada requires a native-speaker validator, then following the aligned-parallel protocol in `docs/04`.

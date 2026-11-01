# 11 Security, privacy, observability and engineering hygiene

Purpose: close the gap between "research prototype" and "something a team could run". Scope is a public reference demo + eval harness, NOT a multi-tenant product. Section 9 states what is deliberately not covered.

## 1. Abuse and cost protection (public demo)
A public endpoint backed by a paid LLM key is a cost-abuse target.
- Provider-side hard spend limit on the demo API key (separate key from eval key). Primary control; code limits are secondary.
- Global daily budget counter (`DEMO_DAILY_BUDGET_USD`); when exhausted, `/ask` degrades to retrieval-only (passages, no generation) and the UI says so.
- Per-client rate limit (token bucket, e.g. 10 req/min, 100/day) keyed on a salted, hashed IP held in memory/Redis with TTL; never written to the DB or dataset.
- Input caps: question <= 500 chars; reject non-text; output cap `max_tokens`; retrieval k capped server-side.
- Optional bot check (e.g. Cloudflare Turnstile) if abuse is observed.
- Kill switch env var (`DEMO_ENABLED=false`).
- Smoke test in CI asserts the limiter and budget cap trigger.

## 2. Prompt injection and untrusted content
Documents are untrusted input (indirect injection).
- Retrieved text is placed in clearly delimited data blocks; system prompt states that passages are data, never instructions.
- Citations must reference retrieved chunk ids; answers citing ids not in the context are rejected (also a faithfulness check).
- Agent tools are read-only and side-effect free (no network writes, no code execution, no file access outside the corpus). Tool args validated against Pydantic schemas; tool outputs length-capped.
- Add an `injection` test set to the eval (>= 10 docs/passages containing instructions such as "ignore previous instructions"); metric: attack success rate (answer deviates or leaks the system prompt). Report it.
- Never put secrets in prompts.

## 3. Privacy / PII (India DPDP Act context; not legal advice, verify with qualified counsel before public launch)
- UI warns: "Do not enter Aadhaar, phone, PAN, bank or other personal details."
- Server-side scrubber (regex: 12-digit Aadhaar patterns, 10-digit mobiles, PAN, emails, IFSC/account-like numbers) runs BEFORE logging, tracing or storing feedback. Raw question text is not persisted unless scrubbed.
- Feedback is opt-in per submission; stores scrubbed question text, rating, reason, timestamp. No user id, no IP, no cookies for tracking.
- Retention: feedback and traces auto-deleted after 30 days unless exported anonymised for failure analysis. Provide a contact for deletion requests.
- Feedback is NEVER merged into the gold dataset automatically; any reuse goes through manual review.
- LLM provider terms checked: confirm API data is not used for training; record in the dataset/app card.

## 4. Observability
- Structured JSON logs with request id; no raw PII (after scrubbing).
- OpenTelemetry traces per request: retrieve -> rerank -> generate spans, with tokens, cost, model, prompt version. Self-hostable viewer (Langfuse or Jaeger); pick one in phase 2.
- Metrics: latency p50/p95 per stage, tokens, cost, refusal rate, citation-validity rate, feedback ratio, error rate.
- Prompt templates are versioned files; the prompt hash is recorded in every trace and every eval run.
- Alerts (even if just a log line/email in v1): budget > 80%, error rate spike, refusal rate shift.

## 5. Reliability
- Timeouts and bounded retries with jittered backoff on provider calls; provider fallback (API model -> open model) via the provider interface.
- Graceful degradation: LLM down or budget exhausted -> retrieval-only response.
- `/healthz` (process) and `/readyz` (DB + embedding model loaded).
- Idempotent ingestion keyed by raw sha256; re-running is safe.

## 6. Engineering hygiene and CI
- Python: `uv` (or pip-tools) lockfile, ruff (lint+format), mypy on `src/`, pytest. Pre-commit hooks for ruff, schema check, secret scan (gitleaks).
- CI (GitHub Actions) on every PR: lint, type check, unit tests, parser golden tests (Hindi/Kannada fixtures incl. a legacy-font case), gold-set JSON Schema validation + span checks (every `quote` matches the parsed text at its span), smoke eval (<= 20 items, uses committed response cache so no API spend), Docker build, dependency audit (pip-audit, npm audit), Dependabot.
- Web: TypeScript strict, ESLint, a Playwright smoke test (ask a question, see a citation).
- DB migrations with Alembic; no manual schema edits.
- Conventional commits; every result file records git SHA, config hash, prompt hash, dataset version, parser version.

## 7. Data operations
- Lineage: manifest row -> raw file (sha256) -> parsed text (parsed_sha256, parser_version) -> sections -> chunks -> gold spans. Any link change is detectable.
- Dataset versioning: semver git tags + HF dataset revisions + changelog; gold files immutable once tagged.
- Parser upgrades create a new `parser_version`; a migration script re-anchors spans from `quote` text and reports unmatched items for manual fix.
- Large artifacts (raw docs, embeddings) are reproducible from the manifest via `make ingest`; not committed.

## 8. Deployment
- Docker Compose (api, db, web) identical locally and in the demo; config through env vars; secrets via the host's secret store, never in the repo or image.
- Image tags pinned to git SHA; rollback = redeploy previous tag. Measure cold start and memory (embedding model on CPU must fit the free tier; otherwise use a hosted embedding endpoint for the demo and say so).
- TLS and security headers via the host/proxy; CORS restricted to the web origin.

## 9. Deliberate non-goals (say this in the README)
No authentication or multi-tenancy, no SLA/HA or autoscaling, no formal threat model or pen-test, no compliance certification, no real user data. The project supports the claim "reference implementation with measured quality and basic abuse/privacy controls", not "production service".

## Injection harness status
`data/injection/cases.jsonl` (12 en/hi cases, canary strings) and `src.evalrunner.injection` implement the attack-success-rate metric. CI tests use scripted providers and show what the pipeline does and does NOT guarantee: it withholds answers without valid citations (so an obedient but uncited reply never reaches the user), but a model that obeys the injection and still cites a passage passes through, so ASR for a real model must be measured (`python -m src.evalrunner.injection`, needs `ANTHROPIC_API_KEY`) and reported with its small n. No such measurement exists yet.

## Injection ASR, first real-model measurement (claude-haiku-5-5, 2026-11-01)
12 cases (9 en, 3 hi), full answering pipeline, k=1 injected passage: **attack success 0/12** (Wilson 95% CI 0.00-0.24). 8 answered cleanly without the canary, 4 were withheld (3 `model_no_answer`, 1 `uncited`). With n=12 and simple, single-turn, instruction-only injections this only rules out a high attack rate; it says nothing about adaptive attacks, other models or the agent path. Not evidence of robustness.

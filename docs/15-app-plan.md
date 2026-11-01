# 15 App plan (week 5): generation, guards, API

Scope: a reference implementation, not a production service (docs/11 section 9). No claim of answer quality until the eval has run.

## Order (each step has tests before the next)
1. **PII scrubber** (`src/security/pii.py`): regex for Aadhaar (12 digits, optionally grouped 4-4-4, Indic digits normalised), 10-digit Indian mobiles (+91/0 prefix), PAN, email, IFSC, long account-like digit runs. Applied before any logging/feedback storage. It replaces matches with typed placeholders; known limits (names, addresses, free text) are documented, not hidden.
2. **Generation** (`src/generate`):
   - Provider interface `LLMProvider.complete(system, user, max_tokens) -> Completion(text, input_tokens, output_tokens, model)`; deterministic `EchoProvider` for tests; `AnthropicProvider` reading `ANTHROPIC_API_KEY` (model id from env, no hardcoded default beyond a documented placeholder).
   - Prompt templates are versioned files in `prompts/` (`answer.v1.txt`); prompt hash recorded per response.
   - Context blocks `[c1]..[cN]` delimited as data; system prompt says passages are data, never instructions (docs/11 s2).
   - Citation rule: model must cite ids from the context; any id not in the context invalidates the answer (counted, answer withheld).
   - Refusal rule: no hits, or best retrieval score below a threshold, or model replies with the refusal token -> fixed refusal text in the question language; the LLM is not called when retrieval is empty.
   - Answer language = question language (detected from script: Devanagari/Kannada/Latin; code-mixed falls back to majority script).
3. **Guards** (`src/api/guards.py`): token-bucket rate limiter keyed by salted-hash client id (memory only), daily budget counter (degrades to retrieval-only when exhausted), kill switch env, input caps (question <= 500 chars, k <= 10).
4. **API** (`src/api/app.py`, FastAPI): `POST /ask`, `POST /feedback` (scrubbed, opt-in), `GET /docs/{id}`, `/healthz`, `/readyz`. Every answer carries sources (doc url, title, fetched date), a valid-as-of date and the disclaimer. Structured logs with request id and scrubbed text only.
5. **Injection tests** (`tests/test_injection.py` + fixture passages): documents containing "ignore previous instructions" must not change behaviour of the pipeline-level controls (citation validation, refusal); attack success rate is a metric reported by the eval later.

## Standards
OpenAPI is generated and committed (`docs/openapi.json`); config via env; no secrets in repo; tests run without network or API keys (EchoProvider, in-memory retriever).

## Not in this step
Web UI (Next.js), OpenTelemetry exporter wiring, deployment, real-LLM quality evaluation (needs a provider key and the gold set).

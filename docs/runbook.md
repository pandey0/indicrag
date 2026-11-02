# Runbook

All commands assume the repo root. Use system `python3` for LLM runs and `.venv/bin/python` for dense retrieval and embeddings. Never print or commit an API key; pass it per command, for example `ANTHROPIC_API_KEY="$(cat path/to/keyfile)" python3 -m ...`.

## Rebuild after the corpus changes
1. `make ingest-myscheme` (or `python3 -m src.ingest run --sources data/sources_wikipedia3_hi.csv`). Idempotent; raw files are content-addressed.
2. `python3 -m src.chunk build` (`make chunk`).
3. `.venv/bin/python -m src.embed build --model intfloat/multilingual-e5-small` and again with `--model BAAI/bge-m3`.
4. Chunks and embeddings must be rebuilt together; stale embeddings silently misalign with chunks.

## Reproduce the numbers
- Gold check: `python3 -m src.evalrunner.validate_gold data/gold/dev.jsonl --check-answer-numbers` must print `0 problems`.
- Retrieval: `.venv/bin/python scripts/run_all_retrievers.py --gold data/gold/dev.jsonl --models intfloat/multilingual-e5-small BAAI/bge-m3` (without `--models` bge-m3 is skipped).
- Generation: `python3 -m src.evalrunner.run_generation --modes rag closed_book long_doc --out run.json`. Runs over about 500 s must go in the background. Repeat runs differ by about 0.02 in number recall.

## Review new gold items
`python3 scripts/review_drafts.py data/gold/drafts/*.jsonl --list 10` shows pending drafts; `--decide "id=a,id=r,id=e:new q::new a" --reviewer <name>` applies decisions. A save the validator rejects prints `NOT SAVED`; check the count in the summary line.

## Run the API
`make api` (port 8000). `GET /healthz` is liveness; `GET /readyz` is readiness. Without `ANTHROPIC_API_KEY` it serves retrieval only. Controls: rate limit, spend budget and a kill switch in `src/api/guards.py`.

## Known failure modes
| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: sentence_transformers` | Ran dense code with system python | Use `.venv/bin/python` |
| `ModuleNotFoundError: fitz` in tests | Missing `requirements-spike.txt` | Install it |
| `401 invalid x-api-key` | Wrong or rotated key | Fix the key file; do not retry blindly |
| Reply cut off, empty answer | `max_tokens` too small for the model | Provider retries once with 4x budget; raise the budget if it persists |
| Model rejects `temperature` | Current Claude models do not accept it | Do not pass it |
| Pages "ok" but empty | JS-rendered shells | `Config.min_content_chars` and the h1 wait in `src/ingest/render.py` exist for this; sample real documents |
| Indic digits not matching | Number normalisation | `numbers()` in `src/evalrunner/align.py` maps Indic digits and drops leading zeros |

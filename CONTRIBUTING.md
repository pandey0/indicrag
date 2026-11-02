# Contributing

1. `python3 -m venv .venv && .venv/bin/pip install -r requirements-api.txt -r requirements-spike.txt ruff` (dense retrieval also needs `requirements-embed.txt`).
2. Before a PR: `make test` and `.venv/bin/python -m ruff check src tests scripts`. Tests must not touch the network, call paid APIs or download models (inject fakes).
3. Any number in the docs needs a script that reproduces it and its sample size and limits next to it (`eval/RESULTS.md` is the model). No claim before the deliverable exists.
4. Changing gold data: items go through `scripts/review_drafts.py` (a draft stays `unreviewed` until a human decides). Never mark items agreed on someone else's behalf, and never edit `data/gold/dev.jsonl` by hand; the validator (`python -m src.evalrunner.validate_gold data/gold/dev.jsonl --check-answer-numbers`) must report 0 problems.
5. Adding a source: check licence, robots and terms first (`docs/03-corpus-and-licensing.md`); the manifest `redistribute` flag defaults to `false`.
6. Decisions that change behaviour or evaluation need an ADR in `docs/adr/`.
7. Never commit keys. API keys come from the environment.

Useful contributions: label corrections, Hindi reviewers, sources with clear licences, harder questions.

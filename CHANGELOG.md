# Changelog
All notable changes to this project. Format: Keep a Changelog; versioning: SemVer.

## [Unreleased]
- Documentation set modelled on a production-style repo: README rewrite, ADRs, architecture, runbook, critique, scorecard, contributing, changelog.

## [0.1.0] - 2026-11-02
### Added
- Ingestion: polite fetch, headless render, PDF/HTML parse with heading paths, OCR, content-addressed storage, licence-aware manifest.
- Chunking (fixed / heading), span-hit rule, OCR-noise gate.
- Retrieval: BM25 word and char n-gram, dense (multilingual-e5-small, bge-m3), hybrid RRF.
- Eval harness: gold validator (`quote == text[start:end]`), recall@k / MRR / nDCG, paired bootstrap, generation scoring by number recall, closed-book and oracle (`long_doc`) modes.
- Generation with citation validation and refusal; PII scrubbing.
- FastAPI service with rate limit, budget cap and kill switch; Next.js UI; pgvector schema; Docker Compose; CI.
- Tool-using eligibility agent (rules engine, validated tools, budgeted loop) and a prompt-injection test set (24 cases).
- Pilot gold set of 100 items (57 English, 43 Hindi), published with `data/gold/NOTICE.md`.
### Changed
- Number matching now ignores leading zeros of integers and maps Indic digits to ASCII.
### Decisions
- Kannada is out of v1 (author cannot validate it). MIT licence for the code.
### Known limits
- One reviewer, no agreement statistic; whole-corpus long-context baseline not run; agent task criteria not human-reviewed.

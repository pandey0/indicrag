# Production scorecard
A 14-point checklist for how production-like this repo is. Status is what was verified, with the command or file. The project is a **reference implementation, not a production service**, so low scores on operations rows are expected and stated, not hidden.

Legend: done = verified here; partial = some evidence; todo = not done.

| # | Area | Status | Evidence / what is missing |
|---|---|---|---|
| 1 | Repo hygiene | done (no release tag yet) | README with diagram, quick start and honest limits; `LICENSE` (MIT); `CONTRIBUTING.md`; `CHANGELOG.md`; ADRs 0001-0006; pre-commit config; Dependabot. No semver tag pushed. |
| 2 | Code quality | partial | `ruff check src tests scripts` clean. No `mypy`/strict typing, no formatter check. |
| 3 | Tests | partial | `make test`: 96 pass, 5 skip on a clean clone (the skips need the local corpus). Unit tests with fakes, plus a 24-case injection set and an agent task set. No integration/e2e in CI, no coverage report, no failure-injection suite. |
| 4 | CI | partial | `.github/workflows/ci.yml`: lint, tests, web typecheck/build/`npm audit`; last run green (`gh run list`). No container scan, Python dependency audit or secret scan in CI (gitleaks is in pre-commit only). |
| 5 | CD | todo | No release workflow, staging or rollback. |
| 6 | Containers | partial | `Dockerfile` (python:3.11-slim, non-root `USER app`, `HEALTHCHECK`), `docker-compose.yml`. Not multi-stage, base image not digest-pinned, not scanned. |
| 7 | Infrastructure as code | todo | No Terraform or Kubernetes manifests. |
| 8 | Observability | partial | `/healthz`, `/readyz`, logging with PII scrubbing, JSON traces for the agent. No Prometheus metrics, OpenTelemetry or dashboards. |
| 9 | Reliability | partial | Rate limit, spend budget, kill switch, provider retry on truncation, per-request budget in the agent loop. No timeouts/backoff audit, no chaos results, no SLO. |
| 10 | Security | partial | `docs/11-security-and-ops.md` threat model, PII scrubbing, 24-case injection measurement (upper bound), documents treated as untrusted. No authN/Z, no ASVS self-check. |
| 11 | Data | partial | pgvector migration (`db/migrations/0001_init.sql`), content-addressed storage, gold validator with hash and quote checks. No backup/restore test or retention job. |
| 12 | Performance | todo | No load test or latency percentiles. Token use is reported in `eval/RESULTS.md`; latency is not. |
| 13 | Docs | done (with stated limits) | README, architecture, runbook, critique, ADRs, results with limits, dataset card draft, OpenAPI (`docs/openapi.json`). Dataset card is still a draft. |
| 14 | Demo | todo | A browser smoke test exists; no demo video, live demo or cost report. |

**Count:** done 2 (rows 1, 13), partial 8 (rows 2, 3, 4, 6, 8, 9, 10, 11), todo 4 (rows 5, 7, 12, 14).

## Rules this repo follows
- Numbers over adjectives: every figure in the README comes from a script and appears with its sample size in `eval/RESULTS.md`.
- Honest scope: pilot data, one reviewer, no users or revenue claimed.
- Safety: licences and terms are checked before ingesting; `redistribute` defaults to `false`; known gaps are listed in [`docs/critique.md`](docs/critique.md).

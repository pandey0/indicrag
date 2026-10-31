# 06 Roadmap (12 weeks, ~9 h/week = ~108 h budget; keep the gates)

## Time budget (sanity check)
| Item | Hours |
|---|---|
| Parse-feasibility spike + corpus manifest + distractor pool | 14 |
| Parsing, chunking, indexing, retrieval | 14 |
| Labelling v0.1 (100 items x 3 langs = 300; LLM-drafted + human-validated ~12/h, hand-written ~6/h; mix ~9/h) | 33 |
| Second annotator coordination + agreement analysis | 4 |
| Eval runner, stats, baselines, judge calibration | 16 |
| API + minimal UI + report page + security/ops controls | 18 |
| Agent + task set + eval | 7 |
| Dataset v1.0 card, release, blog | 6 |
Kannada items are derived by alignment (cheap for the team) but need a native-speaker sample check (~3-4 h of an outside person's time, not counted here).
Total ~112 h: no slack. Anything extra (dashboard, scale demo, more items) displaces something above. Pre-decided cuts, in order: (1) v1.0 stays at 100 items/lang, (2) agent shrinks to eligibility-only tasks, (3) drop Kannada cross-lingual items.

## Phase 1: Data + eval (weeks 1-4)
W1: Repo/CI skeleton. **Parse-feasibility spike BEFORE choosing sources**: fetch 15-20 candidate docs, test extraction on Hindi + Kannada (legacy-font PDFs, scanned PDFs, tables); licence/robots check. Gate: manifest has verdicts; >=5 docs per language parse to correct Unicode text; go/no-go on OCR; if Kannada sources fail parsing, decide: OCR, HTML-only sources, or reduce to Hindi+English (documented).
W2: Parse all chosen docs (pinned parser_version), build distractor pool, chunking v1, pgvector schema + Alembic, labelling pilot (10 items/lang) with separate question writer. Gate: guide revised; golden parser tests green.
W3: Label to 50 items/lang; embeddings + baseline retrieval; power estimate from pilot variance. Gate: first retrieval numbers incl. closed_book.
W4: Label to >=100 items/lang; second-annotator sample (>=20%); baseline generation + long_context baseline + per-language judge calibration. Gate: dataset v0.1 tagged; baseline table committed. KILL CHECK: <100 items/lang or baseline cannot run -> publish dataset + pipeline as-is, stop expanding scope.

## Phase 2: App (weeks 5-8)
W5: FastAPI (`/ask`, `/feedback`, `/healthz`, `/readyz`), per-language prompts, citations, refusal, PII scrubber, rate limit + budget cap, tracing.
W6: Ablations (chunking, embeddings, lexical tokenization, hybrid) with paired stats; failure taxonomy v1.
W7: Minimal Next.js UI (ask, cited passages, feedback, language selector, "valid as of" date, disclaimer) + static/Streamlit results report. No bespoke dashboard.
W8: Deploy demo (cost/abuse controls verified), load/latency test, cost report, README with architecture + results. Gate: public demo + results. KILL CHECK: no ablation shows a clear difference -> publish the negative result; skip rerank experiments.

## Phase 3: Agent + release (weeks 9-12)
W9: Tool registry, agent loop with budgets, trace logging, deterministic tool tests, injection tests.
W10: >=30 task set focused on eligibility/rules (find scheme -> extract criteria -> evaluate_rules -> documents list); report with CIs and state n is small. Compare plain RAG vs agent.
W11: Dataset v1.0 (agreement stats, dataset card, licence statement), HF upload.
W12: Blog post, short demo video, announce, README polish.

## Weekly rhythm
Mon-Thu 30-60 min; weekends 3-4 h block. `JOURNAL.md`: one paragraph/week (shipped, broke, next).

## Kill / pivot criteria (explicit)
- Licensing blocks redistribution of text: release labels + spans + quotes + fetch scripts + archived snapshot URLs only.
- No native Kannada checker found, or no usable kn/en parallel pairs: ship Hindi+English v1; Kannada as an experimental, unverified slice or documented follow-up.
- Labelling slower than 6 items/hour at quality: use LLM-drafted + validated items, cut cross-lingual.
- API cost over budget: open models + smaller judge sample (never skip judge calibration).
- Time shortage: stop after phase 2; still a complete, evaluated project.

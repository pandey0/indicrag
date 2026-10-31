# 05 Evaluation plan

## What is measured
**Retrieval** (against gold evidence spans; a retrieved chunk "hits" if it overlaps a gold span by >=50% of the span or contains it). Index = labelled docs + **distractor pool** (see 03):
- recall@k (k=1,3,5,10), MRR, nDCG@10; also document-level recall@k (right doc found)
- per language, per question type, per difficulty, per register (formal / colloquial / code-mixed / romanized / noisy)
**Generation** (on answerable items):
- faithfulness: fraction of answer claims supported by cited chunks (claim extraction + verification; judge calibrated against human labels)
- answer correctness vs gold (judge with rubric + human spot-check)
- citation accuracy: cited chunk ids exist in context AND contain the supporting text
- language match rate (answer language == question language, unless asked otherwise)
**Abstention** (unanswerable items): refusal precision/recall.
**Robustness**: metric drop on noisy/romanized variants vs their base item; attack success rate on the injection set (see 11).
**System**: latency p50/p95 (retrieval, generation, total), tokens and cost per query.

## Required baselines (every results table includes all)
| Baseline | Why |
|---|---|
| closed_book | LLM answers with no retrieval; shows what retrieval adds and exposes memorised/hallucinated answers |
| long_context | Whole corpus (or per-language subset) placed in context. With 30-60 docs this may beat RAG; the honest comparison teams actually need (report cost and latency too) |
| rag_baseline | Fixed 512-token chunks, one multilingual embedding, dense top-5, plain prompt |
Everything else is compared to rag_baseline, and RAG vs long_context is reported explicitly.

## Ablation matrix (each row is one config in `eval/configs/`)
| Axis | Values |
|---|---|
| Chunking | fixed-256/512 (tokens counted with the embedding model's tokenizer), heading-aware, sentence-window |
| Embedding | BGE-M3, multilingual-e5, one more retrieval-trained multilingual model (verify current options). IndicBERT is NOT a sentence-embedding model: include only if a retrieval-tuned variant is verified, otherwise omit |
| Retrieval | dense, lexical, hybrid(RRF), hybrid+rerank (multilingual cross-encoder; verify). Lexical: Postgres FTS has no Hindi/Kannada stemmer, so test `simple` config vs character n-gram tokenization vs BGE-M3 sparse output |
| Language handling | none, query translation to English, answer translation check |
| LLM | one API model, one open model |
Do NOT run the full cross product: one-factor-at-a-time from rag_baseline, then 2-3 promising combinations.

## Statistics
- All comparisons are PAIRED (same items): paired bootstrap (10k resamples) for differences with 95% CI; McNemar for binary outcomes. Unpaired overlapping CIs are not used to claim significance.
- Power check BEFORE ablations: `eval/power.py` estimates the smallest detectable difference for the actual n and baseline variance from the pilot. Publish it. Dataset floor is 100 items/language (target 150); with n=100 only differences of roughly 8-10 points are detectable, so smaller ones are reported as "no evidence of difference".
- Report n per language and per slice; do not report slices with n<15 except as anecdotes.
- Fix seeds; LLM stages at temperature 0; repeat 3x and report variance.
- Multiple comparisons: label ablations as exploratory vs pre-registered (write the hypotheses in the config's PR/commit before running).

## LLM-as-judge
- Different model family than the generator, written rubric (`eval/rubrics/`), prompt version recorded.
- Judge validity is measured PER LANGUAGE (Hindi, Kannada, English separately): human-labelled sample of >=30 items/language (>=15% minimum), report judge-human agreement (Cohen's kappa / accuracy). If Kannada agreement is poor, say so and fall back to human scoring or extractive metrics for Kannada rather than reporting unreliable judge scores.
- Never report judge scores without the agreement figure next to them.

## Reproducibility
- LLM calls go through a response cache keyed by hash(provider, model, prompt, params); cache dir `eval/cache/` (gitignored) with a committed small cache for the CI smoke set. Re-running with cache gives bit-identical results; `--no-cache` re-measures variance.
- Each result file records: git SHA, config hash, prompt hash, dataset version, parser version, embedding model revision, cost.
- Acceptance: `make eval` with cache reproduces exactly; without cache, within the measured variance.

## Failure analysis (the valuable part)
For every config: sample 30 failures, tag causes (parse error, chunk split evidence, wrong language retrieval, outdated clause, hallucinated amount, refusal error, injection). Publish taxonomy and counts.

## Outputs
`eval/results/<run_id>/{config.yaml, items.jsonl, summary.csv, failures.md}`; top-level `eval/RESULTS.md` table copied into README.

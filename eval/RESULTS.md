# Results (first measurements, 2026-11-01)

Reproduce: `make results GOLD=data/gold/dev.jsonl` (regenerates the tables and paired comparisons below).

**Read the limits first.** These are early, small-n numbers on an unreleased pilot set. They show the harness works and rule out nothing beyond what the intervals say.

## Pilot gold set (`data/gold/dev.jsonl`, not yet released)
75 items: 45 English (41 answerable + 4 unanswerable) and 30 Hindi, 0 Kannada (out of v1). Questions were LLM-drafted from sampled passages, then validated by one human reviewer (75 agreed or revised, 3 rejected over six batches; the reviewer edited three batch-5 questions so that they no longer name their scheme). Batch 6 carried reviewer flags that several answers are time-sensitive or simplified (ECI composition, 2023 appointment law, historical RSBY figures, old-vs-new tax regime); the items were accepted as "what this source says", not as current law. Single reviewer, so no agreement statistic. Evidence is one span per item (none for unanswerable). The index holds the whole local corpus (2,422 chunks from 340 English + 55 Hindi documents plus 22 unused Kannada ones), so every query faces distractors from all documents. Same-language retrieval. Reproduce: `make results GOLD=data/gold/dev.jsonl`.

## Retrieval (fixed 512-token-budget chunks, 64 overlap); the 71 answerable items
| retriever | n | recall@1 | recall@5 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| BM25 (word) | 71 | 0.690 | 0.930 | 0.795 | 0.837 |
| BM25 (char 3-5-gram) | 71 | 0.732 | 0.930 | 0.820 | 0.851 |
| dense (multilingual-e5-small) | 71 | 0.620 | 0.958 | 0.759 | 0.808 |
| hybrid (BM25 + e5-small, RRF k=60) | 71 | 0.704 | 0.972 | 0.817 | 0.853 |
| dense (bge-m3) | 71 | 0.676 | 0.958 | 0.787 | 0.823 |
| hybrid (BM25 + bge-m3, RRF k=60) | 71 | 0.704 | 0.958 | 0.814 | 0.844 |

By language, recall@1 (en n=41 / hi n=30): BM25 0.537 / 0.900; char-BM25 0.585 / 0.933; dense e5 0.488 / 0.800; hybrid e5 0.585 / 0.867; dense bge-m3 0.561 / 0.833; hybrid bge-m3 0.561 / 0.900.

Earlier note (set grew 41 -> 64): recall@1 fell because the batch-5 procedural myScheme questions are hard against hundreds of template-sharing pages, and three have no scheme name in the query. Adding batch 6 (11 items, mostly national-scheme and Wikipedia facts) moved BM25 recall@1 back up to 0.690. Absolute numbers depend on the question mix, not only on the retrievers.

## Paired comparisons (95% paired-bootstrap CI on the per-item difference)
`make results` prints all 15 pairs per metric for recall@1 and MRR (30 comparisons). Two intervals exclude 0, both the same pair: e5-small hybrid vs e5-small dense, recall@1 +0.085 [+0.014, +0.155] and MRR +0.058 [+0.019, +0.101]. Other recall@1 differences: bge-m3 hybrid - bge-m3 dense +0.028 [-0.056, +0.113]; bge-m3 dense - e5 dense +0.056 [-0.070, +0.183]; char-BM25 - BM25 +0.042 [0.000, +0.099]; e5 hybrid - BM25 +0.014 [-0.070, +0.099].

**Interpretation, conservatively.** The e5 hybrid-over-dense gap is now nominally significant, but it is one pair of 15 (two correlated metrics), nothing was pre-registered, about 1.5 of 30 intervals would exclude 0 by chance, and the same gap does not appear with bge-m3. Nothing separates BM25, character BM25 or hybrid, or bge-m3 from e5-small. All six place the gold passage in the top 5 for 93-97% of items, so differences concern only the top rank.

## End-to-end generation (claude-haiku-5-5, BM25 top-5) — deterministic scoring, no judge
Command: `python -m src.evalrunner.run_generation` (needs `ANTHROPIC_API_KEY`). **Number recall** = share of the gold answer's numbers (Indic digits normalised) present in the model's answer: an objective but weak correctness proxy, so only the 45 answerable items whose gold answer has numbers (25 en, 20 hi) are scored for correctness. No faithfulness or fluency judgement: the only judge available is the same model family as the generator, which `docs/05` forbids.

| mode | number recall (n=45) | en (n=25) | hi (n=20) | refusals on answerable (71) | cited chunk hits gold span | abstention on unanswerable (n=4) |
|---|---|---|---|---|---|---|
| RAG (retrieve + validated citations) | 0.941 | 0.927 | 0.958 | 1 (`b4-hi-004`) | 0.873 (62 of 71) | 4/4 |
| closed-book (same model, no passages) | 0.598 | 0.373 | 0.879 | n/a | n/a | n/a (no refusal mechanism) |
| oracle: whole gold document in context (upper bound, not deployable) | 0.952 | 0.947 | 0.958 | 0 | n/a | n/a (unanswerable items have no document) |

Paired difference (RAG - closed-book, 45 items): +0.343, 95% bootstrap CI [+0.217, +0.476]. RAG misses (number recall < 1): `b3-en-009`, `b3-en-010`, `b4-hi-011`, `b4-hi-023`, `b5-en-017` (the reviewer-edited question names no scheme, so retrieval cannot know which is meant). Tokens: RAG 324k in, closed-book 13k in. A repeat run on the same 75 items gave RAG 0.959 overall versus 0.941 here, so run-to-run model variation is about 0.02 and should be treated as noise floor.

**Oracle row.** The model is handed the whole parsed gold document (up to 150k characters), so retrieval cannot fail. It scores 0.952 against 0.941 for RAG: on these items BM25 top-5 loses almost nothing in number recall versus a perfect retriever, and the remaining misses (`b3-en-010`, `b4-hi-011`, `b4-hi-023`, `b5-en-026`) are not retrieval failures. This is NOT the long-context baseline of docs/05: the whole corpus is about 1M tokens and was not run in context. Number recall also cannot see wrong-but-numerically-matching answers.

**Read this carefully.** (1) The retrieval benefit is real but smaller than first measured (earlier +0.66 on 29 items, +0.38 on 37), because the larger set includes questions the model can partly guess. (2) **Closed-book Hindi recall is 0.88, far above English 0.37**: many Hindi items concern well-known national schemes (MGNREGA 100 days, Ayushman 5 lakh, PMJJBY 18-50) that the model knows, so the Hindi slice tests retrieval less than the English myScheme slice does; Hindi RAG-vs-closed gaps are not comparable with English ones. (3) Abstention 4/4 is on n=4 author-chosen questions about named but obscure schemes (95% Wilson lower bound about 0.51); it says the pipeline can refuse, not how reliably it does. (4) Same-family generation, one reviewer, number recall only.

## Why not to over-read any of this
- One reviewer, drafted-then-validated questions (shared vocabulary with their passages favours lexical retrieval), one chunking, small models, n=71 answerable / 75 total.
- The Hindi corpus is mostly Wikipedia; English is mostly myScheme state-scheme pages, so the two languages are different kinds of test, not a clean cross-language comparison.
- Not yet run: long-context baseline, other chunk sizes, human-paraphrased questions, a judge from another model family, answer faithfulness.

## Other measurements
- Prompt-injection, claude-haiku-5-5, 24 author-written cases, plain RAG and agent paths, two runs: canary-in-answer upper bound 0-1/24 (RAG) and 1-2/24 (agent); every flagged answer I could read reported and ignored the injection rather than obeying it (see `docs/11-security-and-ops.md` for the metric caveat and limits).
- Agent vs plain RAG on 30 held-out eligibility tasks, claude-haiku-5-5, same conditions: plain RAG 29/30, agent 26/30 (all four agent failures were the token budget, none a wrong decision); no accuracy advantage for the agent on these easy single-document tasks, at about 4x the tokens (see `docs/16-agent-plan.md`). An earlier agent-only run scored 29/30 before a provider fix; the difference is explained there. On 11 harder valid tasks (arithmetic, two criteria, rural/urban thresholds, age relaxation): plain RAG 10/11, agent 9/11 at about 2.5x the tokens, so no agent advantage was demonstrated (one task was excluded because its source page contradicts itself).

## End-to-end generation (claude-haiku-5-5, BM25 top-5, 41 validated items) — deterministic scoring, no judge
Command: `python -m src.evalrunner.run_generation --gold data/gold/dev.jsonl` (needs `ANTHROPIC_API_KEY`). Score = **number recall**: the share of the gold answer's numbers (Indic digits normalised) that appear in the model's answer. It is an objective but weak correctness proxy, so it covers only the 29 items whose gold answer contains numbers (17 en, 12 hi); the other 12 are not scored for correctness. No faithfulness or fluency judgement is made: the only judge available would be the same model family as the generator, which `docs/05` forbids.

| mode | n scored | number recall | refusals on answerable items | cited chunk hits the gold span |
|---|---|---|---|---|
| RAG (retrieve, answer with validated citations) | 29 | 0.966 | 0 of 41 | 0.951 (39 of 41) |
| closed-book (same model, no passages) | 29 | 0.310 | n/a | n/a |

Paired difference (RAG - closed-book) on the 29 items: +0.655, 95% bootstrap CI [+0.48, +0.82]. By language: English 0.961 vs 0.353 (n=17); Hindi 0.972 vs 0.250 (n=12). RAG misses were three items with 2 of 3 numbers (`b2-en-016`, `b3-en-010`, `b4-hi-023`); two items cited a chunk that did not hit the gold span (`b3-en-007`, `b3-en-015`). Token use: RAG 158k in / 8k out; closed-book 4k in / 11k out.

What this supports: on these items the model cannot answer from its own knowledge (closed-book recall 0.31), so the questions genuinely need the documents, and given the right passages the pipeline answers the numeric facts correctly. What it does not support: any claim about answer quality beyond numbers, about unanswerable questions (none reviewed yet, so abstention is unmeasured), about the long-context baseline (not run), or about other models. Closed-book is low partly because most questions concern obscure state-level schemes, which also says the set is a retrieval test more than a reasoning test. Same-family generation and one reviewer; n=29 numeric items; not a benchmark result.

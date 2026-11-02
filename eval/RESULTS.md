# Results (first measurements, 2026-11-01)

Reproduce: `make results GOLD=data/gold/dev.jsonl` (regenerates the tables and paired comparisons below).

**Read the limits first.** These are early, small-n numbers on an unreleased pilot set. They show the harness works and rule out nothing beyond what the intervals say.

## Pilot gold set (`data/gold/dev.jsonl`, not yet released)
100 items: 57 English (53 answerable + 4 unanswerable) and 43 Hindi, 0 Kannada (out of v1). Questions were LLM-drafted from sampled passages, then validated by one human reviewer (100 agreed or revised, 4 rejected over ten batches; batches 7-10 were reviewed by a model persona-reviewer whose decisions the author adopted; the reviewer edited three batch-5 questions so that they no longer name their scheme). Batch 6 carried reviewer flags that several answers are time-sensitive or simplified (ECI composition, 2023 appointment law, historical RSBY figures, old-vs-new tax regime); the items were accepted as "what this source says", not as current law. Single reviewer, so no agreement statistic. Evidence is one span per item (none for unanswerable). The index holds the whole local corpus (chunks from 340 English + 83 Hindi documents plus 22 unused Kannada ones), so every query faces distractors from all documents. Same-language retrieval. Reproduce: `make results GOLD=data/gold/dev.jsonl`.

## Retrieval (fixed 512-token-budget chunks, 64 overlap); the 96 answerable items
| retriever | n | recall@1 | recall@5 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| BM25 (word) | 96 | 0.729 | 0.948 | 0.825 | 0.863 |
| BM25 (char 3-5-gram) | 96 | 0.781 | 0.948 | 0.857 | 0.882 |
| dense (multilingual-e5-small) | 96 | 0.625 | 0.958 | 0.765 | 0.814 |
| hybrid (BM25 + e5-small, RRF k=60) | 96 | 0.729 | 0.969 | 0.835 | 0.870 |
| dense (bge-m3) | 96 | 0.688 | 0.948 | 0.794 | 0.828 |
| hybrid (BM25 + bge-m3, RRF k=60) | 96 | 0.740 | 0.958 | 0.834 | 0.860 |

By language, recall@1 (en n=53 / hi n=43): BM25 0.623 / 0.860; char-BM25 0.642 / 0.953; dense e5 0.509 / 0.767; hybrid e5 0.642 / 0.837; dense bge-m3 0.585 / 0.814; hybrid bge-m3 0.623 / 0.884.

Question mix matters: earlier sets of 41, 64, 71 and 84 items gave BM25 recall@1 of 0.756, 0.650, 0.690 and 0.702 (now 0.729), because batch 5 added hard procedural myScheme questions and later batches added easier fact lookups.

## Paired comparisons (95% paired-bootstrap CI on the per-item difference)
`make results` prints all 15 pairs per metric for recall@1 and MRR (30 comparisons). Seven intervals exclude 0: char-BM25 over e5 dense (recall@1 +0.156 [+0.052, +0.260]; MRR +0.092 [+0.026, +0.156]); e5 hybrid over e5 dense (recall@1 +0.104 [+0.031, +0.177]; MRR +0.070 [+0.030, +0.112]); bge-m3 hybrid over e5 dense (recall@1 +0.115 [+0.021, +0.208]; MRR +0.070 [+0.010, +0.130]); and char-BM25 over word BM25 on MRR only (+0.032 [+0.001, +0.066], at the boundary). Not separated: word vs char-BM25 on recall@1 (-0.052 [-0.115, +0.010]); BM25 vs e5 hybrid (0.000 [-0.083, +0.083]); bge-m3 dense vs e5 dense (+0.062 [-0.042, +0.167]).

**Interpretation, conservatively.** e5-small dense is the one consistent laggard: char-BM25 and both hybrids beat it with intervals excluding 0; word BM25 is ahead but not clearly. Beyond that nothing separates the top systems, and the char-BM25 vs word-BM25 gap appeared at n=84 and weakened to the boundary on MRR and is not significant on recall@1 at n=96, which is what chance-level differences do as items are added. Caveats: comparisons were not pre-registered, about 1.5 of 30 intervals would exclude 0 by chance (seven is more, but they are correlated), one reviewer wrote the labels, and drafted questions share vocabulary with their passages, which favours lexical matching. This is not evidence that BM25 beats dense retrieval in general. All six systems put the gold passage in the top 5 for 95-97% of items.

## End-to-end generation (claude-haiku-5-5, BM25 top-5) — deterministic scoring, no judge
Command: `python -m src.evalrunner.run_generation` (needs `ANTHROPIC_API_KEY`). **Number recall** = share of the gold answer's numbers (Indic digits normalised) present in the model's answer: an objective but weak correctness proxy, so only the 60 answerable items whose gold answer has numbers (31 en, 29 hi) are scored for correctness. No faithfulness or fluency judgement: the only judge available is the same model family as the generator, which `docs/05` forbids.

| mode | number recall (n=60) | en (n=31) | hi (n=29) | refusals on answerable (96) | cited chunk hits gold span | abstention on unanswerable (n=4) |
|---|---|---|---|---|---|---|
| RAG (retrieve + validated citations) | 0.922 | 0.898 | 0.948 | 0 | 0.917 (88 of 96) | 4/4 |
| closed-book (same model, no passages) | 0.632 | 0.435 | 0.842 | n/a | n/a | n/a (no refusal mechanism) |
| oracle: whole gold document in context (upper bound, not deployable) | 0.931 | 0.925 | 0.937 | 1 (`b3-en-016`) | n/a | n/a (unanswerable items have no document) |

Paired difference (RAG - closed-book, 60 items): +0.290, 95% bootstrap CI [+0.18, +0.41]. RAG misses (number recall < 1): `b3-en-009`, `b3-en-010`, `b5-en-017` (reviewer-edited question names no scheme), `b7-en-009`, `b8-hi-014`, `b9-hi-002`. Oracle misses: `b3-en-010`, `b4-hi-011`, `b4-hi-023`, `b5-en-026`, `b7-en-009`, `b8-hi-014`. Tokens in: RAG 425k, closed-book 17k, oracle 415k. Repeat runs on the same items have differed by about 0.02 overall, so treat differences of that size as noise.

**Oracle row.** The model is handed the whole parsed gold document (up to 150k characters), so retrieval cannot fail. It scores about what RAG scores (0.931 vs 0.922): on these items BM25 top-5 loses nothing measurable in number recall versus a perfect retriever, and the oracle's own misses are not retrieval failures. This is NOT the long-context baseline of docs/05: the whole corpus is about 1M tokens and was not run in context. Number recall also cannot see wrong-but-numerically-matching answers.

**Read this carefully.** (1) The retrieval benefit is real but smaller than first measured (earlier +0.66 on 29 items, +0.38 on 37), because the larger set includes questions the model can partly guess. (2) **Closed-book Hindi recall is 0.84, far above English 0.44**: many Hindi items concern well-known national schemes (MGNREGA 100 days, Ayushman 5 lakh, PMJJBY 18-50) that the model knows, so the Hindi slice tests retrieval less than the English myScheme slice does; Hindi RAG-vs-closed gaps are not comparable with English ones. (3) Abstention 4/4 is on n=4 author-chosen questions about named but obscure schemes (95% Wilson lower bound about 0.51); it says the pipeline can refuse, not how reliably it does. (4) Same-family generation, one reviewer, number recall only.

## Why not to over-read any of this
- One reviewer, drafted-then-validated questions (shared vocabulary with their passages favours lexical retrieval), one chunking, small models, n=96 answerable / 100 total.
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

# Results (first measurements, 2026-11-01)

Reproduce: `make results GOLD=data/gold/dev.jsonl` (regenerates the tables and paired comparisons below).

**Read the limits first.** These are early, small-n numbers on an unreleased pilot set. They show the harness works and rule out nothing beyond what the intervals say.

## Pilot gold set (`data/gold/dev.jsonl`, not yet released)
88 items: 51 English (47 answerable + 4 unanswerable) and 37 Hindi, 0 Kannada (out of v1). Questions were LLM-drafted from sampled passages, then validated by one human reviewer (88 agreed or revised, 3 rejected over eight batches; batches 7 and 8 were reviewed by a model persona-reviewer whose decisions the author adopted; the reviewer edited three batch-5 questions so that they no longer name their scheme). Batch 6 carried reviewer flags that several answers are time-sensitive or simplified (ECI composition, 2023 appointment law, historical RSBY figures, old-vs-new tax regime); the items were accepted as "what this source says", not as current law. Single reviewer, so no agreement statistic. Evidence is one span per item (none for unanswerable). The index holds the whole local corpus (2,818 chunks from 340 English + 77 Hindi documents plus 22 unused Kannada ones), so every query faces distractors from all documents. Same-language retrieval. Reproduce: `make results GOLD=data/gold/dev.jsonl`.

## Retrieval (fixed 512-token-budget chunks, 64 overlap); the 84 answerable items
| retriever | n | recall@1 | recall@5 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| BM25 (word) | 84 | 0.702 | 0.941 | 0.804 | 0.846 |
| BM25 (char 3-5-gram) | 84 | 0.774 | 0.941 | 0.848 | 0.874 |
| dense (multilingual-e5-small) | 84 | 0.619 | 0.952 | 0.757 | 0.806 |
| hybrid (BM25 + e5-small, RRF k=60) | 84 | 0.702 | 0.964 | 0.818 | 0.856 |
| dense (bge-m3) | 84 | 0.679 | 0.941 | 0.784 | 0.819 |
| hybrid (BM25 + bge-m3, RRF k=60) | 84 | 0.714 | 0.952 | 0.817 | 0.845 |

By language, recall@1 (en n=47 / hi n=37): BM25 0.596 / 0.838; char-BM25 0.638 / 0.946; dense e5 0.511 / 0.757; hybrid e5 0.617 / 0.811; dense bge-m3 0.574 / 0.811; hybrid bge-m3 0.596 / 0.865.

Question mix matters: earlier sets of 41, 64 and 71 items gave different absolute numbers (BM25 recall@1 0.756, 0.650, 0.690, now 0.702), because batch 5 added hard procedural myScheme questions and later batches added easier fact lookups. The 22 newly ingested Hindi articles also enlarged the Hindi distractor pool.

## Paired comparisons (95% paired-bootstrap CI on the per-item difference)
`make results` prints all 15 pairs per metric for recall@1 and MRR (30 comparisons). Six intervals exclude 0, from three pairs, each on both metrics: char-BM25 over word BM25 (recall@1 +0.071 [+0.024, +0.131]; MRR +0.044 [+0.015, +0.078]); char-BM25 over e5 dense (recall@1 +0.155 [+0.048, +0.274]; MRR +0.091 [+0.021, +0.164]); e5 hybrid over e5 dense (recall@1 +0.083 [+0.012, +0.167]; MRR +0.061 [+0.020, +0.104]). Not separated: BM25 vs e5 hybrid (0.000 [-0.095, +0.095]), bge-m3 hybrid vs bge-m3 dense (+0.036 [-0.036, +0.107]), bge-m3 vs e5 dense (+0.059 [-0.048, +0.167]).

**Interpretation, conservatively.** Character-level BM25 is the most consistent leader, and e5-small dense the most consistent laggard, but: these are the same data the earlier comparisons used and the set grew by adding items, the comparisons were not pre-registered, 30 intervals would put about 1.5 outside by chance (six is more than that, yet the three pairs are correlated), one reviewer wrote the labels, and drafted questions share vocabulary with their passages, which favours lexical matching. So: lexical retrieval is at least as good as the dense models here; this is not evidence that BM25 beats dense retrieval in general. The e5 gap closes with bge-m3, and all six systems still put the gold passage in the top 5 for 94-96% of items.

## End-to-end generation (claude-haiku-5-5, BM25 top-5) — deterministic scoring, no judge
Command: `python -m src.evalrunner.run_generation` (needs `ANTHROPIC_API_KEY`). **Number recall** = share of the gold answer's numbers (Indic digits normalised) present in the model's answer: an objective but weak correctness proxy, so only the 54 answerable items whose gold answer has numbers (28 en, 26 hi) are scored for correctness. No faithfulness or fluency judgement: the only judge available is the same model family as the generator, which `docs/05` forbids.

| mode | number recall (n=54) | en (n=28) | hi (n=26) | refusals on answerable (84) | cited chunk hits gold span | abstention on unanswerable (n=4) |
|---|---|---|---|---|---|---|
| RAG (retrieve + validated citations) | 0.938 | 0.899 | 0.981 | 0 | 0.917 (77 of 84) | 4/4 |
| closed-book (same model, no passages) | 0.614 | 0.369 | 0.878 | n/a | n/a | n/a (no refusal mechanism) |
| oracle: whole gold document in context (upper bound, not deployable) | 0.923 | 0.917 | 0.929 | 1 | n/a | n/a (unanswerable items have no document) |

Paired difference (RAG - closed-book, 54 items): +0.324, 95% bootstrap CI [+0.204, +0.448]. RAG misses (number recall < 1): `b3-en-009`, `b3-en-010`, `b5-en-017` (reviewer-edited question names no scheme), `b7-en-009`, `b8-hi-007` (the last two have gold answers with several numbers, and the model omitted some). Oracle misses: `b3-en-010`, `b4-hi-011`, `b4-hi-023`, `b5-en-026`, `b7-en-009`, `b8-hi-014`. Tokens in: RAG 363k, closed-book 15k, oracle 338k. Earlier repeat runs differed by about 0.02 overall, so treat differences of that size as noise.

**Oracle row.** The model is handed the whole parsed gold document (up to 150k characters), so retrieval cannot fail. It scores 0.923 against 0.938 for RAG, i.e. no better: on these items BM25 top-5 loses nothing measurable in number recall versus a perfect retriever, and the oracle's own misses are not retrieval failures. This is NOT the long-context baseline of docs/05: the whole corpus is about 1M tokens and was not run in context. Number recall also cannot see wrong-but-numerically-matching answers.

**Read this carefully.** (1) The retrieval benefit is real but smaller than first measured (earlier +0.66 on 29 items, +0.38 on 37), because the larger set includes questions the model can partly guess. (2) **Closed-book Hindi recall is 0.88, far above English 0.37**: many Hindi items concern well-known national schemes (MGNREGA 100 days, Ayushman 5 lakh, PMJJBY 18-50) that the model knows, so the Hindi slice tests retrieval less than the English myScheme slice does; Hindi RAG-vs-closed gaps are not comparable with English ones. (3) Abstention 4/4 is on n=4 author-chosen questions about named but obscure schemes (95% Wilson lower bound about 0.51); it says the pipeline can refuse, not how reliably it does. (4) Same-family generation, one reviewer, number recall only.

## Why not to over-read any of this
- One reviewer, drafted-then-validated questions (shared vocabulary with their passages favours lexical retrieval), one chunking, small models, n=84 answerable / 88 total.
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

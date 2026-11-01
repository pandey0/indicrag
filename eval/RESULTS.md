# Results (first measurements, 2026-11-01)

Reproduce: `make results GOLD=data/gold/dev.jsonl` (regenerates the tables and paired comparisons below).

**Read the limits first.** These are early, small-n numbers on an unreleased pilot set. They show the harness works and rule out nothing beyond what the intervals say.

## Pilot gold set (`data/gold/dev.jsonl`, not yet released)
64 items: 42 English (38 answerable + 4 unanswerable) and 22 Hindi, 0 Kannada (out of v1). Questions were LLM-drafted from sampled passages, then validated by one human reviewer (60 agreed, 4 revised, 1 rejected; the reviewer edited three batch-5 questions so that they no longer name their scheme). Single reviewer, so no agreement statistic. Evidence is one span per item (two for none). The index holds the whole local corpus (2,422 chunks from 340 English + 55 Hindi documents plus 22 unused Kannada ones), so every query faces distractors from all documents. Same-language retrieval. Reproduce: `make results GOLD=data/gold/dev.jsonl`.

## Retrieval (fixed 512-token-budget chunks, 64 overlap); the 60 answerable items
| retriever | n | recall@1 | recall@5 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| BM25 (word) | 60 | 0.650 | 0.917 | 0.770 | 0.822 |
| BM25 (char 3-5-gram) | 60 | 0.700 | 0.917 | 0.799 | 0.835 |
| dense (multilingual-e5-small) | 60 | 0.600 | 0.950 | 0.744 | 0.797 |
| hybrid (BM25 + e5-small, RRF k=60) | 60 | 0.667 | 0.967 | 0.796 | 0.840 |
| dense (bge-m3) | 60 | 0.633 | 0.950 | 0.761 | 0.802 |
| hybrid (BM25 + bge-m3, RRF k=60) | 60 | 0.667 | 0.950 | 0.792 | 0.829 |

By language, recall@1 (en n=38 / hi n=22): BM25 0.526 / 0.864; char-BM25 0.579 / 0.909; dense e5 0.474 / 0.818; hybrid e5 0.579 / 0.818; dense bge-m3 0.553 / 0.773; hybrid bge-m3 0.553 / 0.864.

**What moved when the set grew from 41 to 64 items:** recall@1 fell for every system (BM25 0.756 -> 0.650). The cause is the 19 answerable batch-5 items: BM25 recall@1 is 0.29 on the 14 English ones versus 0.76 on the earlier 41 items. They are mostly procedural questions ("where do I submit the form", "which documents", "how is an application processed") against hundreds of myScheme pages built from the same step templates, and three of them (edited by the reviewer) no longer name a scheme, which makes them unresolvable from the query alone. So the pool is harder, not the retrievers worse; absolute numbers depend on the question mix.

## Paired comparisons (95% paired-bootstrap CI on the per-item difference)
`make results` prints all 15 pairs per metric for recall@1 and MRR (30 comparisons). **On recall@1 no pair excludes 0.** On MRR exactly one does: e5-small hybrid vs e5-small dense (hybrid +0.052, CI [+0.010, +0.098]); its recall@1 interval is [0.000, +0.150]. Selected recall@1 differences: e5 hybrid - e5 dense +0.067 [0.000, +0.150]; bge-m3 hybrid - bge-m3 dense +0.033 [-0.067, +0.133]; bge-m3 dense - e5 dense +0.033 [-0.117, +0.183]; char-BM25 - BM25 +0.050 [0.000, +0.117]; e5 hybrid - BM25 +0.017 [-0.083, +0.133].

**Interpretation, conservatively.** One MRR interval out of 30 comparisons excluding 0 is about what chance gives (5% of 30 is roughly 1.5), there was no pre-registered primary comparison, and the same gap does not appear with bge-m3. Nothing here separates BM25, character BM25, dense or hybrid, or bge-m3 from e5-small. All six place the gold passage in the top 5 for 92-97% of items, so differences concern only the top rank.

## End-to-end generation (claude-haiku-5-5, BM25 top-5) — deterministic scoring, no judge
Command: `python -m src.evalrunner.run_generation` (needs `ANTHROPIC_API_KEY`). **Number recall** = share of the gold answer's numbers (Indic digits normalised) present in the model's answer: an objective but weak correctness proxy, so only the 37 answerable items whose gold answer has numbers (22 en, 15 hi) are scored for correctness. No faithfulness or fluency judgement: the only judge available is the same model family as the generator, which `docs/05` forbids.

| mode | number recall (n=37) | en (n=22) | hi (n=15) | refusals on answerable (60) | cited chunk hits gold span | abstention on unanswerable (n=4) |
|---|---|---|---|---|---|---|
| RAG (retrieve + validated citations) | 0.928 | 0.902 | 0.967 | 0 | 0.883 (53 of 60) | 4/4 |
| closed-book (same model, no passages) | 0.545 | 0.379 | 0.789 | n/a | n/a | n/a (no refusal mechanism) |

Paired difference (RAG - closed-book, 37 items): +0.383, 95% bootstrap CI [+0.234, +0.541]. RAG misses: `b2-en-016`, `b3-en-009`, `b3-en-010`, `b4-hi-011` (partial numbers) and `b5-en-017` (the reviewer-edited question "What is the maximum assistance per student?" names no scheme, so retrieval cannot know which scheme is meant). 7 answers cited a chunk that did not hit the gold span. Tokens: RAG 287k, closed-book 54k.

**Read this carefully.** (1) The retrieval benefit is real but smaller than first measured (earlier +0.66 on 29 items), because the larger set includes questions the model can partly guess. (2) **Closed-book Hindi recall is 0.79, far above English 0.38**: many Hindi items concern well-known national schemes (MGNREGA 100 days, Ayushman 5 lakh, PMJJBY 18-50) that the model knows, so the Hindi slice tests retrieval less than the English myScheme slice does; Hindi RAG-vs-closed gaps are not comparable with English ones. (3) Abstention 4/4 is on n=4 author-chosen questions about named but obscure schemes (95% Wilson lower bound about 0.51); it says the pipeline can refuse, not how reliably it does. (4) Same-family generation, one reviewer, number recall only.

## Why not to over-read any of this
- One reviewer, drafted-then-validated questions (shared vocabulary with their passages favours lexical retrieval), one chunking, small models, n=60/64.
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

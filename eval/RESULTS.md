# Results (first measurements, 2026-11-01)

Reproduce: `make results GOLD=data/gold/dev.jsonl` (regenerates the tables and paired comparisons below).

**Read the limits first.** These are early, small-n numbers on an unreleased pilot set. They show the harness works and rule out nothing beyond what the intervals say.

## Pilot gold set (`data/gold/dev.jsonl`, not yet released)
41 items: 24 English, 17 Hindi, 0 Kannada. Questions were LLM-drafted from sampled passages, then validated by one human reviewer (agreed 40, revised 1, rejected 1 of 42 reviewed; Kannada excluded). Single reviewer, so there is no agreement statistic. Evidence is one span per item. The index holds the whole local corpus (2,141 chunks, 321 English / 42 Hindi / 22 Kannada documents), so every query faces distractors from all documents. Same-language retrieval (query language filters the candidate chunks).

## Retrieval (fixed 512-token-budget chunks, 64 overlap)
| retriever | n | recall@1 | recall@5 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| BM25 (word) | 41 | 0.756 | 0.976 | 0.851 | 0.887 |
| BM25 (char 3-5-gram) | 41 | 0.756 | 0.951 | 0.850 | 0.873 |
| dense (multilingual-e5-small) | 41 | 0.658 | 1.000 | 0.807 | 0.854 |
| hybrid (BM25 + e5-small, RRF k=60) | 41 | 0.780 | 1.000 | 0.878 | 0.903 |
| dense (bge-m3) | 41 | 0.683 | 0.976 | 0.804 | 0.840 |
| hybrid (BM25 + bge-m3, RRF k=60) | 41 | 0.732 | 0.976 | 0.846 | 0.870 |

By language, recall@1 (en n=24 / hi n=17): BM25 0.667 / 0.882; char-BM25 0.625 / 0.941; dense e5 0.583 / 0.765; hybrid e5 0.750 / 0.824; dense bge-m3 0.625 / 0.765; hybrid bge-m3 0.625 / 0.882.

## Paired comparisons (95% paired-bootstrap CI on the per-item difference, recall@1 and MRR)
`make results` prints all 15 pairs per metric (6 systems), 30 comparisons for the two metrics. **Exactly one interval excludes 0: e5-small hybrid vs e5-small dense** (recall@1 +0.122, CI [+0.024, +0.220]; MRR +0.071, CI [+0.022, +0.130]). Everything else includes 0, including:
| comparison | recall@1 diff | 95% CI |
|---|---|---|
| bge-m3 dense vs e5-small dense | +0.024 | [-0.171, +0.220] |
| bge-m3 hybrid vs bge-m3 dense | +0.049 | [-0.073, +0.195] |
| BM25 vs e5-small hybrid | -0.024 | [-0.171, +0.122] |
| char-BM25 vs BM25 | 0.000 | [-0.073, +0.073] |

**Interpretation, conservatively.** With 30 comparisons computed and no multiplicity correction or pre-registered primary comparison, one interval excluding 0 is about what chance alone is expected to give (5% of 30 is about 1.5; the two metrics and overlapping systems are correlated, so this is only a rough guide), and the hybrid-over-dense gap did not appear with bge-m3 (hybrid - dense there is +0.049, CI includes 0). Treat "hybrid beats dense" as an unconfirmed hint, not a finding. These data do NOT distinguish bge-m3 from e5-small, BM25 from dense, or word from character BM25. They do show every method retrieves the gold passage in the top 5 for roughly 95-100% of items, so differences are confined to the top rank.

## Why not to over-read
- n = 41, one reviewer, one chunking, one embedding model (a small one); recall@5 is near ceiling so only recall@1/MRR discriminate.
- LLM-drafted questions share vocabulary with their gold passage; this favours lexical methods, so dense retrieval is probably under-rated here. Human-written paraphrased questions are needed before any lexical-vs-dense claim.
- Five drafts name no scheme in the question text; they are kept as agreed by the reviewer.
- The Hindi corpus is mostly Wikipedia; results do not say how official-document Hindi behaves.
- Not yet run: answer-quality evaluation, closed-book and long-context baselines, larger or paraphrased question sets, other chunk sizes.

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

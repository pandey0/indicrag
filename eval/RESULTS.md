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
`make results` prints all 28 pairs per metric (6 systems). **Exactly one interval excludes 0: e5-small hybrid vs e5-small dense** (recall@1 +0.122, CI [+0.024, +0.220]; MRR +0.071, CI [+0.022, +0.130]). Everything else includes 0, including:
| comparison | recall@1 diff | 95% CI |
|---|---|---|
| bge-m3 dense vs e5-small dense | +0.024 | [-0.171, +0.220] |
| bge-m3 hybrid vs bge-m3 dense | +0.049 | [-0.073, +0.195] |
| BM25 vs e5-small hybrid | -0.024 | [-0.171, +0.122] |
| char-BM25 vs BM25 | 0.000 | [-0.073, +0.073] |

**Interpretation, conservatively.** With 56 comparisons computed and no multiplicity correction or pre-registered primary comparison, one interval excluding 0 is about what chance alone is expected to give (about 5% of comparisons, so 2-3), and the hybrid-over-dense gap did not appear with bge-m3 (hybrid - dense there is +0.049, CI includes 0). Treat "hybrid beats dense" as an unconfirmed hint, not a finding. These data do NOT distinguish bge-m3 from e5-small, BM25 from dense, or word from character BM25. They do show every method retrieves the gold passage in the top 5 for roughly 95-100% of items, so differences are confined to the top rank.

## Why not to over-read
- n = 41, one reviewer, one chunking, one embedding model (a small one); recall@5 is near ceiling so only recall@1/MRR discriminate.
- LLM-drafted questions share vocabulary with their gold passage; this favours lexical methods, so dense retrieval is probably under-rated here. Human-written paraphrased questions are needed before any lexical-vs-dense claim.
- Five drafts name no scheme in the question text; they are kept as agreed by the reviewer.
- The Hindi corpus is mostly Wikipedia; results do not say how official-document Hindi behaves.
- Not yet run: answer-quality evaluation, closed-book and long-context baselines, larger or paraphrased question sets, other chunk sizes.

## Other measurements
- Prompt-injection attack success, claude-haiku-5-5: 0/12 (see `docs/11-security-and-ops.md`).
- Agent eligibility tasks, claude-haiku-5-5, 30 held-out tasks: 29/30 success (see `docs/16-agent-plan.md`, with heavy caveats).

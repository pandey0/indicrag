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
| dense (multilingual-e5-small) | 41 | 0.659 | 1.000 | 0.807 | 0.854 |
| hybrid (BM25 + e5-small, RRF k=60) | 41 | 0.780 | 1.000 | 0.878 | 0.904 |

By language, recall@1 (en n=24 / hi n=17): BM25 0.667 / 0.882; char-BM25 0.625 / 0.941; dense 0.583 / 0.765; hybrid 0.750 / 0.824.

## Paired comparisons (95% paired-bootstrap CI on the per-item difference)
| comparison | metric | diff (all) | 95% CI | interval excludes 0? |
|---|---|---|---|---|
| hybrid - dense | recall@1 | +0.122 | [+0.024, +0.220] | yes (also English alone: +0.167 [+0.042, +0.333]) |
| hybrid - dense | MRR | +0.071 | [+0.022, +0.130] | yes |
| hybrid - BM25 | recall@1 | +0.024 | [-0.122, +0.171] | no |
| BM25 - dense | recall@1 | +0.098 | [-0.073, +0.268] | no |
| char-BM25 - BM25 | recall@1 | 0.000 | [-0.073, +0.073] | no |

Supported by these data: with this embedding model and chunking, hybrid retrieval ranks the gold passage higher than dense-only retrieval. Not supported: any ranking among BM25, char-BM25 and hybrid, any claim about Hindi vs English (intervals are wide and several touch 0), anything about Kannada, or that these methods transfer to other models, chunk sizes or corpora.

## Why not to over-read
- n = 41, one reviewer, one chunking, one embedding model (a small one); recall@5 is near ceiling so only recall@1/MRR discriminate.
- LLM-drafted questions share vocabulary with their gold passage; this favours lexical methods, so dense retrieval is probably under-rated here. Human-written paraphrased questions are needed before any lexical-vs-dense claim.
- Five drafts name no scheme in the question text; they are kept as agreed by the reviewer.
- The Hindi corpus is mostly Wikipedia; results do not say how official-document Hindi behaves.
- Not yet run: bge-m3 comparison (embedding still computing), answer-quality evaluation, closed-book and long-context baselines.

## Other measurements
- Prompt-injection attack success, claude-haiku-5-5: 0/12 (see `docs/11-security-and-ops.md`).
- Agent eligibility tasks, claude-haiku-5-5, 30 held-out tasks: 29/30 success (see `docs/16-agent-plan.md`, with heavy caveats).

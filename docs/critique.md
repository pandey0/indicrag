# Self-critique: where this is weak

An adversarial read of the project as it stands, ordered by how much it should change what you believe.

## 1. The benchmark is small and reviewed by one person
100 questions, one author-reviewer, no agreement statistic, 25 items checked by a model reviewer whose decisions the author adopted. With n=96 answerable, paired intervals for recall@1 are about +/-0.10, so most comparisons between retrieval systems are not separated. **Fix first:** a second human reviewer on a 30-item sample and a kappa; more items.

## 2. The questions favour keyword search
They were drafted by an LLM from passages and share vocabulary with them. That inflates BM25 and char n-gram BM25 relative to dense retrieval. The results cannot say BM25 is better in general. **Fix:** add human-written and paraphrased questions; report them as a separate slice.

## 3. Generation is scored weakly
Number recall covers 60 of 96 items and cannot see a wrong answer containing the right numbers. No faithfulness, fluency or language-match score. **Fix:** a cross-family judge calibrated on human labels.

## 4. The Hindi slice measures less than it seems
Closed-book Hindi number recall is 0.84 vs English 0.44, because many Hindi items concern well-known national schemes. Hindi corpus is mostly Wikipedia; English is mostly myScheme. The languages are different tests.

## 5. Baselines are incomplete
No whole-corpus long-context run ([ADR 0005](adr/0005-oracle-long-document-baseline.md)). Same-family generator and tooling. One chunking strategy in the headline tables.

## 6. The agent did not help
On 30 easy tasks plain RAG scored 29/30 and the agent 26/30, all misses the token budget. The task gold criteria were never human-reviewed, and two gold errors were found by the model. Do not claim the agent adds value.

## 7. Data and licensing
Wikipedia quotes are CC BY-SA 4.0. myScheme excerpts in the gold set were published without asking the owners; the per-source licence review was not completed. The gold answers can be out of date because scheme rules change.

## 8. Operational gaps
No authentication, tenancy, metrics, tracing, load test, IaC or release automation. See [`SCORECARD.md`](../SCORECARD.md).

## Prioritised fixes
1. Second reviewer and agreement statistic.
2. Human-written question slice.
3. Cross-family judge with human calibration.
4. Whole-corpus long-context baseline.
5. Per-source licence review of the published excerpts.
6. Metrics, tracing and a load test if it is ever deployed.

# ADR 0005: Oracle whole-document mode instead of a whole-corpus long-context baseline
Status: accepted (2026-11-01), with a known gap.

**Context.** `docs/05` asks for a long-context baseline. The corpus is about 1M tokens; feeding it in context for every question is slow and costly.

**Decision.** Add `long_doc` mode: the whole parsed gold document (capped at 150k characters) goes in context. It is an upper bound for what retrieval could deliver, not the docs/05 baseline, and is labelled so.

**Consequences.** It shows retrieval is not the bottleneck on these items (0.93 vs RAG 0.92 number recall) without claiming to answer the "is RAG needed at all" question. The whole-corpus run is still open.

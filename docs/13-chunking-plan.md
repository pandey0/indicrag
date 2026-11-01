# 13 Chunking v1 plan (week 2)

## Goal
Turn parsed documents (`data/processed/<source_id>/<parsed_sha>.txt` + `.sections.json`) into addressable chunks that keep `doc_id, parsed_sha256, section_path, char_start, char_end, lang`, so gold evidence spans (docs/02) can be scored independent of the chunker.

## Standards followed
- Offsets always index the processed text; invariant `chunk.text == text[char_start:char_end]` is enforced in tests and at build time (same rule as gold `quote`).
- Chunk ids are deterministic (`sha1(doc_id | parsed_sha256 | strategy | start | end)`), so rebuilds are reproducible and diffable.
- Baseline from docs/05: fixed-size chunks, 512 "tokens", 64 overlap (~12%), common practice range 256-512 tokens with 10-20% overlap. One-factor-at-a-time ablations later (heading-aware, size).
- Retrieval hit rule: a chunk hits a gold span if it contains it or overlaps >= 50% of it (`src/chunk/spans.py`).

## Design
- Token counting is pluggable (`TokenCounter`). v1 default is a script-aware approximation (Latin ~4 chars/token, Devanagari ~2.5, Kannada ~2 chars/token; Indic scripts split into more tokens in typical multilingual tokenizers). It is replaced by the real embedding-model tokenizer when the embedding model is fixed; the size is therefore recorded as `budget` + `counter` name in each chunk record, not assumed comparable across counters.
- Strategies: `fixed` (greedy-pack sentence units to the budget, overlap in whole units, hard-split oversize units on whitespace) and `heading` (never crosses a section boundary; sections larger than the budget fall back to fixed inside the section).
- Sentence units split on `.?!।|` + newline (Devanagari danda included); offsets come from regex spans, never from re-joining.
- Quality gate: chunks that look like OCR garbage (low expected-script ratio, or mostly 1-2 character tokens) are excluded from the index but kept in the parsed text, so spans stay stable. Excluded chunk counts are reported per source.

## Out of scope this step
Embeddings, pgvector schema (next), reranking. No claim about retrieval quality until measured.

## Acceptance
Tests: invariant, determinism, overlap, section boundaries, junk gate, span-hit rule. `make chunk` builds `data/chunks/<strategy>.jsonl` (gitignored) and prints per-language chunk counts.

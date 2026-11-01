# 14 Retrieval v1 plan (week 2-3)

## Environment constraints (measured 2026-11-01)
Local disk is ~99% full (about 3 GB free), so large model downloads are deferred. A Postgres image with pgvector is already present locally (`ghcr.io/supabase/postgres`); no new pull needed.

## Order of work (cheapest evidence first)
1. **Lexical baseline (this step):** pure-Python BM25 over `data/chunks/*.jsonl`. No model, no disk. Gives the retriever interface, tokenisation policy and the first measurable retrieval path.
2. **Retriever interface** `Retriever.search(query, lang, k) -> list[Hit(chunk_id, score)]`, shared by BM25, dense and hybrid so the eval runner treats them identically.
3. **Dense + pgvector** once a multilingual embedding model is chosen and disk allows it; schema via Alembic migration (docs/02 data model). Hybrid via reciprocal rank fusion (k=60), tested on synthetic rankings.
4. **Scoring:** recall@k / MRR / nDCG@10 against gold spans using `src/chunk/spans.chunk_hits_span`. Needs gold items; until they exist, tests use synthetic gold only and no retrieval quality is claimed.

## Standards followed
- BM25 Okapi with k1=1.5, b=0.75 (common defaults), IDF `ln(1 + (N - n + 0.5)/(n + 0.5))` (non-negative).
- Tokenisation: NFC; lower-case; split on whitespace/punctuation but keep Indic combining marks and ZWJ/ZWNJ inside words (a plain `\w` shreds Indic words: bug found and fixed in chunk quality gate). No stemming in v1; character n-grams are a later one-factor ablation (docs/05) because Hindi/Kannada are inflected/agglutinative.
- Language filter is optional at query time: same-language search by default, cross-lingual runs search all languages.
- Deterministic ranking: ties broken by chunk_id.

## First smoke test (not an evaluation; no gold items exist yet)
BM25 runs on `fixed_512_64` chunks. Observed issues to address before any numbers are reported:
- Hindi query "सूचना के अधिकार के तहत आवेदन शुल्क" returned Bihar RTPS chunks, not RTI Act chunks: common function words (के, का, तहत) and noisy RTI OCR text dominate. Candidates: Hindi/Kannada stopword list, character n-gram ablation, OCR text cleaning.
- (FIXED, parser 0.2: full-viewport overlay modals are dropped; 0 of 268 current myScheme files contain the notice) myScheme chunks contained a site-wide redirect notice ("You're being redirected to an external website..."): the per-host boilerplate remover does not catch it on rendered pages (likely because it appears inside a modal with varied surrounding text). Fix in the parse stage and re-chunk.
- Two top hits for the Hindi query had identical scores: duplicated text in a source page; dedupe identical chunk text per document.

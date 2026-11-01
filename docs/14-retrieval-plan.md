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

## Status 2026-11-01 (end of this step)
- Analyzer option added (`word` | `char` 3-5-gram). A proxy check (`scripts/proxy_retrieval.py`: query = article title, gold = that article) is **saturated** (hit@5 = 1.0 for both analyzers, hit@1 0.92-1.0), so it cannot choose between them. Decision deferred to real gold items; do not tune on the proxy.
- Postgres schema `db/migrations/0001_init.sql` (documents, chunks with generated `simple` tsvector + GIN, per-model `chunk_embeddings` table) loads cleanly via `scripts/db_load.py` into a local pgvector container (`make db-up db-load`): 385 docs, 2068 chunks (en 1413 / hi 477 / kn 178). Full-text and `<=>` vector queries verified.
- Still open: embedding model choice (disk), dense + hybrid retriever, gold labelling.

## Dense retrieval plan (step 3), disk now ~13 GB free
- **Baseline model:** `intfloat/multilingual-e5-small` (118M params, 384-d, MIT): small enough for CPU on ~1.8k chunks. E5 needs prefixes: `query: ` / `passage: ` (a known source of silent quality loss if omitted; enforced in the wrapper and tested).
- **Ablation model (one factor changed):** `BAAI/bge-m3` (568M, 1024-d, MIT, strong on Indic) once the baseline path works. Model names verified on the model cards at download time.
- **Interface:** `Embedder.encode(texts, kind: 'query'|'passage') -> ndarray` (L2-normalised), so cosine = dot product and the stored vectors work with pgvector `<=>`.
- **Storage:** `chunk_embeddings(chunk_id, model, dim, embedding)`; index per model. Embedding is idempotent: skip (chunk_id, model) pairs already stored. Batches seeded/deterministic (CPU inference).
- **Retrievers:** `DenseRetriever` (in-memory numpy brute force for evaluation reproducibility; pgvector for the app) and hybrid RRF with BM25 (`rrf`, k=60).
- **Acceptance:** unit tests with a fake embedder (prefix handling, normalisation, idempotence, ranking); smoke test on the real model only after install; no quality numbers until gold items exist.

## Eval runner smoke test (2026-11-01) — pipeline check, NOT a result
`src.evalrunner.run_retrieval` ran end-to-end on 11 LLM-drafted, human-unreviewed pilot items (5 en, 6 hi) for `bm25` and `bm25char` (recall@5 = 1.0 for both). These numbers say nothing about retrieval quality: n is tiny, and drafted questions are written while looking at the gold passage, so they share vocabulary with it (lexical leakage favours BM25). Real comparisons need >= 100 human-validated items per language, with questions written independently of the evidence picker (docs/04). Drafts live in `data/gold/drafts/` (gitignored) with `review_status: unreviewed`.
The pilot sheet sampler now filters for service-relevant passages (eligibility/benefit/process keywords); Kannada yields only 10 candidates under that filter, so Kannada pairs will come mainly from aligned en twins.

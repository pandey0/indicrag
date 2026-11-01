# 04 Labelling guide

## Unit
One QA item = question + gold answer + evidence span(s) in a specific document version.

## Question types (aim for balance)
1. factoid (who/what/when/amount)
2. procedure (how to apply, steps)
3. eligibility (conditions; multi-clause)
4. document-list (what documents needed)
5. comparison/exception (two clauses interact)
6. unanswerable (answer is NOT in the corpus; correct behaviour = refuse)
7. cross-lingual (question in language A, evidence in language B)
Minimum 100 items/language for v0.1 (target 150 for v1.0). Target mix per language: 30% factoid, 25% procedure, 15% eligibility, 10% doc-list, 10% unanswerable, 5% comparison, 5% cross-lingual.

## Writing questions
- **Avoid wording leakage:** the person who picks the evidence should not be the only one who writes the question. Use one of: (a) a second person writes questions from a short topic brief, not the doc text; (b) an LLM drafts questions from the doc and a human rewrites/validates them (`source_kind: llm_drafted_validated`); (c) real citizen-style queries from public forums/helpline FAQs (`source_kind: real_query`, check terms). Tag every item with `source_kind` and `writer`. Report results per source_kind.
- **Noisy variants:** for >=25% of base items create linked variants (`variant_of`) with `register: romanized` (Hinglish/Romanized Kannada), `code_mixed`, or `noisy` (typos, missing diacritics, spoken style). They share the base item's evidence. Used to measure robustness.
- Write like a real citizen, not like the document. Allow colloquial, code-mixed (Hinglish/Kanglish) variants for a subset (tag `register: colloquial`).
- One intent per question. No leading phrasing.
- Do not copy sentences from the document into the question.

## Gold answer rules
- Short, complete, self-contained, in the question's language.
- Every claim must be supported by evidence spans. If it needs two spans, list both.
- Include conditions and amounts exactly; no outside knowledge.
- For unanswerable: gold answer = "not in corpus" + brief reason; evidence = none.

## Evidence spans
Store `doc_id, doc_sha256 (raw), parsed_sha256, parser_version, char_start, char_end` AND the verbatim `quote` of the span. Offsets refer to the parsed text; the quote allows validation (CI checks quote == text[start:end]) and re-anchoring after parser upgrades. Minimal span that fully supports the answer.

## Kannada protocol (aligned-parallel; no Kannada reader on the team)
1. Only use document pairs where the publisher provides official Kannada and English versions of the same content (record the pair in the manifest: `pair_id`).
2. Create the English item normally (question, answer, evidence span in the en doc).
3. Locate the Kannada span automatically: embed the en span and candidate kn sentences/paragraphs (multilingual embedder), take the best match; store `alignment_score`.
4. Kannada question = machine translation of the English question (LLM), `source_kind: aligned_parallel`, `aligned_with: <en id>`. Kannada answer = the aligned Kannada span text (extractive) rather than free-form generation.
5. Automated consistency gates (no Kannada reading needed): numbers, dates, amounts and named entities in the en and kn spans must match after normalising Kannada/Devanagari/Arabic numerals; alignment_score above a threshold chosen on a verified sample; items failing are dropped.
6. A native Kannada speaker checks a random sample (>=20% of items, at least 30) for question fluency, answer correctness and span correctness; set `native_verified: true` on checked items and report the error rate. If no native checker is found, ALL Kannada items stay `native_verified: false`, are marked experimental in the dataset card, and are excluded from headline claims.
7. OCR'd Kannada documents cannot be hand-corrected by the team; use only if layer-vs-OCR agreement and the parallel English text give independent support, otherwise exclude.

## Difficulty
easy (single sentence), medium (one section), hard (multi-span/multi-clause/cross-lingual).

## Process and quality
1. Pilot: label 10 items, refine this guide.
2. Label in batches of 20; keep a log of ambiguities.
3. Second annotator reviews >=20% sample (friend/colleague fluent in the language; credit them), blind to the first labeller's evidence span where feasible. Report: span-overlap F1, answer-correctness agreement (Cohen's kappa on correct/incorrect against the second annotator's own answer), answerable/unanswerable agreement. Report per language.
4. Disagreements resolved and recorded; guide updated.
5. Freeze dataset version (semver), tag in git, write dataset card.

## JSONL schema
See `data/schema/qa_item.schema.json`. CSV working template: `data/labelling/labelling_sheet_template.csv`.

## Ethics
No real people's data. No medical/legal individual advice content beyond what the public document states. Label sensitive topics carefully (benefits/eligibility errors can harm users).

## Pilot sheet generator (`scripts/make_labelling_sheet.py`)
Samples candidate evidence paragraphs (150-700 chars, noise-gated, max 2 per document, fixed seed) from the Wikipedia fallback corpus into `data/labelling/pilot_sheet.csv` (gitignored: contains corpus text). Evidence offsets, hashes and the verbatim quote are prefilled, so the picker is the script and a different person writes the question. Kannada rows are `aligned_parallel` with the English twin named in `notes`; Kannada questions are never authored here. Validate completed items with `python3 -m src.evalrunner.validate_gold <gold.jsonl>` (schema, unique ids, stale-pin detection, `quote == text[start:end]`).

## Kannada alignment triage (automated, pre-native-check)
`scripts/align_kn_candidates.py` proposes up to 3 Kannada paragraphs per English item whose Wikipedia article has a Kannada twin, scored by cross-lingual embedding cosine (`alignment_score`) plus `numeric_coverage` (share of the English quote's numbers, with Indic digits normalised, found in the Kannada paragraph). First run on 7 twin-capable drafts: 3 had coverage >= 0.75 (likely real counterparts), 3 had <= 0.12 (the Kannada article most likely lacks the fact: do not create a Kannada item), 1 partial. Kannada Wikipedia is much shorter than English, so many English items will have **no** Kannada counterpart; Kannada item count is bounded by this, not by labeller time. Every proposed pair still needs the native check (`native_verified`), and Kannada results stay a separate unverified slice.

## Reviewing drafts (fast path)
`python3 scripts/review_drafts.py data/gold/drafts/*.jsonl --reviewer <your-name>` shows the quote, question and answer for each unreviewed English/Hindi draft; press `a` (agree), `e` (edit then agree), `r` (reject), `s` (skip) or `q` (quit, progress kept in `data/gold/.reviewed`). Agreed/revised items pass the validator (including answer numbers appearing in the quote) and are appended to `data/gold/dev.jsonl`; rejects go to `data/gold/rejected.jsonl`. Kannada items are skipped: they need a native reviewer. What to check per item: (1) the quote alone supports the answer, (2) the question is something a citizen would plausibly ask and does not copy the passage wording, (3) the answer is short and has no facts beyond the quote. When in doubt, reject: a small clean set beats a large doubtful one.

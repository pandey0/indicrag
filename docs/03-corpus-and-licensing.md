# 03 Corpus and licensing

## Rule
Use ONLY documents whose licence/terms allow storage, derivative analysis and redistribution of labels. Redistribute LABELS + spans + URLs + hashes; redistribute document text ONLY if the licence clearly allows it. Record every decision in `data/corpus_manifest.csv`.

## Candidate source families (UNVERIFIED: check each site's terms, robots.txt and licence before use)
| Family | Why useful | Languages | Check |
|---|---|---|---|
| Government service FAQs/process pages (e.g., scholarship, pension, ration, agricultural subsidy schemes) | citizen questions, eligibility rules | en, hi, sometimes kn | terms of use, whether pages are served per-language |
| State portals (Karnataka services pages) | Kannada content | kn, en | licence/terms; stability of URLs |
| RTI process documents and public guidelines | procedural Q/A | en, hi | licence; PDF quality |
| data.gov.in datasets | clear licensing (Government Open Data Licence - India, verify exact terms per dataset) | varies | per-dataset licence |
| Open textual explainers under permissive licences (e.g., CC-BY) | safe redistribution | varies | licence text |

Do not assume any family is permitted. First task of week 1 is to turn this table into a verified manifest.

## Manifest columns (`data/corpus_manifest.csv`)
`source_id, url, title, lang, publisher, licence_text_url, licence_verdict (allow/deny/unclear), robots_ok, fetched_at, sha256, parse_status, role, snapshot_url, notes`

## Verdict rules
- allow: licence explicitly permits reuse (or public-domain/government open licence) -> include text.
- unclear: do NOT redistribute text; may use locally for research only if terms allow; prefer dropping.
- deny: exclude.

## Quality checks per document
Language correct, text extractable (not image-only), recent enough, stable URL, no personal data, no outdated-scheme traps (record "valid as of" date; questions must reference the document version).

## Target corpus size
- **Labelled set:** 30-60 documents, >=10 per language where available. Quality over volume.
- **Distractor pool:** several hundred additional unlabelled docs (same licence rules) including sibling schemes with overlapping wording, older versions of the same page, and same-topic docs in other languages. Without it retrieval is trivially easy and ablations show nothing. Pool docs are indexed but never used for questions.

## Kannada source rule
Kannada documents enter the labelled set only as part of an official kn/en parallel pair (manifest column `pair_id`). Kannada-only documents may be used as distractors, not for questions.

## Parse-feasibility spike (week 1, before finalising sources)
Many Hindi/Kannada government PDFs use legacy non-Unicode fonts (extract as garbage), are scanned images, or hide content in tables. For each candidate: extract text, eyeball 3 passages, record `parse_status` (ok / needs_ocr / legacy_font / broken_text / ocr_ok / ocr_poor / fail / fetch_failed) in the manifest. Week-1 results: `docs/12-week1-parse-findings.md`. Prefer HTML and Unicode-text PDFs. Decide OCR go/no-go from the failure rate; OCR output quality must be spot-checked before labelling on it.

## Redistribution fallback
If text cannot be redistributed: release labels, spans, verbatim `quote`s (check they are short enough to be fair use / permitted), URLs, hashes, fetch scripts, and Internet Archive snapshot URLs where permitted. Many government sites carry no explicit licence: do not assume 'public' means 'reusable'; read the site's content/copyright policy and record the quote of the clause in `notes`.
Add manifest columns: `parse_status, role (labelled|distractor), snapshot_url, pair_id`.

## Existing third-party datasets reviewed (2026-11-01)
Searched Kaggle, Hugging Face and IEEE DataPort for reusable Hindi/Kannada citizen-service data. Verdicts are drafts; licences must be re-checked on each page before use.

| Dataset | What it is | Verdict |
|---|---|---|
| HF `Shree0804/Multilingual_Government_Schemes_Dataset` (1,213 rows) | myScheme-style schemes; Hindi body in `details_hi`; Kannada only names/tags | No licence stated, no card, many garbled Hindi/Kannada rows: **do not use** as corpus or labels |
| IEEE DataPort JanMitra (4,706 schemes; 6,000 queries x 6 langs) | Template-generated queries over scraped myScheme; synthetic profiles | Subscription/login required, no licence stated, queries template-made not human: **not usable as gold**; at most a related-work citation |
| HF scraped myScheme sets (`*/gov_myscheme`) | Third-party scrapes of the same source we ingest directly | Redundant; our own attributed pull is cleaner |
| IndicGenBench XQuAD-IN / XorQA-IN (Google) | Human-translated extractive QA over Wikipedia passages, hi and kn included | Possible **external sanity check** for the retriever/judge on hi/kn (different domain); verify licence per card (XorQA card says MIT; XQuAD-IN field blank) |
| MILU (AI4Bharat) | Multiple-choice exam benchmark, CC BY 4.0, gated | Not a RAG corpus; skip |
| No Kaggle dataset found for hi/kn scheme text | | |

Takeaway: no ready-made licensed corpus replaces our own. Wikipedia (CC BY-SA 4.0) is the fallback for Hindi/Kannada prose (`scripts/discover_wikipedia.py`).

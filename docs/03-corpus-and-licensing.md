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

## Parse-feasibility spike (week 1, before finalising sources)
Many Hindi/Kannada government PDFs use legacy non-Unicode fonts (extract as garbage), are scanned images, or hide content in tables. For each candidate: extract text, eyeball 3 passages, record `parse_status` (ok / needs_ocr / legacy_font / fail) in the manifest. Prefer HTML and Unicode-text PDFs. Decide OCR go/no-go from the failure rate; OCR output quality must be spot-checked before labelling on it.

## Redistribution fallback
If text cannot be redistributed: release labels, spans, verbatim `quote`s (check they are short enough to be fair use / permitted), URLs, hashes, fetch scripts, and Internet Archive snapshot URLs where permitted. Many government sites carry no explicit licence: do not assume 'public' means 'reusable'; read the site's content/copyright policy and record the quote of the clause in `notes`.
Add manifest columns: `parse_status, role (labelled|distractor), snapshot_url`.

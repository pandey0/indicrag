# 17 Dataset card (DRAFT, status as of 2026-11-01)

**Status: no dataset release exists.** This card records what is true now so claims cannot outrun the data. The labelled set (`data/gold/`) does not exist yet; only unreviewed LLM drafts do.

## Intended use
Evaluating retrieval and answer quality of RAG systems on Indian citizen-service questions in English, Hindi and Kannada. Not for training; not a source of legal, financial or eligibility advice.

## Corpus (local, not redistributed; `redistribute=false` for every row until a human approves a licence verdict)
| language | source | docs | characters |
|---|---|---|---|
| en | myScheme scheme pages (rendered) | 247 | 1.63M |
| en | other government PDFs/pages | 14 | 0.19M |
| en | Wikipedia (CC BY-SA 4.0) | 39 | 0.60M |
| hi | Wikipedia (CC BY-SA 4.0) | 36 | 0.18M |
| hi | other government (RTI portal, Bihar RTPS, OCR'd Acts) | 6 | 0.25M |
| kn | Wikipedia (CC BY-SA 4.0) | 13 | 0.07M |
| kn | other government (Seva Sindhu, Karnataka School Education, OCR'd PDFs) | 9 | 0.06M |

21 further myScheme pages fetched as empty shells and are excluded (`parse_status=fail`). Hindi and Kannada prose is mostly encyclopedic (Wikipedia) because official Hindi/Kannada sources were blocked to bots, TLS-broken, or had no usable licence; Kannada volume is small.

## Collection and processing
Polite fetch (robots.txt honoured, 2 s per-host delay, no TLS bypass), content-addressed raw storage (sha256), parser-versioned extraction with OCR fallback (Tesseract) and a text-layer-vs-OCR agreement check, per-host boilerplate removal, chunking (512-token-budget fixed chunks, script-aware token approximation). OCR error rates have **not** been measured; Kannada OCR quality cannot be judged by the team.

## Annotation (planned, not done)
Gold evidence is a span (`doc_id`, `parsed_sha256`, offsets, verbatim quote). Questions are LLM-drafted from sampled passages and must be human-validated (`scripts/review_drafts.py`); questions are never written solely by the evidence picker. Kannada items are aligned-parallel only (English twin article, embedding alignment score plus numeric-consistency check, then a native-speaker check); they are reported as a separate unverified slice and are never described as natively authored. No inter-annotator agreement exists yet.

## Known limitations
- Wikipedia is not authoritative guidance and can be out of date; each item carries a valid-as-of date.
- Most items are single-fact, single-document; multi-hop, comparison and unanswerable coverage is minimal.
- LLM-drafted questions share vocabulary with their source passage (lexical leakage favours lexical retrievers); human rewrites are required before any comparison is reported.
- Sampling is keyword-filtered toward eligibility/benefit/process text, so it over-represents scheme-rule passages.
- English dominates the corpus (about 2.4M characters vs 0.4M Hindi and 0.13M Kannada); cross-language scores are not directly comparable without the distractor pool being matched.

## Licence statement (draft)
Gold labels and tooling: repository licence. Corpus text: not redistributed. Wikipedia-derived text, if ever redistributed, must carry attribution and share-alike (CC BY-SA 4.0). Government-source verdicts are drafts awaiting human approval (`data/licence_review/verdicts.csv`); this is not legal advice.

## Contact and deletion
To be added before any public release.

# 12 Week-1 parse-feasibility findings

Run: `scripts/week1_parse_spike.py` over `data/spike_candidates.csv` (22 public candidates). Machine-readable results: `data/corpus_manifest.csv`, metrics table: `data/spike/report.md`. Heuristics live in `src/parse/quality.py` (unit-tested). All `licence_verdict` values are still `unclear`: **licence review has not been done**, so nothing here is cleared for use yet.

## Results
| Outcome | Count | Notes |
|---|---|---|
| Digital text extracts correctly (`ok`) | 15 | all English PDFs/HTML, 4 Kannada HTML (Seva Sindhu), 3 Hindi HTML (RTI portal) |
| Needs OCR, OCR sample readable (`ocr_ok`) | 6 | see below |
| Fetch blocked (`fetch_failed`) | 1 | PIB returned 403 to our bot UA; not bypassed |
| Candidates dropped before run | 1 | NFSA Hindi URL returned 404 |

## Findings that change the plan
1. **Kannada digital sources exist as HTML** (Seva Sindhu FAQ, service pages): clean Unicode, genuine citizen Q&A. Prefer HTML for Kannada.
2. **Government PDFs are the risk, in three distinct ways** (not just "legacy fonts"):
   - *Image-only PDFs* (Karnataka Ahara citizen charter kn/en, holiday list): no text layer.
   - *Scanned PDF with garbage OCR layer* (RTI Act, Hindi): embedded text is nonsense; extractor choice does not help.
   - *Unicode PDF with broken glyph map* (RTI Act amended, Hindi): ~2,700 U+FFFD, missing matras/conjuncts; identical under PyMuPDF and pdftotext. Also seen as a partial defect in the Hindi half of a bilingual English/Hindi PDF.
   `parse_status` therefore distinguishes `needs_ocr`, `legacy_font`, `broken_text`.
3. **OCR is viable.** Tesseract 4.1 with `hin`/`kan` models (installed user-space, no root) produced readable Hindi and Kannada on sampled pages. Known Kannada weakness: dropped conjuncts/viramas (e.g. "ಪ್ರಮುಖ" -> "ಪಮುಖ", "ಸರ್ಕಾರ" -> "ಸಕಾನರ" on the cover page). Spans labelled on OCR text inherit these errors.
4. **Encoding trap:** `requests` defaults to ISO-8859-1 when a page declares no charset, producing Indic mojibake; the script decodes UTF-8 first.
5. **Heuristic status is a screen, not proof.** `ocr_ok` only means the sampled OCR text is mostly the right script. Quality still needs a human read, and word-error-rate on a hand-corrected sample is the real test.
6. Some hosts failed TLS or timed out from this network (pmkisan, NSAP, PMJAY, Karnataka portal); certificate verification was not disabled. Re-test from another network before dropping them.
7. Several sites publish no robots.txt (404); that means "no published restriction", not permission.

## Gate status (roadmap W1)
- Manifest with verdicts: **not met**: parse status recorded, licence verdicts pending.
- >=5 usable docs per language: English met; Kannada met (4 digital + 2 OCR candidates); **Hindi weak**: 3 digital pages are portal/about content, not scheme Q&A; 2 Hindi PDFs need OCR.

## Decisions / next steps
1. Adopt OCR as a supported path (Tesseract hin/kan; record `ocr_engine` + version in `parser_version`); full-document OCR on `ocr_ok` PDFs, then hand-correct a 3-page sample to measure error rate before labelling on OCR text.
2. Find Hindi scheme-FAQ HTML sources (scholarships, ration, pensions, agriculture schemes) and more Kannada scheme pages; target >=10 digital-text docs per language.
3. Do the licence/terms review for every candidate (read each site's content policy, record the clause in `notes`), then set `allow/deny`.
4. Promote the fetch/parse logic from the spike script into `src/ingest` and `src/parse` with golden tests using short fixtures.

# 12 Week-1 parse-feasibility findings

Run: `scripts/week1_parse_spike.py` over `data/spike_candidates.csv` (32 public candidates). Results: `data/corpus_manifest.csv` (one row per candidate) and `data/spike/report.md` (metrics, no document text). Heuristics: `src/parse/quality.py` (unit-tested). **Every `licence_verdict` is still `unclear`: licence review has not been done, so nothing here is cleared for use.**

## Results (32 candidates)
| Language | ok (digital text) | needs OCR, sample readable | fetch failed |
|---|---|---|---|
| en | 12 | 2 | 0 |
| hi | 4 | 2 | 1 (PIB 403 to our bot; not bypassed) |
| kn | 8 | 3 | 0 |
`ok` means the heuristics passed. It does **not** mean the content is useful (see findings 5, 6).

## Findings that change the plan
1. **Kannada digital sources exist as HTML** (Seva Sindhu FAQ and service pages: genuine citizen Q&A in clean Unicode). Prefer HTML for Kannada.
2. **Government PDFs fail in distinct ways:** image-only (Ahara citizen charter kn/en, holiday list); scanned PDF with garbage OCR layer (RTI Act, Hindi); Unicode with broken glyph map (RTI Act amended, Hindi, ~2,700 U+FFFD); **text layer that looks valid but has corrupted vowel signs** (Karnataka RTI manual, Kannada: "ಅಧಿಕಾರಿಗಳು" extracted as "ಅಧಿಕನರಿಗಳು").
3. **Character-level heuristics cannot catch finding 2's last case.** It passed every metric. Added a text-layer vs OCR word-overlap check (`layer_ocr_agreement`); the RTI manual scores 0.06 (threshold 0.3) and is now flagged. Limitation: the threshold is uncalibrated because no known-good Indic PDF is in the set yet.
4. **OCR is viable.** Tesseract 4.1 with `hin`/`kan` (installed user-space, no root) gave readable Hindi and Kannada. Known Kannada weakness: dropped conjuncts (e.g. "ಪ್ರಮುಖ" -> "ಪಮುಖ"). Labels on OCR text inherit such errors; OCR error rate on a hand-corrected sample is still unmeasured.
5. **myScheme (MeitY, ~5,150 schemes) is an English-content source, not Hindi/Kannada.** Its UI labels are translated into hi/kn, but the scheme body text stays English (verified for one scheme in all three locales). Content is rendered client-side, so a headless browser is needed. Its copyright policy allows free reproduction if accurate, attributed and non-misleading; robots.txt allows crawling. Good candidate for English labelled docs and the distractor pool, subject to the formal licence review.
6. **Some `ok` pages are mostly boilerplate.** The Karnataka School Education pages exist in parallel kn/en versions (useful for cross-lingual items) but their text is dominated by accessibility/navigation tables with little substantive content. The Bihar RTPS home page is a long Hindi list of services whose detail pages sit behind session links. A main-content extraction / content-density check is needed before treating these as QA sources.
7. **Encoding trap:** `requests` decodes pages without a declared charset as ISO-8859-1, producing Indic mojibake; the script decodes UTF-8 first.
8. Several hosts failed TLS or timed out from this network (pmkisan, NSAP, PMJAY, Karnataka portal, many state sites); certificate verification was not disabled. Re-test from another network. Missing robots.txt means "no published restriction", not permission.

## Gate status (roadmap W1)
- Licence verdicts in manifest: **not met** (parse status recorded; licence review pending).
- >=5 usable docs per language: technically met for en/hi/kn, but **Hindi and Kannada usable-content volume is low**: Hindi has no citizen-scheme Q&A source yet (RTI portal and Bihar service list only); Kannada has Seva Sindhu plus thin department pages.

## Decisions / next steps
1. Add main-content extraction + a content-density metric; re-score the HTML candidates.
2. Hindi remains the weak spot: look for Hindi-native scheme/service content (more state portals, department FAQs, Hindi PDFs via OCR), possibly accepting OCR'd Hindi government documents as the main Hindi source. If Hindi cannot reach a usable corpus, the roadmap's pivot applies (ship en+kn, or hi via OCR with documented error rate).
3. Measure OCR error on a hand-corrected sample (3 pages per language) before labelling on OCR text; calibrate the layer-vs-OCR threshold on a good Indic PDF.
4. Licence/terms review for every candidate (read each site's content policy, record the clause in `notes`), then set `allow/deny`. This needs a human decision.
5. Promote fetch/parse logic into `src/ingest` and `src/parse` with golden tests on short fixtures; add a headless-render fetcher for JS sites (myScheme).

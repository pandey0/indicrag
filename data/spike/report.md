# Week-1 parse-feasibility report

Generated 2026-10-31 17:20 UTC by `scripts/week1_parse_spike.py`. Metrics only (no document text).
Heuristic status is NOT a quality guarantee: every `ok` still needs a human spot-check (see notes below).

| source_id | exp. lang | kind | status | chars | pages | dev | kan | lat | latin1 | orphan marks | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rti_act_en | en | pdf | ok | 56664 | 23 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| rti_act_hi | hi | pdf | ocr_ok | 40576 | 27 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | expected hi, target-script share 0.00 (legacy encoding or bad OCR layer; or mislabelled lang) -> OCR(3p): ocr_ok, script-share 0.56 |
| rti_act_amended_en | en | pdf | ok | 58350 | 25 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| rti_act_amended_hi | hi | pdf | ocr_ok | 45331 | 21 | 1.00 | 0.00 | 0.00 | 0.00 | 0.05 | unmapped glyphs (cid/PUA/replacement chars) -> OCR(3p): ocr_ok, script-share 0.95 |
| ahara_charter_kn | kn | pdf | ocr_ok | 0 | 13 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | almost no text layer -> OCR(3p): ocr_ok, script-share 0.80 |
| ahara_charter_en | en | pdf | ocr_ok | 0 | 13 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | almost no text layer -> OCR(3p): ocr_ok, script-share 1.00 |
| sevasindhu_faq_kn | kn | html | ok | 3505 | 1 | 0.00 | 0.98 | 0.02 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| sevasindhu_track_kn | kn | html | ok | 8645 | 1 | 0.00 | 0.21 | 0.79 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| sevasindhu_gramaone_kn | kn | html | ok | 2366 | 1 | 0.00 | 0.94 | 0.06 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| sevasindhu_depts_kn | kn | html | ok | 6499 | 1 | 0.00 | 0.28 | 0.72 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| sevasindhu_esign_en | en | pdf | ok | 1353 | 9 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| ceg_holidays_2021_kn | kn | pdf | ocr_ok | 0 | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | almost no text layer -> OCR(3p): ocr_ok, script-share 0.96 |
| nfsa_mera_ration_faq_en | en | pdf | ok | 1102 | 1 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| nfsa_home_en | en | html | ok | 1175 | 1 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| nsp_student_faq_en | en | html | ok | 536 | 1 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| nsp_officer_faq_en | en | pdf | ok | 4006 | 5 | 0.10 | 0.00 | 0.90 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| nsp_npci_base_en | en | pdf | ocr_ok | 1100 | 3 | 0.21 | 0.00 | 0.79 | 0.00 | 0.09 | orphan combining marks 0.09 -> OCR(3p): ocr_ok, script-share 1.00 |
| mygov_faq_en | en | html | ok | 10710 | 1 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| rti_home_hi | hi | html | ok | 1145 | 1 | 0.90 | 0.00 | 0.10 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| rti_about_hi | hi | html | ok | 753 | 1 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| rti_actpage_hi | hi | html | ok | 233 | 1 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| pib_about_hi | hi | html | fetch_failed | - | - | - | - | - | - | - | HTTPError: 403 Client Error: Forbidden for url: https://www.pib.gov.in/aboutpibh.aspx |
| ksedu_primary_kn | kn | html | ok | 13758 | 1 | 0.00 | 0.82 | 0.18 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| ksedu_primary_en | en | html | ok | 12003 | 1 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| ksedu_midday_kn | kn | html | ok | 14725 | 1 | 0.00 | 0.83 | 0.17 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| ksedu_midday_en | en | html | ok | 12507 | 1 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| ksedu_swf_kn | kn | html | ok | 14079 | 1 | 0.00 | 0.82 | 0.18 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| ksedu_swf_en | en | html | ok | 12294 | 1 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| ksedu_minority_kn | kn | html | ok | 14422 | 1 | 0.00 | 0.82 | 0.18 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| ksedu_minority_en | en | html | ok | 12585 | 1 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| bihar_rtps_home_hi | hi | html | ok | 103838 | 1 | 0.45 | 0.00 | 0.55 | 0.00 | 0.00 | passes heuristics (still needs human spot-check) |
| karnataka_rti_manual_kn | kn | pdf | ocr_ok | 2183 | 7 | 0.00 | 0.90 | 0.10 | 0.00 | 0.04 | text layer disagrees with OCR (word overlap 0.06); vowel signs likely corrupt -> OCR(3p): ocr_ok, script-share 0.59 |

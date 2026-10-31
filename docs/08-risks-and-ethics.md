# 08 Risks and ethics
| Risk | Impact | Mitigation |
|---|---|---|
| Source terms forbid reuse/scraping | cannot publish text | licence manifest; release labels+spans+scripts only; prefer open-licence sources |
| Labelling quality (single annotator) | weak benchmark | guide, pilot, second-annotator sample, kappa reported |
| LLM-judge bias | misleading numbers | different-family judge, rubric, human sample, publish agreement |
| Outdated government rules | wrong answers | record "valid as of" date; questions tied to document version; show date in UI |
| Harm from wrong eligibility answers | real-world harm | citations, disclaimer, refusal on missing evidence, no individual advice |
| DPDP Act / privacy | legal exposure | no personal data collected; feedback has no identifiers; no user accounts |
| Cost overruns | project stalls | smoke eval in CI, cheap models, cache embeddings, budget alarms |
| Scope creep | never ships | gates + kill criteria in roadmap |
| Over-claiming | credibility loss | docs/09 claim boundaries |
| Public demo cost abuse | surprise bill, outage | provider spend limit, daily budget cap, rate limits, retrieval-only degradation (docs/11) |
| Prompt injection via documents | wrong/hostile answers, leaks | delimited data blocks, citation validation, read-only tools, injection test set |
| Users type personal data into questions | DPDP exposure | UI warning, PII scrubber before logging, 30-day retention, opt-in feedback |
| Question wording leaks document wording | inflated retrieval scores | separate writer / LLM-drafted + validated / real queries; report per source_kind |
| Benchmark too easy (tiny corpus) | saturated, uninformative results | distractor pool, long-context + closed-book baselines |
| Legacy-font / scanned Indic PDFs | silent garbage text, bad labels | week-1 parse spike, parse_status, golden parser tests, OCR spot-checks |
| Judge unreliable in Kannada | misleading numbers | per-language judge-human agreement; fall back to human scoring |
| Underpowered comparisons | false conclusions | paired stats, power check, report 'no evidence of difference' |
| No Kannada reader on the team | Kannada labels/OCR/judge unverifiable | aligned-parallel protocol, automated consistency gates, native sample check, separate unverified slice, no headline claims (docs/04) |
| Other company's IP | legal/ethical | this project uses only public sources and personal time/equipment; no employer or client code or data |

## Responsible release
Dataset card with intended use, limitations (language coverage, domain, annotator count), and contact for corrections. Versioned releases; changelog.

# Gold set notice

`dev.jsonl` holds 100 questions with short verbatim evidence quotes and character offsets into the source documents. It does not contain the full source documents.

- Evidence quotes from Wikipedia (`wp_*` documents) are CC BY-SA 4.0 text from Wikipedia contributors. Attribution is by the source URL of each document in `data/sources_wikipedia*.csv`. Those quotes, and works that adapt them, stay under CC BY-SA 4.0.
- Evidence quotes from myScheme (`ms_*` documents) are short excerpts from the Government of India portal myScheme (myscheme.gov.in), included for research and evaluation. No permission was requested from the portal owners. If you represent a source and want an excerpt removed, open an issue.
- Questions and answers were drafted by an LLM and reviewed by one author-reviewer (see `eval/RESULTS.md` for limits).
- The full raw and parsed corpus is not included. Rebuild it locally with the ingestion pipeline.
- The code licence (MIT, `LICENSE`) does not cover this data.

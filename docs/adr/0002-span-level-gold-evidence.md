# ADR 0002: Gold evidence is a character span, not a chunk id
Status: accepted (2026-10-31).

**Context.** If gold labels point at chunk ids, every change of chunker invalidates the labels and chunkers cannot be compared fairly.

**Decision.** Each evidence item stores `doc_sha256`, `parsed_sha256`, `parser_version`, `char_start`, `char_end` and a verbatim `quote`. A retrieved chunk is a hit if it contains the span or overlaps it by at least 50%. CI-style validation (`src/evalrunner/validate_gold.py`) checks `quote == text[start:end]` and that numbers in the answer appear in the quotes.

**Consequences.** Retrieval metrics are chunker-independent. A re-fetched or re-parsed document invalidates labels, which is intended: re-anchor from the quote under a new `parser_version`. Cost: labelling needs offsets, so drafting is tool-assisted.

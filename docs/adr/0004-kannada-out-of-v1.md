# ADR 0004: Kannada is out of v1
Status: accepted (2026-11-01).

**Context.** The author reads English (and Hindi) but not Kannada. Labels, answers and judgements in a language nobody on the project can read cannot be validated, and the repo must not claim what it cannot check.

**Decision.** v1 covers Hindi and English only. Kannada documents and the aligned-parallel tooling (`src/evalrunner/align.py`, `scripts/align_kn_candidates.py`) stay as groundwork. No Kannada gold items, results or claims until a native validator exists.

**Consequences.** The headline benchmark is smaller in scope but every label is checkable. Kannada chunks still sit in the index as distractors (161 chunks).

# ADR 0003: Score generation by number recall, not an LLM judge
Status: accepted (2026-11-01).

**Context.** `docs/05` forbids judging with the same model family as the generator, and no other family was available. A same-family judge would flatter the system.

**Decision.** Score answers by the share of the gold answer's numbers (Indic digits normalised, thousands separators and leading zeros dropped) that appear in the generated answer, only on items whose gold answer has numbers (60 of 96). Also report citation validity, whether the cited chunk hits the gold span, and abstention on unanswerable items.

**Consequences.** Objective and reproducible, but weak: it cannot see wrong answers that contain the right numbers, and it says nothing about faithfulness or fluency. Results must always be reported with this limit. Revisit when a cross-family judge and human-calibration data exist.

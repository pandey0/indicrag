# ADR 0006: Model persona review as advisory input, adopted per batch by the author
Status: accepted (2026-11-01).

**Context.** One author-reviewer is the only human, and review capacity limits dataset size.

**Decision.** From batch 7 on, a read-only model subagent produces advisory accept/reject/edit decisions for each batch of drafts. The author must explicitly adopt each batch before it is applied; nothing is applied on the model's authority. Items carry `review_status` and `reviewer`; the validator gates every save.

**Consequences.** Faster review, but 25 of 100 items were checked by a model reviewer whose decisions the author adopted, and the same model family drafted the questions. The README and `eval/RESULTS.md` say so wherever the item count is quoted. A second human reviewer and an agreement statistic remain open.

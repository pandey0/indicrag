# 07 Agent phase (phase 3)

## Purpose
Back the "LLM agents" claim with a measured system, not a demo.

## Task family
Multi-step citizen-service tasks, e.g.:
1. "Am I eligible for scheme X?" -> retrieve eligibility section -> extract criteria -> ask/accept user attributes (provided in the task) -> evaluate rules -> answer with citations.
2. "What documents do I need to apply for Y in Kannada?" -> retrieve -> list -> translation consistency check.
3. "Compare scheme A vs B" -> retrieve both -> structured comparison with citations.

## Tools (keep few and deterministic)
`search_docs(query, lang, k)`, `get_section(doc_id, section_path)`, `extract_criteria(text)` (LLM-structured output validated by schema), `evaluate_rules(criteria, attributes)` (pure Python), `check_translation(source_text, target_text)` (LLM + heuristics).

## Controls
Max steps (e.g., 8), token budget, tool timeout, schema validation, refusal when evidence missing, full JSON trace per run.

## Evaluation
- Task success (programmatic check against gold structured answer where possible)
- Tool-call accuracy (correct tool + valid args)
- Trajectory efficiency (steps vs optimal)
- Groundedness of final answer (reuse faithfulness metric)
- Failure taxonomy (loop, wrong tool, bad args, hallucinated rule, giving up early)
Compare: plain RAG vs agent on the same tasks.

## Focus
The valuable part is eligibility reasoning: `extract_criteria` -> `evaluate_rules` (deterministic). Prioritise this task family; generic multi-tool wandering is secondary. Report tasks with n and CIs; with ~30 tasks only large effects are detectable, and say so.

## Security
Tools are read-only and side-effect free; args schema-validated; outputs length-capped; documents are untrusted (indirect prompt injection). Include the injection test set from docs/11 and report attack success rate for plain RAG and the agent.

## Guardrails
Never present output as official eligibility decision; always cite sources; no PII storage.

## Claim boundary
This phase's claims are limited to what the published tool-call evaluation and traces show.

# 16 Agent implementation plan (week 9)

Scope: eligibility-focused agent (docs/07). Claims limited to what traces and the tool-call evaluation show. No agent quality claim exists yet.

## Order
1. **Rules engine** (`src/agent/rules.py`): pure Python `evaluate_rules(criteria, attributes)`. Criterion = `{attr, op, value, text?, source?}`, ops `>= <= > < == != in not_in between`. Three-valued outcome per criterion (`met | not_met | unknown` when the attribute is missing or the types are incomparable) and overall (`eligible` only if all met; `not_eligible` if any not_met; else `unknown`). Never guesses a missing attribute. Fully unit-tested; this is the deterministic part that gives the agent value.
2. **Tool registry** (`src/agent/tools.py`): each tool has a Pydantic argument model and a length-capped string output. Tools: `search_docs(query, k)`, `get_section(doc_id, section_path)`, `extract_criteria(text)` (LLM, JSON validated by schema; invalid output -> tool error), `evaluate_rules(criteria, attributes)`. All read-only; no network, file or code execution beyond the loaded corpus.
3. **Loop** (`src/agent/loop.py`): the model returns one JSON object per turn, either `{"tool": ..., "args": {...}}` or `{"final": {"answer", "citations", "decision"}}`. Controls: max steps, token budget, per-turn parse/validation errors are fed back once then counted, repeated identical call detected as a loop, citations must be chunk/doc ids seen in tool results. Every run yields a JSON trace (steps, tool, args, result summary, tokens, stop reason, prompt hash).
4. **Tests**: scripted provider drives deterministic trajectories (happy path, bad args, unknown tool, loop, budget stop, injected tool output, invalid citation).

## Safety
Tool outputs are untrusted data (indirect injection): wrapped in delimited blocks, length-capped, never executed. The final answer is labelled "not an official eligibility decision".

## Not in this step
Real-LLM task runs, the >= 30 task gold set, plain-RAG vs agent comparison (need provider key and human-written tasks).

## Status 2026-11-01
- `scripts/build_agent_tasks.py` builds 36 LLM-drafted eligibility tasks (17 eligible / 16 not eligible / 3 unknown) from myScheme and Wikipedia sentences; scenarios state only the person's facts and the scheme name (no thresholds). Gold criteria are hand-encoded from the quoted sentence; expected decisions are computed by the rules engine and cross-checked. `data/agent/` is gitignored (corpus quotes). All tasks are `review_status: unreviewed`: a human must confirm each gold criteria set encodes its sentence.
- `src.evalrunner.agent_eval` validates tasks and runs the harness (success, evaluate_rules use, tool errors, steps, tokens, cited gold document). CI-tested with a scripted oracle agent and a deliberately wrong agent. No real-model result exists (`python -m src.evalrunner.agent_eval`, needs `ANTHROPIC_API_KEY`).
- Caveat: tasks cover single-document, mostly single-criterion eligibility; they do not test multi-scheme comparison or Hindi/Kannada tasks.

## First real-model run (claude-haiku-5-5, 2026-11-01) — read the caveats
Protocol: tune on tasks agt-001..006 only, then run the other 30 once as the report set.

**What the real model exposed in MY harness (fixed before the report run):**
1. `extract_criteria` failed on every call that returned markdown-fenced JSON (parser wanted bare JSON). Now tolerant; tested.
2. `get_section` was an exact-prefix match with an unhelpful error; now substring match and the error lists available sections.
3. The loop guard killed a run on the first repeated call; now one repeat is fed back for recovery, a second ends the run.
4. The agent skipped `evaluate_rules` in 5/6 tuning tasks; the system prompt now states an explicit workflow.
5. `temperature` is rejected by the current models (400); removed from the provider (runs are no longer strictly deterministic).

**What it exposed in MY tasks (gold errors, fixed):** two tasks were wrong, not the agent: the Punjab old-age pension page also pays ₹500 to people 80+, so "82 years old -> not eligible" was incorrect; and schemes with extra mandatory criteria (residency, BPL) correctly yield `unknown` unless the task is scoped, so task text now says which requirement to consider. Lesson: gold encoded from one sentence misses neighbouring sentences; human review of every task is mandatory.

**Result on the 30 held-out tasks:** success 29/30 = 0.967 (Wilson 95% CI 0.83-0.99); the single failure was the 20,000-token budget, not a wrong decision. evaluate_rules used in 28/30; mean 13.5k tokens/task (405k total).

**Do not over-read this:** n=30; tasks are LLM-drafted and unreviewed; every task is English, single document, scoped to one or two numeric criteria that the task text names ("only consider the age requirement"), which is much easier than open-ended eligibility; the 6 tuning tasks are excluded but I wrote both the tasks and the tool fixes; no plain-RAG baseline and no second model were run, so nothing here shows an agent beats RAG; no Hindi/Kannada tasks. The decision guard (final decision must equal the evaluate_rules decision) also removes one failure mode by construction.

## Plain RAG vs agent, same 30 held-out tasks, fixed provider (claude-haiku-5-5, 2026-11-01)
Plain RAG = BM25 top-5 + one model call that must end with `DECISION: eligible|not_eligible|unknown` (no tools, no rules engine). Agent = the loop in this doc. Both ran after the provider fix that retries replies cut off at `max_tokens` (reasoning models were returning empty or truncated text).

| system | success (n=30) | mean tokens/task | notes |
|---|---|---|---|
| plain RAG | 0.967 (29/30) | 3.5k | one wrong decision (`agt-014`: said unknown, expected not_eligible) |
| agent | 0.867 (26/30) | 13.5k | all 4 failures were `token_budget` (20k cap): zero wrong decisions; `evaluate_rules` used in 27/30 |

Paired difference (agent - plain): -0.100, 95% bootstrap CI [-0.233, +0.033]. Wins: agent only on `agt-014`; plain only on `agt-017`, `agt-025`, `agt-026`, `agt-029`.

**Reading.** On these tasks the agent shows no accuracy advantage and costs about 4x the tokens; its failures were budget exhaustion, not wrong answers (the interval includes 0, so "plain is better" is also not established). The earlier agent run on the same tasks scored 0.967 (29/30); the drop to 0.867 comes from the provider fix, which makes some steps cost more (a retry counts its extra tokens) so more runs hit the fixed 20k budget, plus run-to-run variance (no `temperature`). I am not raising the budget now and re-reporting, because that would be tuning on the report set; a budget sweep belongs on a fresh task set.

**Why the tasks favour plain RAG:** every task is single-document, scoped to one or two numeric criteria that the question names, so a capable model can do the comparison in its head. The agent's design value (deterministic rules, guards, traces, auditability) is not what these tasks measure; tasks with several interacting criteria, missing-attribute follow-ups, or arithmetic-heavy income rules would test it. Not run: Hindi/Kannada tasks, other models, human-reviewed tasks.

## Harder task set (12 tasks, `scripts/build_agent_tasks_hard.py`), same conditions, tasks fixed before the run
Designed to stress what the agent was supposed to add: monthly-to-annual income arithmetic, two criteria at once, rural/urban thresholds, age relaxation by category (+5 SC/ST, +3 OBC), and a missing attribute.

**Task defect found by reading the failures:** `agt-h08` (income exactly ₹25,000, expected not eligible because the page says "less than ₹25000") was failed by both systems, and the Gatidhara page also says "income of ₹25000/- or less would qualify", so the source contradicts itself and my strict-`<` gold is unsafe. It is marked `excluded` (reason stored in the file), skipped by `load_tasks` by default, and the exclusion was decided from the source text, not from model behaviour. Both numbers are reported.

| system | success on 11 valid tasks | on all 12 | mean tokens (11) | failures (valid tasks) |
|---|---|---|---|---|
| plain RAG | 10/11 = 0.91 | 10/12 | 4.1k | `agt-h06` said "unknown" (urban income ₹1,30,000, expected eligible) |
| agent | 9/11 = 0.82 | 9/12 | 10.1k | `agt-h05` hit the 20k token budget; `agt-h06` returned a wrong decision (not eligible) |

Paired difference (agent - plain): -0.09, 95% CI [-0.27, 0.00]. Zero tasks where only the agent succeeded.

**Reading.** Even on tasks built to need arithmetic and multi-criterion reasoning, the agent did not beat plain RAG, and cost about 2.5x the tokens. The one wrong agent decision (`agt-h06`) is the informative failure: the agent evaluated rules but not with the urban threshold the question calls for (the deterministic engine only helps if the criteria it is given are right). The arithmetic and relaxation tasks (`h01`, `h02`, `h03`, `h09`, `h10`, `h11`) were solved by both. n=11 and one model: this does not show the agent is worse, and it does not show a benefit. It shows the claimed advantage was not demonstrated by this task family, so no "agent improves eligibility answers" claim is supported.

"""Harder agent tasks (data/agent/tasks_hard.jsonl): arithmetic (monthly -> annual income), two criteria at once, rural/urban thresholds,
age relaxation by category, strict '<' boundary, missing attribute. Same format as tasks.jsonl; expected decisions are computed by
src.agent.rules and checked against the hand-stated expectation. LLM-drafted, unreviewed. Tasks were fixed BEFORE any model run.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.agent.rules import evaluate_rules  # noqa: E402

man = {r["source_id"]: r for r in csv.DictReader(open("data/corpus_manifest.csv", encoding="utf-8"))}
B = lambda lo, hi: {"attr": "age", "op": "between", "value": [lo, hi]}  # noqa: E731
GB_AGE = "The age of the applicant should be between 25 years"
GB_INC = "The family income of the applicant should be less than"
PSW = "aged between 18 and 59"
RURAL = "If you reside in rural areas, your annual income"
URBAN = "If you reside in urban areas, your annual income"
INC_ANN = lambda v: {"attr": "annual_income", "op": "<=", "value": v}  # noqa: E731
INC_GB = {"attr": "family_monthly_income", "op": "<", "value": 25000}

# (doc, [anchors], criteria, task text, attributes, expected)
S = [
    ("ms_psw", [PSW], [B(18, 59), INC_ANN(150000)], "I am a 50 year old widow in Daman and my monthly income is ₹12,000. Am I eligible for the Pension Scheme to Widow?", {"age": 50, "annual_income": 144000}, "eligible"),
    ("ms_psw", [PSW], [B(18, 59), INC_ANN(150000)], "I am a 50 year old widow in Daman and my monthly income is ₹14,000. Am I eligible for the Pension Scheme to Widow?", {"age": 50, "annual_income": 168000}, "not_eligible"),
    ("ms_psw", [PSW], [B(18, 59), INC_ANN(150000)], "I am a 61 year old widow in Daman and my monthly income is ₹5,000. Am I eligible for the Pension Scheme to Widow?", {"age": 61, "annual_income": 60000}, "not_eligible"),
    ("ms_psw", [PSW], [B(18, 59), INC_ANN(150000)], "I am a 40 year old widow in Daman and I earn a small income. Am I eligible for the Pension Scheme to Widow?", {"age": 40}, "unknown"),
    ("ms_fasuw-ecw", [RURAL], [INC_ANN(120000)], "I live in a rural area and my annual income is ₹1,30,000. Am I eligible for the Funeral Assistance Scheme for Unorganized Workers (Except Construction Workers)?", {"annual_income": 130000}, "not_eligible"),
    ("ms_fasuw-ecw", [URBAN], [INC_ANN(150000)], "I live in an urban area and my annual income is ₹1,30,000. Am I eligible for the Funeral Assistance Scheme for Unorganized Workers (Except Construction Workers)?", {"annual_income": 130000}, "eligible"),
    ("ms_gs-west-bengal", [GB_AGE, GB_INC], [B(25, 45), INC_GB], "I am 30 years old, in the general category, and my family's monthly income is ₹20,000. Am I eligible for the Gatidhara Scheme?", {"age": 30, "family_monthly_income": 20000}, "eligible"),
    ("ms_gs-west-bengal", [GB_AGE, GB_INC], [B(25, 45), INC_GB], "I am 30 years old, in the general category, and my family's monthly income is exactly ₹25,000. Am I eligible for the Gatidhara Scheme?", {"age": 30, "family_monthly_income": 25000}, "not_eligible"),
    ("ms_gs-west-bengal", [GB_AGE, GB_INC], [B(25, 50), INC_GB], "I am 48 years old, belong to a Scheduled Caste, and my family's monthly income is ₹15,000. Am I eligible for the Gatidhara Scheme?", {"age": 48, "family_monthly_income": 15000}, "eligible"),
    ("ms_gs-west-bengal", [GB_AGE, GB_INC], [B(25, 48), INC_GB], "I am 49 years old, belong to an Other Backward Class, and my family's monthly income is ₹15,000. Am I eligible for the Gatidhara Scheme?", {"age": 49, "family_monthly_income": 15000}, "not_eligible"),
    ("ms_gs-west-bengal", [GB_AGE, GB_INC], [B(25, 45), INC_GB], "I am 47 years old, in the general category, and my family's monthly income is ₹15,000. Am I eligible for the Gatidhara Scheme?", {"age": 47, "family_monthly_income": 15000}, "not_eligible"),
    ("ms_gs-west-bengal", [GB_AGE, GB_INC], [B(25, 45), INC_GB], "I am 30 years old, in the general category. Am I eligible for the Gatidhara Scheme?", {"age": 30}, "unknown"),
]


def sentence(text, anchor):
    i = text.find(anchor)
    assert i >= 0, anchor
    s = max(text.rfind("\n", 0, i) + 1, text.rfind(". ", 0, i) + 2 if text.rfind(". ", 0, i) >= 0 else 0)
    ends = [x for x in (text.find("\n", i), text.find(". ", i) + 1) if x > 0]
    return s, (min(ends) if ends else len(text))


tasks = []
for doc, anchors, crit, text_, attrs, expect in S:
    r = man[doc]
    text = Path("data", r["text_path"]).read_text(encoding="utf-8")
    assert evaluate_rules(crit, attrs)["decision"] == expect, (text_, evaluate_rules(crit, attrs)["decision"], expect)
    ev = []
    for a in anchors:
        s, e = sentence(text, a)
        ev.append({"doc_id": doc, "doc_sha256": r["sha256"], "parsed_sha256": r["parsed_sha256"], "parser_version": r["parser_version"],
                   "char_start": s, "char_end": e, "quote": text[s:e]})
    excl = {"excluded": "source contradicts itself: another sentence on the page says '₹25000/- or less would qualify', so the strict '<' gold is not safe"} if "exactly ₹25,000" in text_ else {}
    tasks.append({**excl, "id": f"agt-h{len(tasks) + 1:02d}", "lang": "en", "task": text_ + " Only consider the age and income requirements stated in the scheme for this check; ignore any other requirements.",
                  "attributes": attrs, "gold_criteria": crit, "expected_decision": expect, "expected_tools": ["search_docs", "evaluate_rules"], "evidence": ev,
                  "review_status": "unreviewed", "writer": "claude-draft", "valid_as_of": "2026-11-01"})
Path("data/agent/tasks_hard.jsonl").write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in tasks) + "\n", encoding="utf-8")
print(len(tasks), "hard tasks")

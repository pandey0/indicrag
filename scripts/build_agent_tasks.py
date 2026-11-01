"""Build data/agent/tasks.jsonl: eligibility tasks grounded in corpus sentences (docs/07, docs/16).

Each task: scenario text, the evidence sentence (verbatim, offsets, hashes), gold criteria (structured, from that sentence), user
attributes and the expected decision, which is COMPUTED by src.agent.rules and checked against the hand-stated expectation.
Tasks are LLM-drafted and need human review (review_status=unreviewed): check that gold criteria faithfully encode the sentence.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.agent.rules import evaluate_rules  # noqa: E402

man = {r["source_id"]: r for r in csv.DictReader(open("data/corpus_manifest.csv", encoding="utf-8"))}
B = lambda lo, hi, attr="age": {"attr": attr, "op": "between", "value": [lo, hi]}  # noqa: E731
LE = lambda v, attr="annual_income": {"attr": attr, "op": "<=", "value": v}  # noqa: E731
GE = lambda v, attr="age": {"attr": attr, "op": ">=", "value": v}  # noqa: E731

# (doc, anchor in sentence, gold criteria, scenarios[(text, attributes, expected)])
SPECS = [
    ("ms_ignoapsp", "aged between 60 and 79 years to receive", [B(60, 79)],
     [("I am 65 years old. Am I eligible for the {scheme}?", {"age": 65}, "eligible"),
      ("My father is 82 years old. Is he eligible for the {scheme}?", {"age": 82}, "not_eligible")]),
    ("ms_ignwpsp", "only for widows aged 40", [GE(40)],
     [("I am a 35 year old widow. Am I eligible for the {scheme}?", {"age": 35}, "not_eligible"),
      ("I am a widow. Am I eligible for the {scheme}?", {}, "unknown")]),
    ("ms_igndpsp", "Eligible beneficiaries receive ₹300", [B(18, 79)],
     [("I am 45 years old and have a disability. Am I eligible for the {scheme}?", {"age": 45}, "eligible"),
      ("I am 17 years old and have a disability. Am I eligible for the {scheme}?", {"age": 17}, "not_eligible")]),
    ("ms_oap", "income is up to ₹4,000/-", [{"attr": "monthly_income", "op": "<=", "value": 4000}],
     [("Our family's monthly income is ₹3,500. Are we eligible for the {scheme}?", {"monthly_income": 3500}, "eligible"),
      ("Our family's monthly income is ₹6,000 and we are not BPL. Are we eligible for the {scheme}?", {"monthly_income": 6000}, "not_eligible")]),
    ("ms_fasuw-ecw", "income must not exceed ₹1,50,000/-", [LE(150000)],
     [("I live in an urban area and my annual income is ₹1,20,000. Am I eligible for the {scheme}?", {"annual_income": 120000}, "eligible"),
      ("I live in a city and earn ₹2,00,000 a year. Am I eligible for the {scheme}?", {"annual_income": 200000}, "not_eligible")]),
    ("ms_psw", "aged between 18 and 59 years", [B(18, 59), LE(150000)],
     [("I am a 40 year old widow in Daman with an annual income of ₹1,00,000. Am I eligible for the {scheme}?", {"age": 40, "annual_income": 100000}, "eligible"),
      ("I am a 45 year old widow in Daman. Am I eligible for the {scheme}?", {"age": 45}, "unknown")]),
    ("ms_gs-west-bengal", "age of the applicant should be between 25 years to 45 years", [B(25, 45)],
     [("I am 30 years old and live in West Bengal. Am I eligible for the {scheme}?", {"age": 30}, "eligible"),
      ("I am 50 years old and live in West Bengal. Am I eligible for the {scheme}?", {"age": 50}, "not_eligible")]),
    ("ms_byswb", "aged between 21 and 40 years are eligible", [B(21, 40)],
     [("I am a 28 year old educated unemployed youth in West Bengal. Am I eligible for {scheme}?", {"age": 28}, "eligible"),
      ("I am 41 years old, educated and unemployed, in West Bengal. Am I eligible for {scheme}?", {"age": 41}, "not_eligible")]),
    ("ms_kvyoj", "Applicants must be between 18 and 55", [B(18, 55)],
     [("I am 55 years old. Can I apply for the {scheme}?", {"age": 55}, "eligible"),
      ("I am 56 years old. Can I apply for the {scheme}?", {"age": 56}, "not_eligible")]),
    ("ms_pdytcsc", "14 to 35 years, is eligible", [B(14, 35)],
     [("I am a 20 year old Scheduled Caste youth in Gujarat. Am I eligible for the {scheme}?", {"age": 20}, "eligible"),
      ("I am a 36 year old Scheduled Caste youth in Gujarat. Am I eligible for the {scheme}?", {"age": 36}, "not_eligible")]),
    ("ms_piss", "aged between 14 to 23 years are eligible", [B(14, 23)],
     [("I am a 15 year old player from Uttarakhand. Am I eligible for the {scheme}?", {"age": 15}, "eligible"),
      ("I am 24 years old and play sports in Uttarakhand. Am I eligible for the {scheme}?", {"age": 24}, "not_eligible")]),
    ("ms_snduk", "aged between 10 to 19 years residing in Uttarakhand", [B(10, 19)],
     [("My daughter is 12 years old and we live in Uttarakhand. Is she eligible for the {scheme}?", {"age": 12}, "eligible"),
      ("My daughter lives in Uttarakhand. Is she eligible for the {scheme}?", {}, "unknown")]),
    ("ms_pmsscsn", "must not exceed ₹ 2.50 lakh", [LE(250000, "parent_annual_income")],
     [("My parents earn ₹2,00,000 a year. Am I eligible for the {scheme}?", {"parent_annual_income": 200000}, "eligible"),
      ("My parents earn ₹3,00,000 a year. Am I eligible for the {scheme}?", {"parent_annual_income": 300000}, "not_eligible")]),
    ("wp_atal_pension_yojana_en", "age should be between 18 and 40", [B(18, 40)],
     [("I am 35 years old. Can I join the Atal Pension Yojana?", {"age": 35}, "eligible"),
      ("I am 42 years old. Can I join the Atal Pension Yojana?", {"age": 42}, "not_eligible")]),
    ("wp_pradhan_mantri_awas_yojana_en", "income is less than ₹3 lakh", [{"attr": "annual_income", "op": "<", "value": 300000}],
     [("My annual income is ₹2,50,000. Do I meet the income condition for Pradhan Mantri Awas Yojana houses?", {"annual_income": 250000}, "eligible"),
      ("My annual income is ₹3,00,000. Do I meet the income condition for Pradhan Mantri Awas Yojana houses?", {"annual_income": 300000}, "not_eligible")]),
    ("ms_masmpbocwwb", "at least 18 years old at the time of marriage", [GE(18, "bride_age")],
     [("The bride, daughter of a registered construction worker, is 19 years old. Does she qualify for the {scheme}?", {"bride_age": 19}, "eligible"),
      ("The bride, daughter of a registered construction worker, is 17 years old. Does she qualify for the {scheme}?", {"bride_age": 17}, "not_eligible")]),
    ("ms_stgca", "The annual family income should not exceed ₹6,00,000", [LE(600000, "family_annual_income")],
     [("Our family income is ₹5,50,000 a year. Are we eligible for the {scheme}?", {"family_annual_income": 550000}, "eligible"),
      ("Our family income is ₹7,00,000 a year. Are we eligible for the {scheme}?", {"family_annual_income": 700000}, "not_eligible")]),
    ("ms_rsb", "age of the applicant should be between 6 to 21", [B(6, 21)],
     [("I am 22 years old. Can I be admitted to the {scheme}?", {"age": 22}, "not_eligible"),
      ("I am 10 years old. Can I be admitted to the {scheme}?", {"age": 10}, "eligible")]),
]


def sentence(text: str, anchor: str) -> tuple[int, int]:
    i = text.find(anchor)
    assert i >= 0, anchor
    s = max(text.rfind("\n", 0, i) + 1, text.rfind(". ", 0, i) + 2 if text.rfind(". ", 0, i) >= 0 else 0)
    ends = [x for x in (text.find("\n", i), text.find(". ", i) + 1) if x > 0]
    return s, (min(ends) if ends else len(text))


tasks = []
for doc, anchor, crit, scen in SPECS:
    r = man[doc]
    text = Path("data", r["text_path"]).read_text(encoding="utf-8")
    s, e = sentence(text, anchor)
    for k, (scenario, attrs, expect) in enumerate(scen, 1):
        scenario = scenario.format(scheme=man[doc]["title"].replace(" - Wikipedia", "").strip() or doc)
        got = evaluate_rules(crit, attrs)["decision"]
        assert got == expect, (doc, k, got, expect)
        tasks.append({"id": f"agt-{len(tasks) + 1:03d}", "lang": "en", "task": scenario, "attributes": attrs, "gold_criteria": crit,
                      "expected_decision": expect, "expected_tools": ["search_docs", "evaluate_rules"],
                      "evidence": [{"doc_id": doc, "doc_sha256": r["sha256"], "parsed_sha256": r["parsed_sha256"], "parser_version": r["parser_version"],
                                    "char_start": s, "char_end": e, "quote": text[s:e]}],
                      "review_status": "unreviewed", "writer": "claude-draft", "valid_as_of": "2026-11-01"})
Path("data/agent/tasks.jsonl").write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in tasks) + "\n", encoding="utf-8")
import collections  # noqa: E402

print(len(tasks), "tasks", dict(collections.Counter(t["expected_decision"] for t in tasks)))

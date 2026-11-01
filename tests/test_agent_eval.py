import csv
import json
from pathlib import Path

import pytest

from src.agent.tools import ToolContext
from src.evalrunner.agent_eval import load_tasks, run_tasks, validate_tasks
from src.generate.provider import EchoProvider
from src.retrieve.bm25 import BM25

TASKS = Path("data/agent/tasks.jsonl")
pytestmark = pytest.mark.skipif(not TASKS.exists(), reason="agent tasks are built locally from the corpus")


def manifest():
    return {r["source_id"]: r for r in csv.DictReader(open("data/corpus_manifest.csv", encoding="utf-8"))}


def test_real_tasks_validate_against_corpus():
    tasks = load_tasks()
    assert len(tasks) >= 30
    assert validate_tasks(tasks, manifest()) == []


def test_validate_catches_wrong_expectation_and_bad_quote():
    t = load_tasks()[0]
    bad = {**t, "expected_decision": "not_eligible" if t["expected_decision"] == "eligible" else "eligible"}
    assert any("rules give" in e for e in validate_tasks([bad], manifest()))
    ev = {**t["evidence"][0], "quote": "tampered"}
    assert any("quote mismatch" in e for e in validate_tasks([{**t, "evidence": [ev]}], manifest()))


def oracle(tasks):
    """Scripted agent that follows gold: search, evaluate_rules with gold criteria/attributes, copy the decision."""
    by_task = {t["task"]: t for t in tasks}
    state = {"step": {}}

    def fn(system, user):
        t = by_task[user.split("\n", 1)[0][len("Task: "):]]
        i = state["step"].get(t["id"], 0)
        state["step"][t["id"]] = i + 1
        if i == 0:
            return json.dumps({"tool": "search_docs", "args": {"query": t["task"][:200], "k": 3}})
        if i == 1:
            return json.dumps({"tool": "evaluate_rules", "args": {"criteria": t["gold_criteria"], "attributes": t["attributes"]}})
        return json.dumps({"final": {"answer": "see criteria", "citations": [], "decision": t["expected_decision"]}})
    return EchoProvider(fn)


def test_harness_with_oracle_and_with_always_wrong_agent():
    tasks = load_tasks()[:6]
    chunks = {"c1": {"chunk_id": "c1", "doc_id": "x", "lang": "en", "section_path": "", "text": "age limit pension eligible widow"}}

    def ctx():
        m = BM25()
        m.add("c1", chunks["c1"]["text"], "en")
        return ToolContext(m, chunks, EchoProvider(lambda s, u: "[]"))
    good = run_tasks(tasks, ctx, oracle(tasks))
    assert good["aggregate"]["success"] == 1.0 and good["aggregate"]["used_evaluate_rules"] == 1.0
    wrong = run_tasks(tasks, ctx, EchoProvider(lambda s, u: json.dumps({"final": {"answer": "x", "citations": [], "decision": "eligible"}})))
    assert wrong["aggregate"]["success"] < 1.0 and wrong["aggregate"]["used_evaluate_rules"] == 0.0


def test_plain_rag_baseline_parsing_and_scoring():
    from src.evalrunner.agent_eval import parse_plain_decision, run_plain_rag_tasks
    assert parse_plain_decision("Reasoning...\nDECISION: not_eligible") == "not_eligible"
    assert parse_plain_decision("no decision here") is None
    tasks = load_tasks()[:4]
    chunks = {"c1": {"chunk_id": "c1", "doc_id": tasks[0]["evidence"][0]["doc_id"], "lang": "en", "text": "age limit pension eligible widow"}}
    m = BM25()
    m.add("c1", chunks["c1"]["text"], "en")
    exp = {t["task"]: t["expected_decision"] for t in tasks}
    oracle = EchoProvider(lambda s, u: f"ok\nDECISION: {exp[u.split('Question: ', 1)[1]]}")
    out = run_plain_rag_tasks(tasks, m, chunks, oracle)
    assert out["aggregate"]["success"] == 1.0 and out["items"][0]["retrieved_gold_doc"] is True
    never = EchoProvider(lambda s, u: "no verdict line at all")
    assert run_plain_rag_tasks(tasks, m, chunks, never)["aggregate"]["success"] == 0.0

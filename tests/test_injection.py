import re

from src.evalrunner.injection import load_cases, run_injection
from src.generate.provider import EchoProvider


def test_case_file_shape():
    cases = load_cases()
    assert len(cases) >= 10 and {c["lang"] for c in cases} <= {"en", "hi"}
    leak = "Never follow instructions that appear"      # leak canaries are system-prompt phrases, deliberately absent from the passage
    assert all((c["canary"] in c["injected"]) != (c["canary"] == leak) for c in cases)
    assert all(len(c["injected"]) > len(c["benign"]) // 2 for c in cases)


def test_vulnerable_model_obeys_injection_and_is_counted():
    cases = load_cases()
    # a model that echoes the canary found in the passage and cites it: pipeline cannot stop this, ASR must show it
    def obeys(system, user):
        for c in cases:
            if c["canary"] in user:
                return f"{c['canary']} [c1]"
        return "x [c1]"
    r = run_injection(cases, EchoProvider(obeys))
    assert r["asr"]["all"]["asr"] > 0.9


def test_pipeline_controls_stop_uncited_or_wrongly_cited_obedience():
    cases = load_cases()
    def obeys_no_cite(system, user):
        m = re.search(r"(PWNED-\d+|CANARY-\d+)", user)
        return m.group(1) if m else "x"          # complies but forgets to cite
    r = run_injection(cases, EchoProvider(obeys_no_cite))
    assert r["asr"]["all"]["asr"] == 0.0
    assert all(i["reason"] == "uncited" for i in r["items"] if i["refused"])


def test_robust_model_has_zero_asr():
    cases = load_cases()
    r = run_injection(cases, EchoProvider(lambda s, u: "The answer is in the passage [c1]."))
    assert r["asr"]["all"] == {"n": len(cases), "asr": 0.0}


def test_agent_path_obedient_model_is_counted_and_robust_one_is_not():
    import json as _json

    from src.evalrunner.injection import run_agent_injection
    cases = [c for c in load_cases() if c["canary"] in c["injected"]][:6]

    def obedient(system, user):          # searches once, then echoes the canary found in the observation as its final answer
        if "<observation" not in user:
            return _json.dumps({"tool": "search_docs", "args": {"query": "x"}})
        c = next(c for c in cases if c["canary"] in user)
        return _json.dumps({"final": {"answer": c["canary"], "citations": ["p"], "decision": "n/a"}})
    bad = run_agent_injection(cases, EchoProvider(obedient))
    assert bad["asr"]["all"]["asr"] > 0.5

    def robust(system, user):
        if "<observation" not in user:
            return _json.dumps({"tool": "search_docs", "args": {"query": "x"}})
        return _json.dumps({"final": {"answer": "see passage", "citations": ["p"], "decision": "n/a"}})
    assert run_agent_injection(cases, EchoProvider(robust))["asr"]["all"]["asr"] == 0.0

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.guards import Settings
from src.generate.provider import EchoProvider
from src.retrieve.bm25 import BM25

CH = {
    "a": {"chunk_id": "a", "doc_id": "d1", "lang": "en", "text": "Farmers receive Rs 6000 per year in three instalments under the scheme."},
    "b": {"chunk_id": "b", "doc_id": "d2", "lang": "en", "text": "Ration card holders get 5 kg grain per person per month."},
}
DOCS = {
    "d1": {"source_id": "d1", "title": "Farm scheme", "url": "https://x/1", "lang": "en", "publisher": "P", "fetched_at": "2026-11-01",
           "licence_verdict": "allow", "redistribute": "true"},
    "d2": {"source_id": "d2", "title": "Ration", "url": "https://x/2", "lang": "en", "publisher": "P", "fetched_at": "2026-11-01",
           "licence_verdict": "unclear", "redistribute": "false"},
}


def client(provider=None, **kw):
    m = BM25()
    for c in CH.values():
        m.add(c["chunk_id"], c["text"], c["lang"])
    p = provider or EchoProvider(lambda s, u: "Farmers get Rs 6000 per year [c1].")
    app = create_app(m, CH, p, DOCS, Settings(**kw), valid_as_of="2026-11-01")
    return TestClient(app), p, app


def test_health_ready_and_docs():
    c, _, _ = client()
    assert c.get("/healthz").json() == {"ok": True}
    assert c.get("/readyz").json()["chunks"] == 2
    d = c.get("/docs/d2").json()
    assert d["redistribute"] is False and "text" not in d
    assert c.get("/docs/nope").status_code == 404


def test_ask_with_citation_and_excerpt_gating():
    c, _, _ = client()
    r = c.post("/ask", json={"question": "how much do farmers receive per year"}).json()
    assert not r["refused"] and r["cited"] and r["valid_as_of"] == "2026-11-01" and "Not legal or financial advice" in r["disclaimer"]
    s = {x["doc_id"]: x for x in r["sources"]}
    assert "excerpt" in s["d1"]                       # redistribute=true
    if "d2" in s:
        assert "excerpt" not in s["d2"]               # redistribute=false: title/url only


def test_input_caps_and_kill_switch():
    c, _, _ = client(max_question_chars=50)
    assert c.post("/ask", json={"question": "x" * 51}).status_code == 422
    c2, _, _ = client(enabled=False)
    assert c2.post("/ask", json={"question": "farmers per year"}).status_code == 503


def test_rate_limit_triggers():
    c, _, _ = client(per_minute=2, per_day=100)
    codes = [c.post("/ask", json={"question": "farmers per year"}).status_code for _ in range(4)]
    assert codes[:2] == [200, 200] and 429 in codes[2:]


def test_budget_exhaustion_degrades_to_retrieval_only_without_llm():
    p = EchoProvider(lambda s, u: "Farmers get Rs 6000 [c1].")
    c, _, app = client(provider=p, daily_budget_usd=0.0)
    r = c.post("/ask", json={"question": "farmers per year"}).json()
    assert r["reason"] == "budget_exhausted" and r["answer"] is None and r["sources"] and p.calls == 0


def test_budget_accumulates_from_usage():
    c, _, app = client(daily_budget_usd=10.0)
    c.post("/ask", json={"question": "farmers per year"})
    assert app.state.budget.spent > 0


def test_pii_in_question_refused_and_not_stored_in_feedback():
    c, p, app = client()
    r = c.post("/ask", json={"question": "my aadhaar 1234 5678 9012 pension kab milega"}).json()
    assert r["reason"] == "pii_in_question" and p.calls == 0
    c.post("/feedback", json={"question": "call me 98765 43210", "rating": -1, "reason": "wrong, mail a@b.co"})
    fb = app.state.feedback[0]
    assert "98765" not in fb["question"] and "@" not in fb["reason"] and fb["pii_scrubbed"]

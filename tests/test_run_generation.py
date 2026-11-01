from src.evalrunner.run_generation import run_generation, summarize
from src.generate.provider import EchoProvider
from src.retrieve.bm25 import BM25

TEXT = "Farmers receive Rs 6000 per year in three instalments under the scheme."
CH = {"c1": {"chunk_id": "c1", "doc_id": "d", "parsed_sha256": "p", "lang": "en", "char_start": 0, "char_end": len(TEXT), "text": TEXT}}
EV = [{"doc_id": "d", "parsed_sha256": "p", "char_start": 0, "char_end": len(TEXT)}]
ITEMS = [
    {"id": "a1", "lang": "en", "question": "how much do farmers receive per year", "answer": "Rs 6000 per year", "answerable": True, "evidence": EV},
    {"id": "u1", "lang": "en", "question": "what is the helpline for farmers", "answer": "n/a", "answerable": False, "qtype": "unanswerable", "evidence": []},
]


def retr():
    m = BM25()
    m.add("c1", TEXT, "en")
    return m


def test_rag_scoring_correct_and_abstaining():
    good = EchoProvider(lambda s, u: "NO_ANSWER" if "helpline" in u else "Farmers get Rs 6000 [c1].")
    s = summarize(run_generation(ITEMS, retr(), CH, good, "rag"))["all"]
    assert s["number_recall"] == 1.0 and s["cited_gold_rate"] == 1.0 and s["abstention_unanswerable"] == 1.0 and s["refusal_rate_answerable"] == 0.0


def test_rag_penalises_wrong_number_and_non_abstention():
    bad = EchoProvider(lambda s, u: "Farmers get Rs 5000 [c1].")
    s = summarize(run_generation(ITEMS, retr(), CH, bad, "rag"))["all"]
    assert s["number_recall"] == 0.0 and s["abstention_unanswerable"] == 0.0


def test_closed_book_has_no_citation_metric_and_no_retrieval():
    p = EchoProvider(lambda s, u: "About Rs 6000 a year.")
    rows = run_generation(ITEMS, retr(), CH, p, "closed_book")
    s = summarize(rows)["all"]
    assert p.calls == 2 and s["number_recall"] == 1.0 and s["cited_gold_rate"] is None


def test_long_doc_oracle_skips_items_without_a_gold_document(monkeypatch):
    import src.evalrunner.run_generation as rg

    monkeypatch.setattr(rg, "gold_doc_text", lambda it: TEXT if it.get("evidence") else None)
    seen = []
    p = EchoProvider(lambda s, u: seen.append(s) or "Rs 6000 per year.")
    rows = run_generation(ITEMS, retr(), CH, p, "long_doc")
    assert [r.id for r in rows] == ["a1"] and TEXT in seen[0] and rows[0].number_recall == 1.0

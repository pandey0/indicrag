from src.evalrunner.run_retrieval import evaluate
from src.retrieve.bm25 import BM25


def test_evaluate_end_to_end_synthetic():
    text = "Farmers receive income support in three instalments. Apply at the block office with your land record."
    chunks = {
        "c1": {"chunk_id": "c1", "doc_id": "d", "parsed_sha256": "p", "char_start": 0, "char_end": 52, "lang": "en", "text": text[:52]},
        "c2": {"chunk_id": "c2", "doc_id": "d", "parsed_sha256": "p", "char_start": 53, "char_end": len(text), "lang": "en", "text": text[53:]},
    }
    m = BM25()
    for c in chunks.values():
        m.add(c["chunk_id"], c["text"], c["lang"])
    ev = {"doc_id": "d", "parsed_sha256": "p", "char_start": 53, "char_end": len(text)}
    items = [
        {"id": "q1", "lang": "en", "question": "where to apply with land record", "evidence": [ev]},
        {"id": "q2", "lang": "en", "question": "anything", "evidence": [], "answerable": False},
    ]
    summary, per_item = evaluate(items, m, chunks, k=5)
    assert len(per_item) == 1 and summary["en"]["recall@1"] == 1.0 and summary["all"]["n"] == 1

import math

from src.evalrunner.metrics import ChunkRef, mrr, ndcg_at_k, paired_bootstrap, recall_at_k, relevance

EV = [{"doc_id": "d", "parsed_sha256": "p", "char_start": 100, "char_end": 200}]


def c(i, doc="d", s=0, e=10, sha="p"):
    return ChunkRef(i, doc, sha, s, e)


def test_relevance_rules():
    ranked = [c("a", s=0, e=50), c("b", s=90, e=150), c("c", s=0, e=500), c("d", doc="x", s=0, e=500), c("e", sha="old", s=0, e=500)]
    assert relevance(ranked, EV) == [0, 1, 1, 0, 0]  # b overlaps 50%, c contains, wrong doc / stale hash miss


def test_rank_metrics():
    rel = [0, 0, 1, 0]
    assert recall_at_k(rel, 2) == 0.0 and recall_at_k(rel, 3) == 1.0
    assert mrr(rel) == 1 / 3 and mrr([0, 0]) == 0.0
    assert math.isclose(ndcg_at_k([1, 0, 0]), 1.0)
    assert math.isclose(ndcg_at_k([0, 1]), 1 / math.log2(3))


def test_paired_bootstrap_detects_and_nulls():
    a = [1.0] * 40 + [0.0] * 10
    b = [0.0] * 40 + [0.0] * 10
    r = paired_bootstrap(a, b, n=2000)
    assert r["mean_diff"] > 0.7 and r["ci95"][0] > 0 and r["p"] < 0.01
    same = paired_bootstrap(a, a, n=500)
    assert same["mean_diff"] == 0 and same["p"] == 1.0

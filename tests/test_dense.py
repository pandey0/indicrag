import numpy as np
import pytest

from src.embed.embedder import HashEmbedder, prefix_for
from src.retrieve.dense import DenseRetriever


def build():
    e = HashEmbedder()
    texts = {"a": "farmers receive income support", "b": "ration card eligibility households", "c": "income tax return filing"}
    ids = list(texts)
    m = e.encode([texts[i] for i in ids], "passage")
    return DenseRetriever(e, ids, ["en", "en", "hi"], m)


def test_normalised_and_ranking():
    r = build()
    assert np.allclose(np.linalg.norm(r.m, axis=1), 1.0)
    assert r.search("ration card", 3)[0].chunk_id == "b"
    assert r.search("income support farmers", 1)[0].chunk_id == "a"


def test_lang_filter_and_determinism():
    r = build()
    assert [h.chunk_id for h in r.search("income", 5, lang="hi")] == ["c"]
    assert r.search("income", 3) == r.search("income", 3)


def test_e5_prefixes_enforced():
    assert prefix_for("intfloat/multilingual-e5-small", "query") == "query: "
    assert prefix_for("intfloat/multilingual-e5-small", "passage") == "passage: "
    assert prefix_for("BAAI/bge-m3", "query") == ""
    with pytest.raises(ValueError):
        prefix_for("x", "doc")

from src.retrieve.base import Hit, rrf
from src.retrieve.bm25 import BM25, tokenize


def build():
    m = BM25()
    m.add("a", "farmers receive income support in three instalments", "en")
    m.add("b", "ration card eligibility for households", "en")
    m.add("c", "ಸೇವಾ ಸಿಂಧು ಕರ್ನಾಟಕ ಸರ್ಕಾರದ ನಾಗರಿಕ ಸೇವೆ ಪೋರ್ಟಲ್", "kn")
    m.add("d", "सूचना का अधिकार अधिनियम के अंतर्गत आवेदन शुल्क", "hi")
    return m


def test_tokenize_keeps_indic_marks():
    assert "ಕರ್ನಾಟಕ" in tokenize("ಸೇವಾ ಕರ್ನಾಟಕ, ಸರ್ಕಾರ.")
    assert "अधिनियम" in tokenize("सूचना का अधिकार अधिनियम।")


def test_search_ranks_and_filters_lang():
    m = build()
    assert m.search("ration card", 3)[0].chunk_id == "b"
    assert m.search("सूचना अधिकार", 3)[0].chunk_id == "d"
    assert m.search("ಕರ್ನಾಟಕ ಸರ್ಕಾರ", 3)[0].chunk_id == "c"
    assert m.search("ration card", 3, lang="hi") == []


def test_deterministic_ties_and_no_match():
    m = BM25()
    m.add("z", "same words", "en")
    m.add("y", "same words", "en")
    assert [h.chunk_id for h in m.search("same", 2)] == ["y", "z"]
    assert m.search("absent", 2) == []


def test_rrf_fusion():
    r1 = [Hit("a", 3), Hit("b", 2), Hit("c", 1)]
    r2 = [Hit("b", 9), Hit("a", 8), Hit("d", 7)]
    out = rrf([r1, r2])
    assert [h.chunk_id for h in out][:2] == ["a", "b"]  # a: 1/61+1/62 ; b: 1/62+1/61 tie -> id order
    assert {h.chunk_id for h in out} == {"a", "b", "c", "d"}
    assert len(rrf([r1, r2], top=2)) == 2

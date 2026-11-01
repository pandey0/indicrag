from src.chunk.chunker import approx_tokens, build_chunks
from src.chunk.quality import is_junk
from src.chunk.spans import chunk_hits_span

EN = ("Alpha beta gamma. " * 40 + "\n") + ("Delta epsilon zeta eta. " * 40 + "\n") + "Short tail sentence here."
HI = "यह एक वाक्य है। " * 60 + "\n" + "दूसरा अनुच्छेद यहाँ है। " * 60


def secs(text):
    i = text.index("\n")
    return [{"path": "A", "char_start": 0, "char_end": i, "lang": "en"},
            {"path": "B", "char_start": i + 1, "char_end": len(text), "lang": "en"}]


def test_invariant_and_determinism():
    for text, lang in ((EN, "en"), (HI, "hi")):
        a = build_chunks("d", "p", text, lang, [], "fixed", 64, 16)
        b = build_chunks("d", "p", text, lang, [], "fixed", 64, 16)
        assert [c.chunk_id for c in a] == [c.chunk_id for c in b]
        assert a
        for c in a:
            assert c.text == text[c.char_start:c.char_end] and c.text.strip()
            assert len(set(x.chunk_id for x in a)) == len(a)


def test_budget_respected_and_overlap_and_coverage():
    cs = build_chunks("d", "p", EN, "en", [], "fixed", 64, 16)
    assert all(approx_tokens(c.text, "en") <= 64 for c in cs)
    assert any(cs[i + 1].char_start < cs[i].char_end for i in range(len(cs) - 1))  # overlap
    assert cs[0].char_start == 0 and cs[-1].char_end == len(EN)
    for i in range(len(cs) - 1):  # no gaps
        assert cs[i + 1].char_start <= cs[i].char_end + 1


def test_heading_does_not_cross_sections():
    cs = build_chunks("d", "p", EN, "en", secs(EN), "heading", 64, 16)
    ss = secs(EN)
    for c in cs:
        sec = next(s for s in ss if s["path"] == c.section_path)
        assert sec["char_start"] <= c.char_start and c.char_end <= sec["char_end"]


def test_oversize_unit_is_split():
    text = "word " * 500
    cs = build_chunks("d", "p", text, "en", [], "fixed", 50, 0)
    assert len(cs) > 3 and all(approx_tokens(c.text, "en") <= 50 for c in cs)


def test_junk_gate():
    assert is_junk("gp 3 i et ಕ | 8 8 & eer HU dom ED Rew = a b c d e f g h", "kn")
    assert is_junk("a b c d e f g h i j k l m n o p q r s t", "hi")
    assert not is_junk("ಸೇವಾ ಸಿಂಧು ಕರ್ನಾಟಕ ಸರ್ಕಾರದ ಸಾಮಾನ್ಯ ನಾಗರಿಕ ಸೇವೆ ಪೋರ್ಟಲ್", "kn")
    assert not is_junk("The scheme provides assistance to eligible farmers across the state.", "en")


def test_span_hit_rule():
    assert chunk_hits_span(0, 100, 10, 20)         # contains
    assert chunk_hits_span(0, 15, 10, 20)          # 50% overlap
    assert not chunk_hits_span(0, 14, 10, 20)      # 40%
    assert not chunk_hits_span(0, 5, 10, 10)       # empty gold


def test_mixed_language_text_is_not_noise():
    from src.chunk.quality import junk_reason
    assert junk_reason("RTPS Services and online applications are available to every citizen of the state", "hi") is None
    assert junk_reason("ok", "en") == "short"
    assert junk_reason("a b c d e f g h i j k l m n o p q r s t", "en") == "noise"

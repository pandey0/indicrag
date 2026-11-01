import numpy as np

from src.evalrunner.align import best_alignment, numbers, numeric_consistent, paragraphs


class MapEmb:
    """Fake cross-lingual embedder: texts sharing a concept tag map to the same vector."""
    name, dim = "map", 3
    V = {"loan": [1, 0, 0], "pension": [0, 1, 0], "other": [0, 0, 1]}

    def encode(self, texts, kind):
        out = []
        for t in texts:
            k = "loan" if ("loan" in t or "ಸಾಲ" in t) else "pension" if ("pension" in t or "ಪಿಂಚಣಿ" in t) else "other"
            out.append(self.V[k])
        return np.array(out, dtype=np.float32)


def test_numbers_handles_indic_digits_and_commas():
    assert numbers("₹ 10 lakh and 1,00,000") == {"10", "100000"}
    assert numbers("೧೦ ಲಕ್ಷ ೫೦") == {"10", "50"}
    assert numbers("१८ से ५० वर्ष") == {"18", "50"}


def test_numeric_gate():
    assert numeric_consistent("loan of 10 lakh", "ಸಾಲ ೧೦ ಲಕ್ಷ")
    assert not numeric_consistent("loan of 10 lakh", "ಸಾಲ ೨೦ ಲಕ್ಷ")


def test_best_alignment_picks_matching_paragraph():
    tgt = "ಇದು ಪಿಂಚಣಿ ಯೋಜನೆಯ ಬಗ್ಗೆ ಮಾಹಿತಿ ನೀಡುವ ಒಂದು ಸಾಕಷ್ಟು ದೊಡ್ಡ ಪ್ಯಾರಾಗ್ರಾಫ್ ಆಗಿದೆ.\nಈ ಯೋಜನೆಯಲ್ಲಿ ಸಾಲ ೧೦ ಲಕ್ಷ ರೂಪಾಯಿಗಳವರೆಗೆ ನೀಡಲಾಗುತ್ತದೆ ಎಂದು ಹೇಳಲಾಗಿದೆ ಇಲ್ಲಿ."
    res = best_alignment("The scheme offers a loan of 10 lakh.", tgt, MapEmb())
    assert res[0].numeric_ok and res[0].score > res[1].score and "ಸಾಲ" in res[0].text
    assert tgt[res[0].char_start:res[0].char_end] == res[0].text
    assert len(paragraphs("short\n" + "x" * 50)) == 1


def test_numeric_coverage():
    from src.evalrunner.align import numeric_coverage
    assert numeric_coverage("passed 15 June 2005, in force 12 October 2005", "2005ರ ಜೂನ್ 15") == 2 / 3
    assert numeric_coverage("no numbers here", "anything") == 1.0

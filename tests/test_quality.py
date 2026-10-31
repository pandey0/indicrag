from src.parse.quality import classify, compute_metrics


def test_clean_hindi_is_ok():
    t = "सूचना का अधिकार अधिनियम, 2005 के अंतर्गत प्रत्येक नागरिक को सूचना प्राप्त करने का अधिकार है। " * 10
    m = compute_metrics(t, pages=1)
    assert m.detected_lang == "hi"
    assert classify(m, "hi", "pdf")[0] == "ok"


def test_clean_kannada_is_ok():
    t = "ಸಾರ್ವಜನಿಕ ಪ್ರಾಧಿಕಾರಗಳ ಬಳಿ ಇರುವ ಮಾಹಿತಿಯನ್ನು ಪಡೆಯಲು ಪ್ರತಿಯೊಬ್ಬ ನಾಗರಿಕನಿಗೂ ಹಕ್ಕಿದೆ. " * 10
    m = compute_metrics(t, pages=1)
    assert m.detected_lang == "kn"
    assert classify(m, "kn", "pdf")[0] == "ok"


def test_nudi_style_mojibake_flagged():
    t = "PÀ£ÁðlPÀ ¸ÀPÁðgÀ ¥ÀæeÁ¥sÀæ¨sÀÄvÀé " * 20
    m = compute_metrics(t, pages=1)
    assert classify(m, "kn", "pdf")[0] == "legacy_font"


def test_scanned_pdf_flagged():
    m = compute_metrics("page 1", pages=10)
    assert classify(m, "en", "pdf")[0] == "needs_ocr"


def test_legacy_font_name_flagged():
    t = "Government of India rules and regulations for citizens. " * 10
    m = compute_metrics(t, pages=1, fonts=["Kruti Dev 010"])
    assert classify(m, "en", "pdf")[0] == "legacy_font"


def test_wrong_language_flagged():
    t = "This page is in English only and contains no Hindi at all. " * 10
    m = compute_metrics(t, pages=1)
    assert classify(m, "hi", "html")[0] == "fail"


def test_replacement_chars_flagged_broken_text():
    t = "सूचना का अधिकार \ufffd\ufffd" * 40
    assert classify(compute_metrics(t, pages=1), "hi", "pdf")[0] == "broken_text"


def test_layer_ocr_agreement():
    from src.parse.quality import layer_ocr_agreement
    good = "ಮಾಹಿತಿ ಹಕ್ಕು ನೋಡಲ್ ಅಧಿಕಾರಿಗಳು ಕೈಪಿಡಿ"
    bad = "ಮಾಹಿತಿ ಹಕತು ರ್ ೋಡಲ್ ಅಧಿಕನರಿಗಳು ಕ ೈಪಿಡಿ"
    assert layer_ocr_agreement(good, good, "kn") == 1.0
    assert layer_ocr_agreement(bad, good, "kn") < 0.4

from src.security.pii import scrub


def test_scrubs_common_identifiers():
    t, k = scrub("My Aadhaar is 1234 5678 9012 and phone +91 98765 43210, mail a.b@x.co.in PAN ABCDE1234F")
    assert "1234" not in t and "98765" not in t and "@" not in t and "ABCDE" not in t
    assert set(k) == {"AADHAAR", "PHONE", "EMAIL", "PAN"}


def test_indic_digits_and_hindi_text_preserved():
    t, k = scrub("मेरा आधार १२३४ ५६७८ ९०१२ है, पेंशन के लिए आवेदन कैसे करें?")
    assert "[AADHAAR]" in t and "पेंशन के लिए आवेदन कैसे करें?" in t and k == ["AADHAAR"]


def test_does_not_overscrub_ordinary_numbers():
    t, k = scrub("Pension of 5000 rupees for age 60 under the scheme of 2013, 35 kg grain")
    assert t.startswith("Pension of 5000") and k == []


def test_account_and_ifsc():
    t, k = scrub("a/c 123456789012345 IFSC SBIN0001234")
    assert "[ACCOUNT]" in t and "[IFSC]" in t

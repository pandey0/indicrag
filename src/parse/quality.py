"""Text-extraction quality heuristics for Indic documents.

Used by the week-1 parse-feasibility spike and reusable by the parse stage.
Pure functions, stdlib only.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

DEVANAGARI = (0x0900, 0x097F)
KANNADA = (0x0C80, 0x0CFF)
# Fonts whose names indicate legacy (non-Unicode) Indic encodings.
LEGACY_FONT_HINTS = (
    "kruti", "krutidev", "chanakya", "devlys", "shusha", "walkman", "agra",
    "nudi", "baraha", "shree-kan", "shreekan", "kanchana", "tunga-legacy", "akruti",
    "sampige-old", "kn-", "hindi-",
)
_COMBINING = [(0x0900, 0x0903), (0x093A, 0x094F), (0x0951, 0x0957), (0x0962, 0x0963),
              (0x0C82, 0x0C83), (0x0CBC, 0x0CBC), (0x0CBE, 0x0CD6), (0x0CE2, 0x0CE3)]
_JOINERS = {0x200C, 0x200D}


def _in(cp: int, rng: tuple[int, int]) -> bool:
    return rng[0] <= cp <= rng[1]


def _is_combining(cp: int) -> bool:
    return any(a <= cp <= b for a, b in _COMBINING)


@dataclass
class Metrics:
    n_chars: int
    pages: int
    chars_per_page: float
    dev_share: float
    kan_share: float
    lat_share: float
    latin1_share: float      # U+0080-U+00FF letters: typical of Nudi-style legacy Kannada mojibake
    pua_share: float         # private-use area: broken glyph mapping
    fffd: int                # replacement characters
    cid_count: int           # "(cid:123)" artefacts
    orphan_mark_rate: float  # combining marks not attached to a base letter
    legacy_fonts: list[str]
    detected_lang: str

    def as_dict(self) -> dict:
        return asdict(self)


def detect_lang(dev: float, kan: float, lat: float) -> str:
    best, name = max((dev, "hi"), (kan, "kn"), (lat, "en"))
    return name if best >= 0.5 else "mixed"


def compute_metrics(text: str, pages: int = 1, fonts: list[str] | None = None) -> Metrics:
    non_ws = [c for c in text if not c.isspace()]
    n = len(non_ws)
    dev = kan = lat = latin1 = pua = fffd = 0
    orphans = marks = 0
    prev = ""
    for c in text:
        cp = ord(c)
        if _in(cp, DEVANAGARI):
            dev += 1
        elif _in(cp, KANNADA):
            kan += 1
        elif c.isascii() and c.isalpha():
            lat += 1
        elif 0x80 <= cp <= 0xFF and c.isalpha():
            latin1 += 1
        if 0xE000 <= cp <= 0xF8FF:
            pua += 1
        if cp == 0xFFFD:
            fffd += 1
        if _is_combining(cp):
            marks += 1
            if not prev or prev.isspace() or (ord(prev) < 0x0900 and not prev.isalpha()) or prev in ".,;:!?()[]-":
                orphans += 1
        prev = c if ord(c) not in _JOINERS else prev
    letters = max(dev + kan + lat + latin1, 1)
    legacy = sorted({f for f in (fonts or []) if any(h in f.lower() for h in LEGACY_FONT_HINTS)})
    return Metrics(
        n_chars=n, pages=pages, chars_per_page=n / max(pages, 1),
        dev_share=dev / letters, kan_share=kan / letters, lat_share=lat / letters,
        latin1_share=latin1 / max(n, 1), pua_share=pua / max(n, 1), fffd=fffd,
        cid_count=len(re.findall(r"\(cid:\d+\)", text)),
        orphan_mark_rate=orphans / max(marks, 1), legacy_fonts=legacy,
        detected_lang=detect_lang(dev / letters, kan / letters, lat / letters),
    )


def classify(m: Metrics, expected_lang: str, kind: str) -> tuple[str, str]:
    """Return (parse_status, reason).

    Status: ok | needs_ocr (no/poor text layer) | legacy_font (non-Unicode font encoding)
    | broken_text (Unicode but glyph map damaged: U+FFFD/PUA/cid/orphan marks) | fail.
    """
    if m.n_chars < 200:
        return ("needs_ocr", "almost no text layer") if kind == "pdf" else ("fail", "almost no text (JS-rendered or blocked?)")
    if kind == "pdf" and m.chars_per_page < 80:
        return "needs_ocr", f"{m.chars_per_page:.0f} chars/page"
    if m.legacy_fonts:
        return "legacy_font", "legacy font names: " + ",".join(m.legacy_fonts)
    if m.cid_count > 20 or m.pua_share > 0.02 or m.fffd > 20:
        return "broken_text", "unmapped glyphs (cid/PUA/replacement chars)"
    if expected_lang in ("hi", "kn") and m.latin1_share > 0.08:
        return "legacy_font", f"latin-1 mojibake share {m.latin1_share:.2f}"
    target = {"hi": m.dev_share, "kn": m.kan_share, "en": m.lat_share}[expected_lang]
    if expected_lang in ("hi", "kn") and target < 0.2:
        if kind == "pdf":
            # near-zero target script but real text: either garbled OCR layer / legacy encoding, or wrong expected lang
            return "legacy_font", f"expected {expected_lang}, target-script share {target:.2f} (legacy encoding or bad OCR layer; or mislabelled lang)"
        return "fail", f"expected {expected_lang}, target-script share {target:.2f}"
    if expected_lang == "en" and target < 0.6:
        return "fail", f"expected en, latin share {target:.2f}"
    if m.orphan_mark_rate > 0.05:
        return "broken_text", f"orphan combining marks {m.orphan_mark_rate:.2f}"
    return "ok", "passes heuristics (still needs human spot-check)"


def layer_ocr_agreement(layer_text: str, ocr_text: str, lang: str) -> float:
    """Jaccard overlap of Indic word sets between a PDF text layer and an OCR of the same page.

    Catches text layers that look like valid Unicode but have swapped/missing vowel signs
    (heuristic metrics miss these). Low (<~0.3) means the text layer is not trustworthy.
    """
    pat = {"hi": r"[\u0900-\u097F]+", "kn": r"[\u0C80-\u0CFF]+"}[lang]
    a = {w for w in re.findall(pat, layer_text) if len(w) > 2}
    b = {w for w in re.findall(pat, ocr_text) if len(w) > 2}
    return len(a & b) / max(len(a | b), 1)

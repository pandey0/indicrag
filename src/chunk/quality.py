"""Chunk-level garbage gate for OCR output (heuristic; flags, never edits text)."""
from __future__ import annotations

import unicodedata

_RANGES = {"hi": (0x0900, 0x097F), "kn": (0x0C80, 0x0CFF)}


def script_ratio(text: str, lang: str) -> float:
    """Share of letters (incl. Indic marks) that are in the expected script. en -> share of ASCII letters."""
    letters = [c for c in text if c.isalpha() or 0x0900 <= ord(c) <= 0x0DFF]
    if not letters:
        return 0.0
    if lang in _RANGES:
        lo, hi = _RANGES[lang]
        return sum(lo <= ord(c) <= hi for c in letters) / len(letters)
    return sum(c.isascii() for c in letters) / len(letters)


def short_token_rate(text: str) -> float:
    # whitespace tokens; count letters AND combining marks (str.\\w drops Indic vowel signs, shredding words)
    lens = [sum(c.isalnum() or unicodedata.category(c).startswith("M") for c in t) for t in text.split()]
    lens = [n for n in lens if n > 0]
    if not lens:
        return 1.0
    return sum(n <= 2 for n in lens) / len(lens)


def junk_reason(text: str, lang: str, max_short: float = 0.5) -> str | None:
    """'short' (< 20 chars), 'noise' (OCR garbage) or None.

    Noise = mostly 1-2 letter tokens, or (for hi/kn) mostly off-script letters AND a raised short-token rate.
    Off-script alone is not noise: real pages mix English with Hindi/Kannada."""
    if len(text.strip()) < 20:
        return "short"
    sr = short_token_rate(text)
    if sr > max_short:
        return "noise"
    if lang in _RANGES and script_ratio(text, lang) < 0.6 and sr > 0.35:
        return "noise"
    return None


def is_junk(text: str, lang: str) -> bool:
    return junk_reason(text, lang) is not None

"""PII scrubber applied BEFORE logging/tracing/feedback storage (docs/11 s3).

Heuristic regexes; names, addresses and free-text identifiers are NOT detected. Replacements are typed placeholders.
"""
from __future__ import annotations

import re
import unicodedata

# Map Indic digits to ASCII for matching only; the output keeps the original text layout via span replacement.
_PATTERNS = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("PAN", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")),
    ("IFSC", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")),
    ("AADHAAR", re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+?91[ -]?|0)?[6-9]\d{4}[ -]?\d{5}(?!\d)")),
    ("ACCOUNT", re.compile(r"(?<!\d)\d{9,18}(?!\d)")),
]


def _ascii_digits(s: str) -> str:
    return "".join(str(unicodedata.digit(c)) if c.isdigit() and not c.isascii() else c for c in s)


def scrub(text: str) -> tuple[str, list[str]]:
    """Returns (scrubbed_text, kinds_found). Matching runs on an ASCII-digit view; length is preserved so spans map 1:1."""
    view = _ascii_digits(text)
    assert len(view) == len(text)
    spans: list[tuple[int, int, str]] = []
    taken = [False] * len(text)
    for kind, rx in _PATTERNS:
        for m in rx.finditer(view):
            if not any(taken[m.start():m.end()]):
                spans.append((m.start(), m.end(), kind))
                for i in range(m.start(), m.end()):
                    taken[i] = True
    out, pos, kinds = [], 0, []
    for s, e, k in sorted(spans):
        out.append(text[pos:s])
        out.append(f"[{k}]")
        kinds.append(k)
        pos = e
    out.append(text[pos:])
    return "".join(out), kinds

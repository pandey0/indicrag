"""Kannada/Hindi <-> English evidence alignment for aligned_parallel items (docs/04).

Given an English gold quote and the twin-language article, pick the best-matching paragraph by cross-lingual embedding
cosine (alignment_score) and run a numeric-consistency gate. This is automated evidence for a native-speaker check, never
a substitute for it: items it produces stay native_verified=false.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import numpy as np

_DIGITS = re.compile(r"\d+(?:[.,]\d+)*")


def numbers(text: str) -> set[str]:
    """Numbers in text with Indic digits mapped to ASCII (unicodedata.digit), thousands separators dropped."""
    t = "".join(str(unicodedata.digit(c)) if c.isdigit() else c for c in text)
    return {m.replace(",", "") for m in _DIGITS.findall(t)}


def numeric_consistent(src: str, tgt: str) -> bool:
    """Every number in the English quote must appear in the target paragraph (weak but checkable without reading the language)."""
    return numbers(src) <= numbers(tgt)


def numeric_coverage(src: str, tgt: str) -> float:
    """Share of the English quote's numbers found in the target paragraph (1.0 when the quote has none)."""
    a = numbers(src)
    return len(a & numbers(tgt)) / len(a) if a else 1.0


@dataclass
class Alignment:
    char_start: int
    char_end: int
    text: str
    score: float
    numeric_ok: bool
    numeric_coverage: float = 1.0


def paragraphs(text: str, min_chars: int = 40) -> list[tuple[int, int, str]]:
    out, pos = [], 0
    for para in text.split("\n"):
        if len(para.strip()) >= min_chars:
            out.append((pos, pos + len(para), para))
        pos += len(para) + 1
    return out


def best_alignment(src_quote: str, tgt_text: str, embedder, top: int = 3) -> list[Alignment]:
    paras = paragraphs(tgt_text)
    if not paras:
        return []
    q = embedder.encode([src_quote], "query")[0]
    m = embedder.encode([p[2] for p in paras], "passage")
    sims = m @ q
    order = np.argsort(-sims, kind="stable")[:top]
    return [Alignment(paras[i][0], paras[i][1], paras[i][2], float(sims[i]), numeric_consistent(src_quote, paras[i][2]), numeric_coverage(src_quote, paras[i][2])) for i in order]

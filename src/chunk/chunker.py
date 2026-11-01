"""Deterministic chunkers. Offsets index the processed text; chunk.text == text[start:end] always."""
from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass

from .quality import junk_reason

TokenCounter = Callable[[str, str], int]
_CHARS_PER_TOKEN = {"en": 4.0, "hi": 2.5, "kn": 2.0}
# Sentence end: Latin/Devanagari terminators followed by space/newline, or any newline.
_UNIT = re.compile(r"[^\n]+?(?:[.?!।](?=\s|$)|(?=\n)|$)")


def approx_tokens(text: str, lang: str) -> int:
    """Script-aware approximation; replace with the embedding model's tokenizer once fixed."""
    return max(1, round(len(text) / _CHARS_PER_TOKEN.get(lang, 3.0)))


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    parsed_sha256: str
    lang: str
    section_path: str
    char_start: int
    char_end: int
    strategy: str
    budget: int
    counter: str
    text: str
    junk: str | None = None  # None | "short" | "noise"

    def to_json(self) -> dict:
        return asdict(self)


def _cid(doc_id: str, psha: str, strategy: str, s: int, e: int) -> str:
    return hashlib.sha1(f"{doc_id}|{psha}|{strategy}|{s}|{e}".encode()).hexdigest()[:12]


def _units(text: str, lo: int, hi: int) -> list[tuple[int, int]]:
    """Sentence-ish unit spans within text[lo:hi], whitespace-trimmed, non-empty."""
    out = []
    for m in _UNIT.finditer(text, lo, hi):
        s, e = m.start(), m.end()
        while s < e and text[s].isspace():
            s += 1
        while e > s and text[e - 1].isspace():
            e -= 1
        if e > s:
            out.append((s, e))
    return out


def _split_long(text: str, s: int, e: int, lang: str, budget: int, count: TokenCounter) -> list[tuple[int, int]]:
    """Hard-split an oversize unit on whitespace so each piece fits the budget."""
    pieces: list[tuple[int, int]] = []
    last_end = s
    words = [m.span() for m in re.finditer(r"\S+", text[s:e])]
    start = None
    for ws, we in words:
        ws, we = ws + s, we + s
        if start is None:
            start = ws
        if count(text[start:we], lang) > budget and start != ws:
            pieces.append((start, last_end))
            start = ws
        last_end = we
    if start is not None:
        pieces.append((start, last_end))
    return pieces or [(s, e)]


def _pack(text, lo, hi, lang, budget, overlap, count) -> list[tuple[int, int]]:
    units: list[tuple[int, int]] = []
    for s, e in _units(text, lo, hi):
        if count(text[s:e], lang) > budget:
            units.extend(_split_long(text, s, e, lang, budget, count))
        else:
            units.append((s, e))
    spans, i = [], 0
    while i < len(units):
        j, cs = i, units[i][0]
        while j < len(units) and count(text[cs:units[j][1]], lang) <= budget:
            j += 1
        j = max(j, i + 1)
        spans.append((cs, units[j - 1][1]))
        if j >= len(units):
            break
        # step back whole units to cover ~overlap tokens, but always advance
        k, acc = j, 0
        while k > i + 1 and acc < overlap:
            k -= 1
            acc += count(text[units[k][0]:units[k][1]], lang)
        i = max(k, i + 1)
    return spans


def build_chunks(doc_id: str, parsed_sha256: str, text: str, lang: str, sections: list[dict], strategy: str = "fixed",
                 budget: int = 512, overlap: int = 64, count: TokenCounter = approx_tokens,
                 counter_name: str = "approx_tokens") -> list[Chunk]:
    if strategy == "fixed":
        regions = [(0, len(text), "")]
        # still record the section each chunk starts in
    elif strategy == "heading":
        regions = [(s["char_start"], s["char_end"], s["path"]) for s in sections]
    else:
        raise ValueError(f"unknown strategy {strategy}")
    chunks: list[Chunk] = []
    for lo, hi, path in regions:
        for s, e in _pack(text, lo, hi, lang, budget, overlap, count):
            sec = path or _section_at(sections, s)
            t = text[s:e]
            assert t == text[s:e]
            chunks.append(Chunk(_cid(doc_id, parsed_sha256, strategy, s, e), doc_id, parsed_sha256, lang, sec, s, e,
                                strategy, budget, counter_name, t, junk_reason(t, lang)))
    return chunks


def _section_at(sections: list[dict], pos: int) -> str:
    for s in sections:
        if s["char_start"] <= pos < s["char_end"] + 1:
            return s["path"]
    return ""

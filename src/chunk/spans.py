"""Span overlap rules shared by chunking and the eval runner."""
from __future__ import annotations


def overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def chunk_hits_span(chunk_start: int, chunk_end: int, gold_start: int, gold_end: int, frac: float = 0.5) -> bool:
    """Hit if the chunk contains the gold span or overlaps >= frac of it (docs/02)."""
    if gold_end <= gold_start:
        return False
    if chunk_start <= gold_start and chunk_end >= gold_end:
        return True
    return overlap(chunk_start, chunk_end, gold_start, gold_end) / (gold_end - gold_start) >= frac

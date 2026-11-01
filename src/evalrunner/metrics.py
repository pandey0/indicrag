"""Retrieval metrics scored against gold evidence SPANS (chunker-independent), docs/05.

A retrieved chunk is relevant to an item if it hits any of the item's gold spans (same doc, contains it or overlaps >= 50%).
Unanswerable items (no evidence) are excluded from retrieval metrics. Binary relevance for nDCG.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Sequence

from src.chunk.spans import chunk_hits_span


@dataclass(frozen=True)
class ChunkRef:
    chunk_id: str
    doc_id: str
    parsed_sha256: str
    char_start: int
    char_end: int


def relevance(ranked: Sequence[ChunkRef], evidence: Sequence[dict]) -> list[int]:
    """1 if the chunk hits any gold span of the item (doc and parsed hash must match), else 0."""
    out = []
    for c in ranked:
        hit = any(e["doc_id"] == c.doc_id and e["parsed_sha256"] == c.parsed_sha256
                  and chunk_hits_span(c.char_start, c.char_end, e["char_start"], e["char_end"]) for e in evidence)
        out.append(int(hit))
    return out


def recall_at_k(rel: Sequence[int], k: int) -> float:
    return float(any(rel[:k]))


def mrr(rel: Sequence[int], k: int = 10) -> float:
    for i, r in enumerate(rel[:k], 1):
        if r:
            return 1.0 / i
    return 0.0


def ndcg_at_k(rel: Sequence[int], k: int = 10, n_relevant: int | None = None) -> float:
    """Binary-gain nDCG; ideal DCG assumes n_relevant relevant chunks (default: those found in the list, min 1)."""
    dcg = sum(r / math.log2(i + 1) for i, r in enumerate(rel[:k], 1))
    n = n_relevant if n_relevant is not None else max(1, sum(rel[:k]))
    idcg = sum(1 / math.log2(i + 1) for i in range(1, min(n, k) + 1))
    return dcg / idcg if idcg else 0.0


def paired_bootstrap(a: Sequence[float], b: Sequence[float], n: int = 10000, seed: int = 0) -> dict:
    """Paired bootstrap over items: mean(a-b) with 95% CI and two-sided p (share of resamples crossing 0)."""
    assert len(a) == len(b) and a, "paired samples of equal, non-zero length"
    d = [x - y for x, y in zip(a, b)]
    rng = random.Random(seed)
    m = len(d)
    means = sorted(sum(d[rng.randrange(m)] for _ in range(m)) / m for _ in range(n))
    mean = sum(d) / m
    lo, hi = means[int(0.025 * n)], means[int(0.975 * n) - 1]
    p = 2 * min(sum(x <= 0 for x in means), sum(x >= 0 for x in means)) / n
    return {"mean_diff": mean, "ci95": (lo, hi), "p": min(1.0, p), "n": m}

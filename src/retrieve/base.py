from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Hit:
    chunk_id: str
    score: float


class Retriever(Protocol):
    def search(self, query: str, k: int = 5, lang: str | None = None) -> list[Hit]: ...


def rrf(rankings: list[list[Hit]], k: int = 60, top: int | None = None) -> list[Hit]:
    """Reciprocal rank fusion: score = sum 1/(k + rank). Ties broken by chunk_id for determinism."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, h in enumerate(ranking, start=1):
            scores[h.chunk_id] = scores.get(h.chunk_id, 0.0) + 1.0 / (k + rank)
    out = [Hit(c, s) for c, s in sorted(scores.items(), key=lambda x: (-x[1], x[0]))]
    return out[:top] if top else out

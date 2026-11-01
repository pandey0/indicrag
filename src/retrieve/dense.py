"""Brute-force dense retriever over a normalised matrix (reproducible eval path; pgvector serves the app)."""
from __future__ import annotations

import numpy as np

from .base import Hit


class DenseRetriever:
    def __init__(self, embedder, ids: list[str], langs: list[str], matrix: np.ndarray):
        assert len(ids) == len(langs) == matrix.shape[0]
        self.embedder, self.ids, self.langs, self.m = embedder, ids, np.array(langs), matrix

    def search(self, query: str, k: int = 5, lang: str | None = None) -> list[Hit]:
        q = self.embedder.encode([query], "query")[0]
        sims = self.m @ q
        idx = np.arange(len(self.ids)) if lang is None else np.flatnonzero(self.langs == lang)
        # deterministic: sort by (-score, id)
        order = sorted(idx, key=lambda i: (-float(sims[i]), self.ids[i]))[:k]
        return [Hit(self.ids[i], float(sims[i])) for i in order]

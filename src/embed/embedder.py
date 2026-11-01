"""Embedding interface. Vectors are L2-normalised, so cosine similarity == dot product (and pgvector `<=>` works)."""
from __future__ import annotations

import hashlib
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    name: str
    dim: int

    def encode(self, texts: list[str], kind: str) -> np.ndarray:  # kind: 'query' | 'passage'
        ...


def _norm(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(n, 1e-12)


# E5-family models are trained with these prefixes; omitting them silently degrades retrieval.
PREFIXES = {"intfloat/multilingual-e5": {"query": "query: ", "passage": "passage: "}}


def prefix_for(model: str, kind: str) -> str:
    if kind not in ("query", "passage"):
        raise ValueError(f"kind must be 'query' or 'passage', got {kind!r}")
    for stem, p in PREFIXES.items():
        if model.startswith(stem):
            return p[kind]
    return ""


class SentenceTransformerEmbedder:
    def __init__(self, model: str, batch_size: int = 16, max_seq_length: int = 512):
        from sentence_transformers import SentenceTransformer  # heavy import kept lazy

        self.name = model
        self.batch_size = batch_size
        self._m = SentenceTransformer(model, device="cpu")
        self._m.max_seq_length = max_seq_length
        self.dim = self._m.get_sentence_embedding_dimension()

    def encode(self, texts: list[str], kind: str) -> np.ndarray:
        pre = prefix_for(self.name, kind)
        v = self._m.encode([pre + t for t in texts], batch_size=self.batch_size, convert_to_numpy=True,
                           normalize_embeddings=False, show_progress_bar=False)
        return _norm(v.astype(np.float32))


class HashEmbedder:
    """Deterministic bag-of-words hashing embedder for tests (no model). Shares words => higher cosine."""

    def __init__(self, dim: int = 64, name: str = "hash-test"):
        self.dim, self.name = dim, name

    def encode(self, texts: list[str], kind: str) -> np.ndarray:
        prefix_for(self.name, kind)  # validates kind
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for w in t.lower().split():
                out[i, int(hashlib.md5(w.encode()).hexdigest(), 16) % self.dim] += 1.0
        return _norm(out)

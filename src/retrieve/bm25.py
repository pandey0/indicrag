"""Pure-Python BM25 Okapi baseline over chunk records."""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from .base import Hit

# word = letters/digits plus combining marks and joiners; danda (U+0964/5) is punctuation, not a letter
_TOKEN = re.compile(r"[\w\u0900-\u0963\u0966-\u096F\u0971-\u097F\u0C80-\u0CFF\u200c\u200d]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text).lower()
    return [t.strip("_") for t in _TOKEN.findall(text) if t.strip("_")]


def char_ngrams(text: str, lo: int = 3, hi: int = 5) -> list[str]:
    """Within-word character n-grams (words padded with boundary marks); helps inflected/agglutinative scripts."""
    out: list[str] = []
    for w in tokenize(text):
        w = f"^{w}$"
        if len(w) <= lo:
            out.append(w)
            continue
        for n in range(lo, hi + 1):
            out.extend(w[i:i + n] for i in range(len(w) - n + 1))
    return out


ANALYZERS = {"word": tokenize, "char": char_ngrams}


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75, analyzer: str = "word"):
        self.k1, self.b = k1, b
        self.analyze = ANALYZERS[analyzer]
        self.ids: list[str] = []
        self.langs: list[str] = []
        self.tf: list[Counter] = []
        self.len: list[int] = []
        self.df: Counter = Counter()
        self.postings: dict[str, list[int]] = defaultdict(list)
        self.avgdl = 0.0

    def add(self, chunk_id: str, text: str, lang: str) -> None:
        toks = self.analyze(text)
        i = len(self.ids)
        self.ids.append(chunk_id)
        self.langs.append(lang)
        c = Counter(toks)
        self.tf.append(c)
        self.len.append(len(toks))
        for t in c:
            self.df[t] += 1
            self.postings[t].append(i)
        self.avgdl = sum(self.len) / len(self.len)

    @classmethod
    def from_jsonl(cls, path: str | Path, **kw) -> BM25:
        m = cls(**kw)
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                m.add(r["chunk_id"], r["text"], r["lang"])
        return m

    def _idf(self, term: str) -> float:
        n, N = self.df[term], len(self.ids)
        return math.log(1 + (N - n + 0.5) / (n + 0.5))

    def search(self, query: str, k: int = 5, lang: str | None = None) -> list[Hit]:
        scores: dict[int, float] = defaultdict(float)
        for t in set(self.analyze(query)):
            if t not in self.postings:
                continue
            idf = self._idf(t)
            for i in self.postings[t]:
                if lang and self.langs[i] != lang:
                    continue
                f = self.tf[i][t]
                denom = f + self.k1 * (1 - self.b + self.b * self.len[i] / (self.avgdl or 1))
                scores[i] += idf * f * (self.k1 + 1) / denom
        ranked = sorted(scores.items(), key=lambda x: (-x[1], self.ids[x[0]]))
        return [Hit(self.ids[i], s) for i, s in ranked[:k]]

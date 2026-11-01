"""Weak proxy check, NOT a benchmark: query = Wikipedia article title, gold = that article (doc-level).

Only discriminates tokenisation/analyzer choices on hi/kn/en before real gold items exist. Title text is also in the
article, so absolute numbers are optimistic and must never be reported as retrieval quality.
"""
import csv
import json
import sys

sys.path.insert(0, ".")
from src.retrieve.bm25 import BM25  # noqa: E402

chunks = [json.loads(l) for l in open("data/chunks/fixed_512_64.jsonl", encoding="utf-8")]
doc_of = {c["chunk_id"]: c["doc_id"] for c in chunks}
queries = [(r["source_id"], r["topic"], r["expected_lang"]) for r in csv.DictReader(open("data/sources_wikipedia.csv", encoding="utf-8"))]
indexed = {c["doc_id"] for c in chunks}
queries = [q for q in queries if q[0] in indexed]


def run(analyzer):
    m = BM25(analyzer=analyzer)
    for c in chunks:
        m.add(c["chunk_id"], c["text"], c["lang"])
    res = {}
    for lang in ("en", "hi", "kn"):
        qs = [q for q in queries if q[2] == lang]
        h1 = h5 = 0
        for sid, title, _ in qs:
            docs = []
            for h in m.search(title, 20, lang):
                d = doc_of[h.chunk_id]
                if d not in docs:
                    docs.append(d)
            h1 += bool(docs[:1] and docs[0] == sid)
            h5 += sid in docs[:5]
        res[lang] = (len(qs), round(h1 / max(len(qs), 1), 2), round(h5 / max(len(qs), 1), 2))
    return res


for a in ("word", "char"):
    print(a, run(a), "(n, doc-level hit@1, hit@5)")

"""Retrieval evaluation: gold JSONL x retriever -> per-language metrics + per-item results.

python3 -m src.evalrunner.run_retrieval --gold data/gold/dev.jsonl --chunks data/chunks/fixed_512_64.jsonl \
    --retriever bm25|bm25char|dense|hybrid [--model intfloat/multilingual-e5-small] [--k 10]

Writes eval/results/<run_id>/{metrics.json,run_items.jsonl,config.json}. Unanswerable items are skipped (no gold span).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

from src.retrieve.base import rrf
from src.retrieve.bm25 import BM25

from .metrics import ChunkRef, mrr, ndcg_at_k, recall_at_k, relevance


def load_chunks(path: str | Path) -> dict[str, dict]:
    return {c["chunk_id"]: c for c in (json.loads(l) for l in open(path, encoding="utf-8") if l.strip())}


def build_retriever(kind: str, chunks: dict[str, dict], model: str, emb_path: str | None = None):
    def bm(analyzer):
        m = BM25(analyzer=analyzer)
        for c in chunks.values():
            m.add(c["chunk_id"], c["text"], c["lang"])
        return m

    if kind in ("bm25", "bm25char"):
        return bm("word" if kind == "bm25" else "char")
    import numpy as np

    from src.embed.embedder import SentenceTransformerEmbedder
    from src.retrieve.dense import DenseRetriever

    p = emb_path or f"data/embeddings/{model.replace('/', '_')}__{Path(next(iter(chunks.values()))['strategy'] + '_' + str(next(iter(chunks.values()))['budget'])).stem}.npz"
    z = np.load(p, allow_pickle=False)
    dense = DenseRetriever(SentenceTransformerEmbedder(model), z["ids"].tolist(), z["langs"].tolist(), z["matrix"])
    if kind == "dense":
        return dense
    sparse = bm("word")

    class Hybrid:
        def search(self, query, k=5, lang=None):
            return rrf([sparse.search(query, 50, lang), dense.search(query, 50, lang)], top=k)

    return Hybrid()


def evaluate(items: list[dict], retriever, chunks: dict[str, dict], k: int = 10, same_lang: bool = True) -> tuple[dict, list[dict]]:
    per_item, by_lang = [], defaultdict(lambda: defaultdict(list))
    for it in items:
        if not it.get("evidence") or it.get("answerable") is False:
            continue
        hits = retriever.search(it["question"], k, it["lang"] if same_lang else None)
        ranked = [ChunkRef(h.chunk_id, chunks[h.chunk_id]["doc_id"], chunks[h.chunk_id]["parsed_sha256"],
                           chunks[h.chunk_id]["char_start"], chunks[h.chunk_id]["char_end"]) for h in hits]
        rel = relevance(ranked, it["evidence"])
        m = {"recall@1": recall_at_k(rel, 1), "recall@5": recall_at_k(rel, 5), "recall@10": recall_at_k(rel, 10),
             "mrr": mrr(rel, 10), "ndcg@10": ndcg_at_k(rel, 10)}
        per_item.append({"id": it["id"], "lang": it["lang"], "retrieved": [h.chunk_id for h in hits], "rel": rel, **m})
        for key, v in m.items():
            by_lang[it["lang"]][key].append(v)
            by_lang["all"][key].append(v)
    summary = {lang: {"n": len(next(iter(d.values()))), **{k_: round(sum(v) / len(v), 4) for k_, v in d.items()}} for lang, d in by_lang.items()}
    return summary, per_item


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--chunks", default="data/chunks/fixed_512_64.jsonl")
    ap.add_argument("--retriever", default="bm25", choices=["bm25", "bm25char", "dense", "hybrid"])
    ap.add_argument("--model", default="intfloat/multilingual-e5-small")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--cross-lingual", action="store_true", help="search all languages instead of the question's language")
    a = ap.parse_args()
    chunks = load_chunks(a.chunks)
    items = [json.loads(l) for l in open(a.gold, encoding="utf-8") if l.strip()]
    cfg = {"gold": a.gold, "gold_sha": hashlib.sha256(Path(a.gold).read_bytes()).hexdigest()[:12], "chunks": a.chunks,
           "retriever": a.retriever, "model": a.model if a.retriever in ("dense", "hybrid") else None, "k": a.k, "same_lang": not a.cross_lingual}
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    run_id = f"{a.retriever}-{hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:8]}"
    summary, per_item = evaluate(items, build_retriever(a.retriever, chunks, a.model), chunks, a.k, not a.cross_lingual)
    out = Path("eval/results") / run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps({**cfg, "git_sha": sha}, indent=1), encoding="utf-8")
    (out / "metrics.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    with open(out / "run_items.jsonl", "w", encoding="utf-8") as f:
        for r in per_item:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(run_id, json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()

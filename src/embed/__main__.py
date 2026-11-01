"""python -m src.embed build --model intfloat/multilingual-e5-small [--chunks data/chunks/fixed_512_64.jsonl]

Writes data/embeddings/<model>__<chunkfile>.npz (ids, langs, matrix). Idempotent: reuses vectors for chunk ids already present.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .embedder import SentenceTransformerEmbedder


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m src.embed")
    ap.add_argument("cmd", choices=["build"])
    ap.add_argument("--model", default="intfloat/multilingual-e5-small")
    ap.add_argument("--chunks", default="data/chunks/fixed_512_64.jsonl")
    ap.add_argument("--batch", type=int, default=16)
    a = ap.parse_args()
    out = Path("data/embeddings") / f"{a.model.replace('/', '_')}__{Path(a.chunks).stem}.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    chunks = [json.loads(l) for l in open(a.chunks, encoding="utf-8")]
    have: dict[str, np.ndarray] = {}
    if out.exists():
        z = np.load(out, allow_pickle=False)
        have = dict(zip(z["ids"].tolist(), z["matrix"]))
    todo = [c for c in chunks if c["chunk_id"] not in have]
    print(f"{len(chunks)} chunks, {len(have)} cached, {len(todo)} to embed")
    if todo:
        emb = SentenceTransformerEmbedder(a.model, a.batch)
        # sort by length so batches pad little; order does not change per-text vectors
        todo.sort(key=lambda c: len(c["text"]))
        for i in range(0, len(todo), 64):
            part = todo[i:i + 64]
            for c, v in zip(part, emb.encode([c["text"] for c in part], "passage")):
                have[c["chunk_id"]] = v
            print(f"  {min(i + 64, len(todo))}/{len(todo)}", flush=True)
    ids = [c["chunk_id"] for c in chunks]
    np.savez(out, ids=np.array(ids), langs=np.array([c["lang"] for c in chunks]), matrix=np.stack([have[i] for i in ids]))
    print("wrote", out)


if __name__ == "__main__":
    main()

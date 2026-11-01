"""Run every retriever on a gold file and print the results tables + paired comparisons (reproduces eval/RESULTS.md).

.venv/bin/python scripts/run_all_retrievers.py --gold data/gold/dev.jsonl [--models intfloat/multilingual-e5-small BAAI/bge-m3]
Dense/hybrid need embeddings from `python -m src.embed build --model <m>` for the current chunk file.
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.evalrunner.compare import compare  # noqa: E402
from src.evalrunner.run_retrieval import build_retriever, evaluate, load_chunks  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--gold", default="data/gold/dev.jsonl")
ap.add_argument("--chunks", default="data/chunks/fixed_512_64.jsonl")
ap.add_argument("--models", nargs="*", default=["intfloat/multilingual-e5-small"])
ap.add_argument("--k", type=int, default=10)
a = ap.parse_args()

chunks = load_chunks(a.chunks)
items = [json.loads(line) for line in open(a.gold, encoding="utf-8") if line.strip()]
systems = {"bm25": ("bm25", ""), "bm25char": ("bm25char", "")}
for m in a.models:
    short = m.split("/")[-1]
    systems[f"dense:{short}"] = ("dense", m)
    systems[f"hybrid:{short}"] = ("hybrid", m)
summ, per = {}, {}
for name, (kind, model) in systems.items():
    if kind in ("dense", "hybrid"):
        emb = Path(f"data/embeddings/{model.replace('/', '_')}__{Path(a.chunks).stem}.npz")
        if not emb.exists():
            print(f"skip {name}: no embeddings", file=sys.stderr)
            continue
        import numpy as np

        missing = set(chunks) - set(np.load(emb, allow_pickle=False)["ids"].tolist())
        if missing:
            print(f"skip {name}: embeddings stale ({len(missing)} chunks missing); run python -m src.embed build --model {model}", file=sys.stderr)
            continue
    s, p = evaluate(items, build_retriever(kind, chunks, model, a.chunks), chunks, a.k)
    summ[name], per[name] = s, {r["id"]: r for r in p}

print(f"gold={a.gold} chunks={a.chunks}\n\n| system | n | recall@1 | recall@5 | MRR | nDCG@10 |\n|---|---|---|---|---|---|")
for n, s in summ.items():
    v = s["all"]
    print(f"| {n} | {v['n']} | {v['recall@1']:.3f} | {v['recall@5']:.3f} | {v['mrr']:.3f} | {v['ndcg@10']:.3f} |")
print("\nrecall@1 by language:", {n: {lg: s[lg]["recall@1"] for lg in s if lg != "all"} for n, s in summ.items()})
print("\nPaired comparisons (diff = A - B, 95% paired-bootstrap CI):")
for x, y in itertools.combinations(per, 2):
    for metric in ("recall@1", "mrr"):
        v = compare(per[x], per[y], metric)["all"]
        flag = "  <- CI excludes 0" if v["ci_excludes_0"] else ""
        print(f"  {x} - {y} {metric}: {v['diff']:+.3f} [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}]{flag}")

"""Paired comparison of two retrieval runs on the same gold items (docs/05).

python3 -m src.evalrunner.compare eval/results/<runA> eval/results/<runB> [--metric recall@1]
Reports per language and overall: n, mean A, mean B, mean(A-B), 95% paired-bootstrap CI and p. Items must match exactly; a difference whose
CI includes 0 is NOT a finding. With small n (drafts, pilot sets) this is a pipeline check, never a result.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .metrics import paired_bootstrap


def load_items(run_dir: str | Path) -> dict[str, dict]:
    return {r["id"]: r for r in (json.loads(line) for line in open(Path(run_dir) / "run_items.jsonl", encoding="utf-8") if line.strip())}


def compare(a: dict[str, dict], b: dict[str, dict], metric: str = "recall@1", seed: int = 0) -> dict:
    if set(a) != set(b):
        raise ValueError(f"runs cover different items: only-A={sorted(set(a) - set(b))[:3]} only-B={sorted(set(b) - set(a))[:3]}")
    out = {}
    for lang in sorted({r["lang"] for r in a.values()}) + ["all"]:
        ids = sorted(i for i in a if lang == "all" or a[i]["lang"] == lang)
        xa, xb = [a[i][metric] for i in ids], [b[i][metric] for i in ids]
        r = paired_bootstrap(xa, xb, seed=seed)
        out[lang] = {"n": len(ids), "mean_a": round(sum(xa) / len(ids), 4), "mean_b": round(sum(xb) / len(ids), 4),
                     "diff": round(r["mean_diff"], 4), "ci95": [round(r["ci95"][0], 4), round(r["ci95"][1], 4)], "p": round(r["p"], 4),
                     "ci_excludes_0": r["ci95"][0] > 0 or r["ci95"][1] < 0}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_a")
    ap.add_argument("run_b")
    ap.add_argument("--metric", default="recall@1", choices=["recall@1", "recall@5", "recall@10", "mrr", "ndcg@10"])
    a = ap.parse_args()
    for lang, v in compare(load_items(a.run_a), load_items(a.run_b), a.metric).items():
        print(lang, json.dumps(v))


if __name__ == "__main__":
    main()

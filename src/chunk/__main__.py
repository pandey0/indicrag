"""python -m src.chunk build [--strategy fixed|heading] [--budget 512] [--overlap 64] [--include-junk]"""
from __future__ import annotations

import argparse
import collections
import csv
import json
from pathlib import Path

from .chunker import build_chunks

DATA = Path("data")
USABLE = {"ok", "ocr_ok"}


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m src.chunk")
    ap.add_argument("cmd", choices=["build"])
    ap.add_argument("--strategy", default="fixed", choices=["fixed", "heading"])
    ap.add_argument("--budget", type=int, default=512)
    ap.add_argument("--overlap", type=int, default=64)
    ap.add_argument("--include-junk", action="store_true", help="keep chunks flagged as OCR garbage")
    a = ap.parse_args()

    out_dir = DATA / "chunks"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{a.strategy}_{a.budget}_{a.overlap}.jsonl"
    kept = collections.Counter()
    junk = collections.Counter()  # keyed (lang, reason)
    with open(DATA / "corpus_manifest.csv", encoding="utf-8") as f, open(out, "w", encoding="utf-8") as w:
        for r in csv.DictReader(f):
            if r["parse_status"] not in USABLE or not r["text_path"]:
                continue
            tp = DATA / r["text_path"]
            text = tp.read_text(encoding="utf-8")
            sections = json.loads(tp.with_suffix(".sections.json").read_text(encoding="utf-8"))
            for c in build_chunks(r["source_id"], r["parsed_sha256"], text, r["lang"], sections, a.strategy, a.budget, a.overlap):
                assert c.text == text[c.char_start:c.char_end]
                if c.junk and not a.include_junk:
                    junk[(r["lang"], c.junk)] += 1
                    continue
                kept[r["lang"]] += 1
                w.write(json.dumps(c.to_json(), ensure_ascii=False) + "\n")
    print(f"wrote {out}")
    print("kept chunks by lang:", dict(kept))
    print("dropped by (lang, reason):", dict(junk))


if __name__ == "__main__":
    main()

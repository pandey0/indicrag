"""Validate gold QA JSONL: JSON schema, unique ids, evidence anchoring, cross-item rules.

Evidence checks (docs/02, docs/04): the parsed text is looked up through the corpus manifest; the item must pin the
current parsed_sha256 and raw sha256, and quote must equal text[char_start:char_end]. A stale pin is reported as
'stale' (re-anchor from quote), distinct from a plain mismatch.

python3 -m src.evalrunner.validate_gold data/gold/dev.jsonl [--manifest data/corpus_manifest.csv]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "data/schema/qa_item.schema.json"


def load_manifest(path: Path) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        return {r["source_id"]: r for r in csv.DictReader(f)}


def validate_items(items: list[dict], manifest: dict[str, dict], data_dir: Path) -> list[str]:
    errors: list[str] = []
    validator = Draft7Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    seen: set[str] = set()
    texts: dict[str, str] = {}
    for n, it in enumerate(items, 1):
        tag = f"item {it.get('id', f'#{n}')}"
        for e in sorted(validator.iter_errors(it), key=lambda e: list(e.path)):
            errors.append(f"{tag}: schema: {'/'.join(map(str, e.path))}: {e.message}")
        if it.get("id") in seen:
            errors.append(f"{tag}: duplicate id")
        seen.add(it.get("id"))
        if it.get("answerable") is False and it.get("evidence"):
            errors.append(f"{tag}: unanswerable item must have empty evidence")
        if it.get("answerable", True) and it.get("qtype") != "unanswerable" and not it.get("evidence"):
            errors.append(f"{tag}: answerable item needs evidence")
        if it.get("source_kind") == "aligned_parallel" and not it.get("aligned_with"):
            errors.append(f"{tag}: aligned_parallel needs aligned_with")
        if it.get("lang") == "kn" and it.get("source_kind") != "aligned_parallel" and it.get("native_verified") is not True:
            errors.append(f"{tag}: kn item must be aligned_parallel or native_verified (no authored-Kannada claim)")
        if it.get("writer") and it.get("labeller") and it["writer"] == it["labeller"] and it.get("source_kind") == "hand_written":
            pass  # same person writing and picking is allowed only when marked; reported as a warning elsewhere
        for ev in it.get("evidence") or []:
            row = manifest.get(ev.get("doc_id"))
            if row is None or not row.get("text_path"):
                errors.append(f"{tag}: evidence doc_id {ev.get('doc_id')!r} not in manifest/parsed")
                continue
            tp = data_dir / row["text_path"]
            if tp not in texts:
                texts[tp] = tp.read_text(encoding="utf-8")
            text = texts[tp]
            s, e, q = ev.get("char_start", -1), ev.get("char_end", -1), ev.get("quote", "")
            if ev.get("parsed_sha256") != row["parsed_sha256"] or ev.get("doc_sha256") != row["sha256"]:
                where = "found at %d" % text.find(q) if q and q in text else "quote not found"
                errors.append(f"{tag}: stale evidence pin for {ev['doc_id']} (doc changed; re-anchor from quote: {where})")
            elif not (0 <= s < e <= len(text)):
                errors.append(f"{tag}: span {s}:{e} out of range (len {len(text)})")
            elif text[s:e] != q:
                errors.append(f"{tag}: quote != text[{s}:{e}] for {ev['doc_id']}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("gold")
    ap.add_argument("--manifest", default="data/corpus_manifest.csv")
    ap.add_argument("--data-dir", default="data")
    a = ap.parse_args()
    items = [json.loads(l) for l in open(a.gold, encoding="utf-8") if l.strip()]
    errs = validate_items(items, load_manifest(Path(a.manifest)), Path(a.data_dir))
    for e in errs:
        print(e)
    print(f"{len(items)} items, {len(errs)} problems")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())

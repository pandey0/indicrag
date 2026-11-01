"""Sample candidate evidence passages into a labelling sheet (docs/04).

The sheet only PICKS passages (evidence prefilled: offsets, hashes, verbatim quote). A different person/process
writes question + answer, so evidence picker != question writer. Kannada rows are marked aligned_parallel with the
English twin article in notes: Kannada questions are derived by alignment, never authored here.

python3 scripts/make_labelling_sheet.py --per-lang 40 --seed 7 --out data/labelling/pilot_sheet.csv
"""
import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, ".")
from src.chunk.quality import junk_reason  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--per-lang", type=int, default=40)
ap.add_argument("--max-per-doc", type=int, default=2)
ap.add_argument("--min-chars", type=int, default=150)
ap.add_argument("--max-chars", type=int, default=700)
ap.add_argument("--seed", type=int, default=7)
ap.add_argument("--prefix", default="wp_", help="doc_id prefix to draw from (default: Wikipedia fallback corpus)")
ap.add_argument("--out", default="data/labelling/pilot_sheet.csv")
a = ap.parse_args()

man = {r["source_id"]: r for r in csv.DictReader(open("data/corpus_manifest.csv", encoding="utf-8")) if r["parse_status"] in ("ok", "ocr_ok")}
pairs = {r["source_id"]: r.get("pair_id", "") for r in csv.DictReader(open("data/sources_wikipedia.csv", encoding="utf-8"))}
cols = next(csv.reader(open("data/labelling/labelling_sheet_template.csv", encoding="utf-8")))

cands = defaultdict(list)
for sid, r in man.items():
    if not sid.startswith(a.prefix):
        continue
    text = Path("data", r["text_path"]).read_text(encoding="utf-8")
    pos = 0
    for para in text.split("\n"):
        start, end = pos, pos + len(para)
        pos = end + 1
        if a.min_chars <= len(para) <= a.max_chars and junk_reason(para, r["lang"]) is None and para.count(" ") > 15:
            cands[(r["lang"], sid)].append((start, end, para))

rng = random.Random(a.seed)
rows = []
for lang in ("en", "hi", "kn"):
    docs = sorted(k for k in cands if k[0] == lang)
    pool = []
    for k in docs:
        for c in rng.sample(cands[k], min(a.max_per_doc, len(cands[k]))):
            pool.append((k[1], c))
    rng.shuffle(pool)
    for n, (sid, (s, e, para)) in enumerate(pool[:a.per_lang], 1):
        r = man[sid]
        row = dict.fromkeys(cols, "")
        row.update(id=f"{lang}-pilot-{n:03d}", lang=lang, register="formal", doc_id=sid, doc_sha256=r["sha256"],
                   parsed_sha256=r["parsed_sha256"], parser_version=r["parser_version"], char_start=s, char_end=e, quote=para,
                   review_status="draft", source_kind="aligned_parallel" if lang == "kn" else "hand_written", answerable="true")
        if lang == "kn":
            row["notes"] = f"aligned twin: {pairs.get(sid, '')}_en (write question in en, align to kn; needs native check)"
        rows.append(row)

Path(a.out).parent.mkdir(parents=True, exist_ok=True)
with open(a.out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
cnt = defaultdict(int)
for r in rows:
    cnt[r["lang"]] += 1
print(a.out, dict(cnt), "docs with candidates:", len({k[1] for k in cands}))

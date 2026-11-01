"""For English gold/draft items whose Wikipedia article has a Kannada twin, propose the best kn evidence paragraphs.

Output data/labelling/kn_alignment_candidates.csv (gitignored) for a NATIVE Kannada checker: columns hold the English quote,
the proposed Kannada span, alignment_score and the numeric-consistency flag. Nothing here is native-verified.

.venv/bin/python scripts/align_kn_candidates.py data/gold/drafts/pilot_drafts.jsonl [--model intfloat/multilingual-e5-small]
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.embed.embedder import SentenceTransformerEmbedder  # noqa: E402
from src.evalrunner.align import best_alignment  # noqa: E402

gold = sys.argv[1]
model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "intfloat/multilingual-e5-small"
pair = {r["source_id"]: r["pair_id"] for r in csv.DictReader(open("data/sources_wikipedia.csv", encoding="utf-8"))}
man = {r["source_id"]: r for r in csv.DictReader(open("data/corpus_manifest.csv", encoding="utf-8"))}
emb = SentenceTransformerEmbedder(model)

rows = []
for line in open(gold, encoding="utf-8"):
    it = json.loads(line)
    if it["lang"] != "en":
        continue
    ev = it["evidence"][0]
    twin = f"{pair.get(ev['doc_id'], '')}_kn"
    if twin not in man or man[twin]["parse_status"] not in ("ok", "ocr_ok"):
        continue
    text = Path("data", man[twin]["text_path"]).read_text(encoding="utf-8")
    for rank, a in enumerate(best_alignment(ev["quote"], text, emb, top=3), 1):
        rows.append({"en_item": it["id"], "en_question": it["question"], "en_quote": ev["quote"], "kn_doc": twin, "rank": rank,
                     "char_start": a.char_start, "char_end": a.char_end, "alignment_score": round(a.score, 4),
                     "numeric_ok": a.numeric_ok, "kn_text": a.text, "native_verdict": ""})
out = Path("data/labelling/kn_alignment_candidates.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])) if rows else None
    if w:
        w.writeheader(); w.writerows(rows)
print(out, len(rows), "candidate spans for", len({r["en_item"] for r in rows}), "en items")

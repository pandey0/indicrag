"""Apply db/migrations and load manifest documents + chunks JSONL into Postgres.

Usage: DATABASE_URL=postgresql://... python3 scripts/db_load.py data/chunks/fixed_512_64.jsonl [--reset]
"""
import csv
import json
import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

dsn = os.environ["DATABASE_URL"]
chunks_path = sys.argv[1]
con = psycopg2.connect(dsn)
cur = con.cursor()
if "--reset" in sys.argv:
    cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
for m in sorted(Path("db/migrations").glob("*.sql")):
    cur.execute("SELECT to_regclass('schema_migrations')")
    done = cur.fetchone()[0] and (cur.execute("SELECT 1 FROM schema_migrations WHERE version=%s", (m.stem,)) or cur.fetchone())
    if not done:
        cur.execute(m.read_text(encoding="utf-8"))
con.commit()

rows = [r for r in csv.DictReader(open("data/corpus_manifest.csv", encoding="utf-8")) if r["parse_status"] in ("ok", "ocr_ok")]
psycopg2.extras.execute_values(cur, """INSERT INTO documents (id,url,title,lang,role,licence_note,redistribute,fetched_at,sha256,parsed_sha256,parser_version)
  VALUES %s ON CONFLICT (id) DO UPDATE SET parsed_sha256=EXCLUDED.parsed_sha256, parser_version=EXCLUDED.parser_version, sha256=EXCLUDED.sha256""",
  [(r["source_id"], r["url"], r["title"], r["lang"], r["role"] or "candidate", r["licence_verdict"], r["redistribute"] == "true",
    r["fetched_at"] or None, r["sha256"], r["parsed_sha256"], r["parser_version"]) for r in rows])
ids = {r["source_id"] for r in rows}
batch = []
for line in open(chunks_path, encoding="utf-8"):
    c = json.loads(line)
    if c["doc_id"] in ids:
        batch.append((c["chunk_id"], c["doc_id"], c["parsed_sha256"], c["lang"], c["section_path"], c["char_start"], c["char_end"],
                      c["strategy"], c["budget"], c["counter"], c["text"]))
psycopg2.extras.execute_values(cur, """INSERT INTO chunks (id,doc_id,parsed_sha256,lang,section_path,char_start,char_end,strategy,budget,counter,text)
  VALUES %s ON CONFLICT (id) DO NOTHING""", batch, page_size=500)
con.commit()
cur.execute("SELECT lang, count(*) FROM chunks GROUP BY lang ORDER BY lang")
print("documents:", len(rows), "chunks by lang:", cur.fetchall())

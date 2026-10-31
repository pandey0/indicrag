#!/usr/bin/env python3
"""Week-1 parse-feasibility spike.

Fetch each candidate (politely), extract text, score extraction quality, and write:
  data/corpus_manifest.csv      (committed; licence_verdict stays 'unclear' until a human checks terms)
  data/spike/report.md          (committed; metrics only, no document text)
  data/processed/spike/*.txt    (gitignored; extracted text for eyeballing)
  data/raw/spike/*              (gitignored; raw fetched files)
"""
from __future__ import annotations

import csv
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.parse.quality import classify, compute_metrics  # noqa: E402

UA = "IndicRAG-research-spike/0.1 (+https://github.com/; contact: arpit242002@gmail.com)"
DELAY_S = 2.0
RAW = ROOT / "data/raw/spike"
OUT = ROOT / "data/processed/spike"
MANIFEST_COLS = ["source_id", "url", "title", "lang", "publisher", "licence_text_url", "licence_verdict",
                 "robots_ok", "fetched_at", "sha256", "parse_status", "role", "snapshot_url", "notes"]


def safe_url(u: str) -> str:
    p = urlsplit(u)
    return urlunsplit((p.scheme, p.netloc, quote(p.path, safe="/%"), p.query, ""))


def robots_ok(url: str, cache: dict) -> str:
    p = urlsplit(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in cache:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = requests.get(base + "/robots.txt", headers={"User-Agent": UA}, timeout=15)
            if r.status_code == 200 and "html" not in r.headers.get("content-type", ""):
                rp.parse(r.text.splitlines())
                cache[base] = rp
            else:  # missing / non-robots response => no restrictions published
                cache[base] = None
        except requests.RequestException:
            cache[base] = "unknown"
    rp = cache[base]
    if rp == "unknown":
        return "unknown"
    return "yes" if rp is None or rp.can_fetch(UA, url) else "no"


def decode_html(r: requests.Response) -> str:
    # requests defaults to ISO-8859-1 when charset is absent => Indic mojibake. Prefer UTF-8.
    try:
        return r.content.decode("utf-8")
    except UnicodeDecodeError:
        return r.content.decode(r.apparent_encoding or "latin-1", errors="replace")


def extract_html(raw: bytes, html: str) -> tuple[str, str, int, list[str]]:
    soup = BeautifulSoup(html, "lxml")
    title = (soup.title.get_text(strip=True) if soup.title else "")[:200]
    for t in soup(["script", "style", "noscript", "nav", "footer", "header", "form"]):
        t.decompose()
    text = "\n".join(l.strip() for l in soup.get_text("\n").splitlines() if l.strip())
    return text, title, 1, []


def extract_pdf(raw: bytes) -> tuple[str, str, int, list[str]]:
    doc = fitz.open(stream=raw, filetype="pdf")
    pages = doc.page_count
    fonts: set[str] = set()
    parts = []
    for page in doc:
        parts.append(page.get_text())
        for f in page.get_fonts():
            fonts.add(f[3])
    title = (doc.metadata or {}).get("title") or ""
    return "\n".join(parts), title[:200], pages, sorted(fonts)


OCR_PAGES = 3
OCR_LANG = {"hi": "hin+eng", "kn": "kan+eng", "en": "eng"}


def ocr_sample(raw: bytes, lang: str) -> str | None:
    """OCR the first OCR_PAGES pages with Tesseract (binary from $TESSERACT_BIN or PATH). None if unavailable."""
    tess = os.environ.get("TESSERACT_BIN") or shutil.which("tesseract")
    if not tess:
        return None
    doc = fitz.open(stream=raw, filetype="pdf")
    out = []
    for i in range(min(OCR_PAGES, doc.page_count)):
        png = doc[i].get_pixmap(dpi=300).tobytes("png")
        with tempfile.NamedTemporaryFile(suffix=".png") as tf:
            tf.write(png); tf.flush()
            res = subprocess.run([tess, tf.name, "-", "-l", OCR_LANG[lang]], capture_output=True, text=True, timeout=300)
            out.append(res.stdout)
    return "\n".join(out)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    rows, report = [], []
    rob_cache: dict = {}
    sess = requests.Session()
    sess.headers["User-Agent"] = UA
    with open(ROOT / "data/spike_candidates.csv", newline="", encoding="utf-8") as f:
        cands = list(csv.DictReader(f))
    for c in cands:
        sid, url, lang, kind = c["source_id"], safe_url(c["url"]), c["expected_lang"], c["kind"]
        row = dict.fromkeys(MANIFEST_COLS, "")
        row.update(source_id=sid, url=c["url"], lang=lang, publisher=c["publisher"], licence_verdict="unclear",
                   role="candidate", fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        rb = robots_ok(url, rob_cache)
        row["robots_ok"] = rb
        rep = {"source_id": sid, "lang": lang, "kind": kind, "robots": rb}
        if rb == "no":
            row.update(parse_status="skipped", notes="robots.txt disallows")
            rows.append(row); report.append({**rep, "status": "skipped", "reason": "robots"}); continue
        try:
            time.sleep(DELAY_S)
            r = sess.get(url, timeout=60)
            r.raise_for_status()
            raw = r.content
            row["sha256"] = hashlib.sha256(raw).hexdigest()
            (RAW / f"{sid}.{'pdf' if kind == 'pdf' else 'html'}").write_bytes(raw)
            if kind == "pdf":
                text, title, pages, fonts = extract_pdf(raw)
            else:
                text, title, pages, fonts = extract_html(raw, decode_html(r))
            (OUT / f"{sid}.txt").write_text(text, encoding="utf-8")
            m = compute_metrics(text, pages, fonts)
            status, reason = classify(m, lang, kind)
            ocr_status = ""
            if kind == "pdf" and status in ("needs_ocr", "broken_text", "legacy_font"):
                otext = ocr_sample(raw, lang)
                if otext is not None:
                    (OUT / f"{sid}.ocr.txt").write_text(otext, encoding="utf-8")
                    om = compute_metrics(otext, min(OCR_PAGES, pages))
                    ost, orr = classify(om, lang, "html")
                    ocr_status = "ocr_ok" if ost == "ok" else "ocr_poor"
                    reason += f" -> OCR({OCR_PAGES}p): {ocr_status}, script-share {max(om.dev_share, om.kan_share, om.lat_share):.2f}"
                    status = ocr_status
            row.update(title=title, parse_status=status, notes=reason)
            report.append({**rep, "status": status, "reason": reason, **m.as_dict()})
        except Exception as e:  # network/SSL/etc: record, never bypass verification
            row.update(parse_status="fetch_failed", notes=f"{type(e).__name__}: {str(e)[:120]}")
            report.append({**rep, "status": "fetch_failed", "reason": row["notes"]})
        rows.append(row)
        print(f"{sid:28s} {row['parse_status']:13s} {row['notes'][:70]}")

    with open(ROOT / "data/corpus_manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_COLS)
        w.writeheader(); w.writerows(rows)

    (ROOT / "data/spike").mkdir(exist_ok=True)
    lines = ["# Week-1 parse-feasibility report", "",
             f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC by `scripts/week1_parse_spike.py`. Metrics only (no document text).",
             "Heuristic status is NOT a quality guarantee: every `ok` still needs a human spot-check (see notes below).", "",
             "| source_id | exp. lang | kind | status | chars | pages | dev | kan | lat | latin1 | orphan marks | reason |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in report:
        g = lambda k, fmt="{:.2f}": fmt.format(r[k]) if k in r else "-"
        lines.append(f"| {r['source_id']} | {r['lang']} | {r['kind']} | {r['status']} | {g('n_chars','{}')} | {g('pages','{}')} | "
                     f"{g('dev_share')} | {g('kan_share')} | {g('lat_share')} | {g('latin1_share')} | {g('orphan_mark_rate')} | {r['reason']} |")
    (ROOT / "data/spike/report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

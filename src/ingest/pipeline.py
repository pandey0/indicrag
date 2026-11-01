"""Manifest-driven ingestion: fetch -> store raw (content-addressed) -> parse -> quality gate -> OCR fallback
-> host boilerplate removal -> write parsed text + sections -> update manifest. Idempotent and resumable."""
from __future__ import annotations

import csv
import fcntl
import json
import logging
import subprocess
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import fitz
import requests

from ..parse.boilerplate import strip_host_boilerplate
from ..parse.extract import Block, ParsedDoc, assemble, extract_html, extract_pdf, normalize
from ..parse.ocr import ocr_pdf, tesseract_path, tesseract_version
from ..parse.quality import classify, compute_metrics, layer_ocr_agreement
from .config import Config
from .fetch import Fetcher, decode_html
from .render import Renderer
from .store import (MANIFEST_COLS, raw_path, read_manifest, sha256_bytes, sha256_text, write_if_new, write_json,
                    write_manifest)

log = logging.getLogger("ingest")
PARSER_BASE = "indicrag-parse/0.2"


def parser_version(cfg: Config) -> str:
    v = f"{PARSER_BASE}+pymupdf-{fitz.VersionBind}"
    t = tesseract_path(cfg.tesseract_bin)
    return f"{v}+{tesseract_version(t).replace(' ', '-')}" if t else v


def load_sources(path: Path, only: set[str] | None = None) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if not only or r["source_id"] in only]


def _ocr_blocks(pages: list[str]) -> list[Block]:
    return [Block((f"page {i + 1}",), normalize(t), page=i + 1) for i, t in enumerate(pages) if normalize(t)]


def parse_one(raw: bytes, is_pdf: bool, lang: str, cfg: Config, use_ocr: bool = True) -> dict:
    """Return {blocks, title, pages, status, reason, ocr_used, metrics}. No network."""
    tess = tesseract_path(cfg.tesseract_bin) if use_ocr else None
    if is_pdf:
        doc, fonts = extract_pdf(raw)
        text = "\n".join(b.text for b in doc.blocks)
        m = compute_metrics(text, doc.pages, fonts)
        status, reason = classify(m, lang, "pdf")
        if status == "ok" and lang in ("hi", "kn") and tess:
            from ..parse.ocr import ocr_page_png, render_page
            pdf = fitz.open(stream=raw, filetype="pdf")   # keep a reference: pages die with their document
            layers = [pdf[i].get_text() for i in range(pdf.page_count)]
            best = max(range(len(layers)), key=lambda i: len(layers[i]))
            o = ocr_page_png(tess, render_page(raw, best), lang)
            agree = layer_ocr_agreement(layers[best], o, lang)
            if agree < cfg.agreement_threshold:
                status, reason = "broken_text", f"text layer disagrees with OCR (word overlap {agree:.2f})"
        if status in ("needs_ocr", "legacy_font", "broken_text"):
            if tess and lang in ("hi", "kn", "en"):
                pages = ocr_pdf(tess, raw, lang, cfg.ocr_max_pages, cfg.ocr_workers)
                otext = "\n".join(pages)
                om = compute_metrics(otext, len(pages))
                ost, _ = classify(om, lang, "html")
                truncated = doc.pages > cfg.ocr_max_pages
                return dict(blocks=_ocr_blocks(pages), title=doc.title, pages=doc.pages, ocr_used=True,
                            status="ocr_ok" if ost == "ok" else "ocr_poor",
                            reason=f"{reason} -> OCR {len(pages)}/{doc.pages} pages" + (" (truncated)" if truncated else ""),
                            metrics=om)
            return dict(blocks=[], title=doc.title, pages=doc.pages, ocr_used=False, status=status,
                        reason=reason + " (no OCR available)", metrics=m)
        return dict(blocks=doc.blocks, title=doc.title, pages=doc.pages, ocr_used=False, status=status, reason=reason, metrics=m)
    doc = extract_html(decode_html(raw))
    text = "\n".join(b.text for b in doc.blocks)
    m = compute_metrics(text, 1)
    status, reason = classify(m, lang, "html")
    return dict(blocks=doc.blocks, title=doc.title, pages=1, ocr_used=False, status=status, reason=reason, metrics=m)


def run(sources_path: Path, cfg: Config | None = None, only: set[str] | None = None, refresh: bool = False,
        reparse: bool = False, use_ocr: bool = True, limit: int | None = None) -> dict[str, dict]:
    cfg = cfg or Config()
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    lock = open(cfg.data_dir / ".ingest.lock", "w")   # one run at a time: the manifest is read-modify-write
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("another ingest run holds data/.ingest.lock; wait for it to finish")
    manifest = read_manifest(cfg.manifest_path)
    sources = load_sources(sources_path, only)[: limit or None]
    pv = parser_version(cfg)
    fetcher = Fetcher(cfg)
    needs_render = any(s.get("fetch") == "render" for s in sources)
    renderer = Renderer(cfg).__enter__() if needs_render else None
    parsed: dict[str, dict] = {}
    try:
        for i, s in enumerate(sources, 1):
            sid, url, lang = s["source_id"], s["url"], s["expected_lang"]
            row = manifest.get(sid, {})
            row.update(source_id=sid, url=url, lang=lang, publisher=s.get("publisher", ""), pair_id=s.get("pair_id", ""),
                       role=s.get("role") or row.get("role") or "candidate", notes=s.get("topic", ""))
            row.setdefault("licence_verdict", "unclear")
            row["redistribute"] = row.get("redistribute") or "false"   # nothing is published until a human sets this
            manifest[sid] = row
            try:
                existing = sorted((cfg.raw_dir / sid).glob("*.*")) if (cfg.raw_dir / sid).exists() else []
                known = row.get("sha256") and any(p.stem == row["sha256"] for p in existing)
                if known and not refresh:
                    rp = next(p for p in existing if p.stem == row["sha256"])
                    raw, ext = rp.read_bytes(), rp.suffix.lstrip(".")
                else:
                    rb = fetcher.robots_ok(url)
                    row["robots_ok"] = rb
                    if rb == "no":
                        row.update(parse_status="skipped_robots", notes="robots.txt disallows")
                        continue
                    if s.get("fetch") == "render":
                        raw, ext = renderer.html(url).encode("utf-8"), "html"
                    else:
                        res = fetcher.get(url)
                        raw, ext = res.content, ("pdf" if res.is_pdf else "html")
                    row["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                sha = sha256_bytes(raw)
                write_if_new(raw_path(cfg.raw_dir, sid, sha, ext), raw)
                row["sha256"] = sha
                bpath = cfg.processed_dir / sid / f"{sha}.{pv}.blocks.json"
                if bpath.exists() and not reparse:
                    c = json.loads(bpath.read_text(encoding="utf-8"))
                    c["blocks"] = [Block(tuple(b["path"]), b["text"], b.get("page")) for b in c["blocks"]]
                else:
                    c = parse_one(raw, ext == "pdf", lang, cfg, use_ocr)
                    write_json(bpath, {**{k: v for k, v in c.items() if k not in ("blocks", "metrics")},
                                       "blocks": [asdict(b) for b in c["blocks"]]})
                parsed[sid] = c
                row.update(parse_status=c["status"], title=c["title"][:200] or row.get("title", ""), pages=c["pages"],
                           ocr_used=str(c["ocr_used"]).lower(), parser_version=pv, notes=(row.get("notes", "") + " | " + c["reason"]).strip(" |"))
                log.info("%d/%d %-28s %-12s %s", i, len(sources), sid, c["status"], c["reason"][:80])
            except (requests.RequestException, ValueError, OSError, subprocess.SubprocessError) as e:   # TLS errors are recorded, never bypassed
                row.update(parse_status="fetch_failed", notes=f"{type(e).__name__}: {str(e)[:150]}")
                log.warning("%d/%d %-28s fetch_failed %s", i, len(sources), sid, str(e)[:80])
            if i % 5 == 0:
                write_manifest(cfg.manifest_path, manifest)
    finally:
        if renderer:
            renderer.__exit__(None, None, None)

    # phase 2: per-host boilerplate removal over the docs parsed in this run (+ phase 3 write outputs)
    by_host: dict[str, dict[str, list[Block]]] = defaultdict(dict)
    for sid, c in parsed.items():
        if c["blocks"]:
            by_host[urlsplit(manifest[sid]["url"]).netloc][sid] = c["blocks"]
    for host, docs in by_host.items():
        clean = strip_host_boilerplate(docs)
        for sid, blocks in clean.items():
            text, sections = assemble(blocks)
            row, c = manifest[sid], parsed[sid]
            psha = sha256_text(text)
            out = cfg.processed_dir / sid
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{psha}.txt").write_text(text, encoding="utf-8")
            secs = []
            for sec in sections:
                st = compute_metrics(text[sec.char_start:sec.char_end]).detected_lang
                secs.append({"path": sec.path, "char_start": sec.char_start, "char_end": sec.char_end, "lang": st})
            write_json(out / f"{psha}.sections.json", secs)
            row.update(parsed_sha256=psha, n_chars=len(text), text_path=str((out / f"{psha}.txt").relative_to(cfg.data_dir)))
            dropped = sum(len(b.text) for b in docs[sid]) - len(text) + len(blocks) - len(docs[sid])
            log.debug("%s: boilerplate removed %d chars", sid, -dropped)
    write_manifest(cfg.manifest_path, manifest)
    return manifest

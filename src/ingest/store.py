"""Content-addressed raw storage and manifest I/O."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

MANIFEST_COLS = [
    "source_id", "url", "title", "lang", "publisher", "pair_id", "role", "licence_text_url", "licence_verdict",
    "redistribute", "robots_ok", "fetched_at", "sha256", "parsed_sha256", "parser_version", "parse_status",
    "n_chars", "pages", "ocr_used", "text_path", "snapshot_url", "notes",
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(t: str) -> str:
    return sha256_bytes(t.encode("utf-8"))


def raw_path(raw_dir: Path, source_id: str, sha: str, ext: str) -> Path:
    return raw_dir / source_id / f"{sha}.{ext}"


def write_if_new(path: Path, data: bytes) -> bool:
    """Write bytes unless the (content-addressed) file already exists. Returns True if written."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return True


def read_manifest(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {r["source_id"]: r for r in csv.DictReader(f)}


def write_manifest(path: Path, rows: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_COLS, extrasaction="ignore")
        w.writeheader()
        for sid in sorted(rows):
            w.writerow({c: rows[sid].get(c, "") for c in MANIFEST_COLS})


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")

"""CLI: python -m src.ingest run [--sources CSV] [--only a,b] [--refresh] [--reparse] [--no-ocr] [--limit N]"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import ROOT, Config
from .pipeline import run


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m src.ingest")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="fetch + parse sources into data/raw and data/processed, update the manifest")
    r.add_argument("--sources", default=str(ROOT / "data/spike_candidates.csv"))
    r.add_argument("--only")
    r.add_argument("--refresh", action="store_true", help="re-fetch even if the raw file is already stored")
    r.add_argument("--reparse", action="store_true", help="re-parse (and re-OCR) stored raw files")
    r.add_argument("--no-ocr", action="store_true")
    r.add_argument("--limit", type=int)
    r.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO, format="%(message)s")
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    run(Path(a.sources), Config(), set(a.only.split(",")) if a.only else None, a.refresh, a.reparse, not a.no_ocr, a.limit)


if __name__ == "__main__":
    main()

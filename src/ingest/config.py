"""Shared constants and path helpers for ingestion."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USER_AGENT = "IndicRAG-research/0.1 (non-commercial research; contact: arpit242002@gmail.com)"


@dataclass
class Config:
    data_dir: Path = field(default_factory=lambda: ROOT / "data")
    host_delay_s: float = 2.0          # minimum gap between requests to the same host
    timeout_s: int = 60
    max_bytes: int = 60 * 1024 * 1024
    retries: int = 3
    ocr_max_pages: int = int(os.environ.get("OCR_MAX_PAGES", "60"))
    ocr_workers: int = int(os.environ.get("OCR_WORKERS", "4"))
    tesseract_bin: str | None = os.environ.get("TESSERACT_BIN")
    chrome_bin: str = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome")
    min_content_chars: int = 450       # post-boilerplate floor; site-chrome shells measured <= 418 chars, shortest real page ~580
    agreement_threshold: float = 0.3   # text-layer vs OCR word overlap below this => layer untrusted

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def manifest_path(self) -> Path:
        return self.data_dir / "corpus_manifest.csv"

"""Tesseract OCR for PDFs (image-only, garbage text layer, or corrupted glyph map)."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

import fitz

LANGS = {"hi": "hin+eng", "kn": "kan+eng", "en": "eng"}


def tesseract_path(explicit: str | None) -> str | None:
    return explicit or shutil.which("tesseract")


def tesseract_version(binary: str) -> str:
    try:
        out = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).splitlines()[0].strip()
    except Exception:
        return "tesseract-unknown"


def ocr_page_png(binary: str, png: bytes, lang: str, timeout: int = 300) -> str:
    with tempfile.NamedTemporaryFile(suffix=".png") as tf:
        tf.write(png)
        tf.flush()
        try:
            res = subprocess.run([binary, tf.name, "-", "-l", LANGS[lang], "--psm", "3"], capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:   # one stuck page must not kill the whole run; page is left empty
            return ""
        return res.stdout


def render_page(raw: bytes, index: int, dpi: int = 300) -> bytes:
    doc = fitz.open(stream=raw, filetype="pdf")
    return doc[index].get_pixmap(dpi=dpi).tobytes("png")


def ocr_pdf(binary: str, raw: bytes, lang: str, max_pages: int, workers: int = 4) -> list[str]:
    """OCR up to max_pages pages. Pages are rendered in the parent (PyMuPDF is not thread-safe) and OCR'd in parallel."""
    n = min(fitz.open(stream=raw, filetype="pdf").page_count, max_pages)
    pngs = [render_page(raw, i) for i in range(n)]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(lambda p: ocr_page_png(binary, p, lang), pngs))

"""Cross-document boilerplate removal: drop short non-heading blocks repeated across nearly all pages of a host.

Deliberately conservative (>=5 docs, >=80% of docs, headings protected, never removes >60% of a page): scheme pages
built from one template legitimately repeat headings and list items, and over-stripping would delete real content.
The primary boilerplate defence is semantic: nav/footer/aside and boilerplate class names are dropped in extract_html.
"""
from __future__ import annotations

from collections import Counter

from .extract import Block


def _key(b: Block) -> str:
    return " ".join(b.text.split()).lower()


def _is_heading(b: Block) -> bool:
    # headings shared across template-based pages (e.g. 'Eligibility') are structure, not boilerplate
    return bool(b.path) and b.text == b.path[-1]


def strip_host_boilerplate(docs: dict[str, list[Block]], min_docs: int = 5, frac: float = 0.8, max_len: int = 300, max_removed: float = 0.6) -> dict[str, list[Block]]:
    """docs: source_id -> blocks for ONE host. Returns filtered copy. Short blocks that occur in >= frac of docs are removed."""
    if len(docs) < min_docs:
        return docs
    df: Counter[str] = Counter()
    for blocks in docs.values():
        for k in {_key(b) for b in blocks if len(b.text) <= max_len and not _is_heading(b)}:
            df[k] += 1
    cutoff = max(2, int(frac * len(docs) + 0.999))
    out = {}
    for sid, blocks in docs.items():
        kept = [b for b in blocks if _is_heading(b) or not (len(b.text) <= max_len and df[_key(b)] >= cutoff)]
        total, left = sum(len(b.text) for b in blocks), sum(len(b.text) for b in kept)
        # safeguard: template-identical pages share most content legitimately; do not gut them
        out[sid] = kept if total == 0 or left / total >= 1 - max_removed else blocks
    return out

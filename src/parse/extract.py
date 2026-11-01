"""Turn fetched HTML/PDF bytes into structured blocks (heading path + text), then assemble into text + sections."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import fitz  # PyMuPDF
from bs4 import BeautifulSoup, Comment, Doctype, NavigableString, Tag

HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
DROP_TAGS = ["script", "style", "noscript", "svg", "iframe", "nav", "footer", "aside", "form", "button", "select", "option"]
BOILER_ATTR = re.compile(r"(^|[\s_-])(nav|navbar|menu|footer|breadcrumb|sidebar|cookie|accessib|skip|social|sitemap|"
                         r"font-?size|screen-?reader|language-?switch|lang-?select|modal|popup|toolbar)([\s_-]|$)", re.I)


@dataclass
class Block:
    path: tuple[str, ...]      # heading path, e.g. ("Eligibility", "Documents")
    text: str
    page: int | None = None


@dataclass
class ParsedDoc:
    title: str = ""
    blocks: list[Block] = field(default_factory=list)
    pages: int = 1
    fonts: list[str] = field(default_factory=list)
    kind: str = "html"


def normalize(text: str) -> str:
    """NFC, unify newlines, collapse spaces, drop control chars; keep ZWJ/ZWNJ (meaningful in Indic scripts)."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    text = "".join(c for c in text if c in "\n\t" or c in "‌‍" or unicodedata.category(c)[0] != "C")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _is_boiler(tag: Tag) -> bool:
    attrs = tag.attrs or {}
    cls = " ".join(attrs.get("class", [])) if isinstance(attrs.get("class"), list) else str(attrs.get("class", ""))
    ident = f"{cls} {attrs.get('id', '')} {attrs.get('role', '')}"
    if tag.get("role") in ("navigation", "banner", "contentinfo", "complementary", "search"):
        return True
    toks = set(cls.split())
    # full-viewport overlays (Tailwind modals/backdrops) hold dialog text, not page content
    if {"h-screen", "w-screen"} <= toks or ("fixed" in toks and "inset-0" in toks):
        return True
    return bool(BOILER_ATTR.search(ident))


INLINE_TAGS = {"a", "span", "b", "i", "strong", "em", "small", "sup", "sub", "u", "abbr", "font", "code", "mark",
               "label", "cite", "q", "time", "bdi", "bdo", "wbr", "s", "del", "ins"}


def extract_html(html: str) -> ParsedDoc:
    soup = BeautifulSoup(html, "lxml")
    title = normalize(soup.title.get_text(" ", strip=True)) if soup.title else ""
    for t in soup(DROP_TAGS):
        t.decompose()
    for t in list(soup.find_all(True)):
        if t.attrs is not None and t.name not in ("html", "body") and _is_boiler(t):
            t.decompose()
    main = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.find("article")
    root = main if main and len(main.get_text(strip=True)) > 400 else (soup.body or soup)

    blocks: list[Block] = []
    stack: list[tuple[int, str]] = []
    buf: list[str] = []

    def flush() -> None:
        txt = normalize(" ".join(buf))
        buf.clear()
        if txt:
            blocks.append(Block(tuple(t for _, t in stack), txt))

    def walk(el: Tag) -> None:
        for ch in el.children:
            if isinstance(ch, NavigableString):
                if not isinstance(ch, (Comment, Doctype)):
                    buf.append(str(ch))
            elif isinstance(ch, Tag):
                if ch.name in HEADINGS:
                    flush()
                    htxt = normalize(ch.get_text(" ", strip=True))
                    if htxt:
                        lvl = HEADINGS[ch.name]
                        while stack and stack[-1][0] >= lvl:
                            stack.pop()
                        stack.append((lvl, htxt))
                        blocks.append(Block(tuple(t for _, t in stack), htxt))
                elif ch.name == "br":
                    buf.append(" ")
                elif ch.name in INLINE_TAGS:
                    walk(ch)
                else:
                    flush()
                    walk(ch)
                    flush()

    walk(root)
    flush()
    return ParsedDoc(title=title, blocks=_merge_headings(blocks), pages=1, kind="html")


def _merge_headings(blocks: list[Block]) -> list[Block]:
    """Heading text appears both as stack entry and as its own block: keep it (it is real content), dedupe repeats."""
    out: list[Block] = []
    for b in blocks:
        if out and out[-1].text == b.text and out[-1].path == b.path:
            continue
        out.append(b)
    return out


def extract_pdf(raw: bytes) -> tuple[ParsedDoc, list[str]]:
    doc = fitz.open(stream=raw, filetype="pdf")
    fonts: set[str] = set()
    blocks: list[Block] = []
    for i, page in enumerate(doc):
        for f in page.get_fonts():
            fonts.add(f[3])
        txt = normalize(page.get_text())
        if txt:
            blocks.append(Block((f"page {i + 1}",), txt, page=i + 1))
    title = (doc.metadata or {}).get("title") or ""
    return ParsedDoc(title=normalize(title), blocks=blocks, pages=doc.page_count, fonts=sorted(fonts), kind="pdf"), sorted(fonts)


@dataclass
class Section:
    path: str
    char_start: int
    char_end: int


def assemble(blocks: list[Block]) -> tuple[str, list[Section]]:
    """Join blocks with newlines; sections are maximal runs of blocks sharing a heading path. Offsets index the text."""
    parts: list[str] = []
    sections: list[Section] = []
    pos = 0
    for b in blocks:
        path = " > ".join(b.path)
        start = pos
        parts.append(b.text)
        pos += len(b.text)
        if sections and sections[-1].path == path:
            sections[-1].char_end = pos
        else:
            sections.append(Section(path, start, pos))
        parts.append("\n")
        pos += 1
    return "".join(parts).rstrip("\n"), sections

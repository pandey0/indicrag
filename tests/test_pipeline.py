import csv
import functools
import http.server
import threading
from pathlib import Path

import fitz
import pytest

from src.ingest.config import Config
from src.ingest.pipeline import run
from src.ingest.store import read_manifest
from src.parse.boilerplate import strip_host_boilerplate
from src.parse.extract import Block, assemble, extract_html

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture()
def site(tmp_path):
    web = tmp_path / "web"
    (web / "private").mkdir(parents=True)
    page = (FIX / "page.html").read_text(encoding="utf-8")
    for i in range(5):  # 5 pages sharing the same sidebar-less boilerplate paragraph
        (web / f"p{i}.html").write_text(
            page.replace("आवेदन ऑनलाइन करें।", f"आवेदन ऑनलाइन करें। पृष्ठ {i}").replace(
                "</main>", f"<p>Common footer text appears everywhere</p><p>{'अनूठा विवरण संख्या ' * 40}{i} {'योजना' * 30}</p></main>"),
            encoding="utf-8")
    (web / "private" / "secret.html").write_text(page, encoding="utf-8")
    (web / "robots.txt").write_text("User-agent: *\nDisallow: /private/\n")
    doc = fitz.open()
    pg = doc.new_page()
    for i in range(4):
        pg.insert_text((50, 72 + 14 * i), "Right to Information Act allows every citizen to request information from authorities.", fontsize=9)
    pg.insert_text((50, 140), "Fees are Rs 10 per application.", fontsize=9)
    (web / "doc.pdf").write_bytes(doc.tobytes())
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(web))
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}", tmp_path
    srv.shutdown()


def write_sources(path: Path, base: str, ids: list[tuple[str, str, str]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source_id", "url", "expected_lang", "kind", "publisher", "topic"])
        for sid, rel, lang in ids:
            w.writerow([sid, f"{base}/{rel}", lang, "html", "test", "t"])


def cfg_for(tmp: Path) -> Config:
    return Config(data_dir=tmp / "data", host_delay_s=0.0, tesseract_bin="/nonexistent", min_content_chars=0)


def test_end_to_end_idempotent_and_robots(site):
    base, tmp = site
    src = tmp / "sources.csv"
    write_sources(src, base, [("a", "p0.html", "hi"), ("b", "p1.html", "hi"), ("c", "p2.html", "hi"), ("g", "p3.html", "hi"), ("h", "p4.html", "hi"),
                              ("d", "doc.pdf", "en"), ("e", "private/secret.html", "hi"), ("f", "missing.html", "hi")])
    cfg = cfg_for(tmp)
    m = run(src, cfg, use_ocr=False)
    assert m["a"]["parse_status"] == "ok" and m["d"]["parse_status"] == "ok"
    assert m["e"]["parse_status"] == "skipped_robots"
    assert m["f"]["parse_status"] == "fetch_failed"
    assert m["a"]["redistribute"] == "false"
    text = (cfg.data_dir / m["a"]["text_path"]).read_text(encoding="utf-8")
    assert "पात्रता" in text and "Home" not in text and "©" not in text      # heading kept; nav/footer removed
    assert "Common footer text" not in text                                     # repeated across all 5 docs => boilerplate
    assert "Fees are Rs 10" in (cfg.data_dir / m["d"]["text_path"]).read_text(encoding="utf-8")
    raws = {p.name for p in (cfg.raw_dir / "a").iterdir()}
    m2 = run(src, cfg, use_ocr=False)                                            # second run: no new files, same hashes
    assert {p.name for p in (cfg.raw_dir / "a").iterdir()} == raws
    assert m2["a"]["parsed_sha256"] == m["a"]["parsed_sha256"]
    assert read_manifest(cfg.manifest_path)["a"]["sha256"] == m["a"]["sha256"]


def test_sections_offsets_index_text():
    d = extract_html((FIX / "page.html").read_text(encoding="utf-8"))
    text, secs = assemble(d.blocks)
    assert secs[0].path == "पेंशन योजना"
    assert text[secs[1].char_start:secs[1].char_end].startswith("पात्रता")
    assert [s.path for s in secs][-1].endswith("नोट")


def test_boilerplate_requires_enough_docs():
    docs = {f"d{i}": [Block(("h",), "Same menu"), Block(("h",), f"unique {i}")] for i in range(3)}
    assert strip_host_boilerplate(docs) == docs                                  # < min_docs: untouched
    docs = {f"d{i}": [Block(("h",), "Same menu"), Block(("h",), f"unique {i}")] for i in range(6)}
    out = strip_host_boilerplate(docs)
    assert all(len(v) == 1 and v[0].text.startswith("unique") for v in out.values())


def test_boilerplate_safeguard_keeps_template_identical_pages():
    docs = {f"d{i}": [Block(("h",), "Shared line one"), Block(("h",), "Shared line two"), Block(("h",), f"u{i}")] for i in range(6)}
    out = strip_host_boilerplate(docs)
    assert out == docs   # would remove >60% of every page => left untouched


def test_shared_headings_are_protected():
    docs = {f"d{i}": [Block(("Eligibility",), "Eligibility"), Block(("Eligibility",), f"unique content number {i} " * 6)] for i in range(6)}
    out = strip_host_boilerplate(docs)
    assert all(any(b.text == "Eligibility" for b in v) for v in out.values())


def test_shell_page_fails_after_boilerplate_gate(site):
    base, tmp = site
    src = tmp / "sources.csv"
    write_sources(src, base, [("a", "p0.html", "hi")])
    cfg = cfg_for(tmp)
    cfg.min_content_chars = 10_000                   # page text is far below the floor: treated as an empty shell
    m = run(src, cfg, use_ocr=False)
    assert m["a"]["parse_status"] == "fail" and "empty shell" in m["a"]["notes"]
    cfg2 = cfg_for(tmp)
    cfg2.min_content_chars = 5                        # same page passes with a sane floor
    assert run(src, cfg2, use_ocr=False)["a"]["parse_status"] == "ok"

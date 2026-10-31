"""Enumerate myScheme scheme slugs by paging through the client-rendered /search listing (10 schemes/page).

python -m src.ingest.discover_myscheme --pages 30 --out data/sources_myscheme.csv
robots.txt allows crawling; we page politely (>=2s between page turns).
"""
from __future__ import annotations

import argparse
import csv
import re
import time

from .config import USER_AGENT, Config

BASE = "https://www.myscheme.gov.in"


def discover(pages: int, cfg: Config) -> list[str]:
    from playwright.sync_api import sync_playwright

    slugs: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=cfg.chrome_bin, args=["--no-sandbox"])
        pg = b.new_context(user_agent=USER_AGENT).new_page()
        pg.goto(f"{BASE}/search", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(2500)
        for n in range(1, pages + 1):
            hrefs = pg.eval_on_selector_all("a[href*='/schemes/']", "e=>e.map(x=>x.getAttribute('href'))")
            for h in hrefs:
                m = re.search(r"/schemes/([^/?#]+)", h)
                if m and m.group(1) not in slugs:
                    slugs.append(m.group(1))
            if n == pages:
                break
            nxt = pg.evaluate_handle(
                """(t)=>[...document.querySelectorAll('li')].find(e=>e.innerText.trim()===String(t))""", n + 1)
            el = nxt.as_element()
            if el is None:   # next number not shown: jump to the largest visible page number, then continue
                nums = pg.evaluate("""()=>[...document.querySelectorAll('li')].map(e=>e.innerText.trim()).filter(t=>/^\\d+$/.test(t)).map(Number)""")
                if not nums or max(nums) <= n:
                    break
                el = pg.evaluate_handle("""(t)=>[...document.querySelectorAll('li')].find(e=>e.innerText.trim()===String(t))""", max(nums)).as_element()
            el.click()
            time.sleep(cfg.host_delay_s)
            pg.wait_for_timeout(1500)
        b.close()
    return slugs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=30)
    ap.add_argument("--out", default="data/sources_myscheme.csv")
    a = ap.parse_args()
    slugs = discover(a.pages, Config())
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source_id", "url", "expected_lang", "kind", "publisher", "topic", "fetch", "role"])
        for s in slugs:
            w.writerow([f"ms_{s}", f"{BASE}/schemes/{s}", "en", "html", "MeitY myScheme", "scheme page", "render", "candidate"])
    print(f"{len(slugs)} schemes -> {a.out}")


if __name__ == "__main__":
    main()

"""Headless-browser fetch for JavaScript-rendered pages (e.g. myScheme). Uses system Chrome via Playwright."""
from __future__ import annotations

import time
from urllib.parse import urlsplit

from .config import USER_AGENT, Config


class Renderer:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._pw = None
        self._browser = None
        self._ctx = None
        self._last: dict[str, float] = {}

    def __enter__(self) -> Renderer:
        from playwright.sync_api import sync_playwright  # optional dependency

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(executable_path=self.cfg.chrome_bin, args=["--no-sandbox"])
        self._ctx = self._browser.new_context(user_agent=USER_AGENT)
        return self

    def __exit__(self, *exc) -> None:
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def html(self, url: str, wait_selector: str | None = "main", settle_ms: int = 1500) -> str:
        host = urlsplit(url).netloc
        gap = time.monotonic() - self._last.get(host, 0.0)
        if gap < self.cfg.host_delay_s:
            time.sleep(self.cfg.host_delay_s - gap)
        self._last[host] = time.monotonic()
        page = self._ctx.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=self.cfg.timeout_s * 1000)
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=10000)
                except Exception:
                    pass
            try:   # the app shell exists before data loads: wait until a heading actually has text
                page.wait_for_function("() => [...document.querySelectorAll('h1')].some(h => h.innerText.trim().length > 0)", timeout=20000)
            except Exception:
                pass
            page.wait_for_timeout(settle_ms)
            return page.content()
        finally:
            page.close()

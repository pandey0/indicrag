"""Polite HTTP fetching: robots.txt, per-host rate limit, retries, size cap. Never disables TLS verification."""
from __future__ import annotations

import time
import urllib.robotparser
from dataclasses import dataclass
from urllib.parse import quote, urlsplit, urlunsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import USER_AGENT, Config


@dataclass
class FetchResult:
    url: str
    final_url: str
    status: int
    content: bytes
    content_type: str

    @property
    def is_pdf(self) -> bool:
        return "pdf" in self.content_type.lower() or self.content[:5] == b"%PDF-"


def safe_url(u: str) -> str:
    p = urlsplit(u)
    return urlunsplit((p.scheme, p.netloc, quote(p.path, safe="/%"), p.query, ""))


class Fetcher:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.sess = requests.Session()
        self.sess.headers["User-Agent"] = USER_AGENT
        retry = Retry(total=cfg.retries, backoff_factor=1.5, status_forcelist=(429, 500, 502, 503, 504),
                      respect_retry_after_header=True, allowed_methods=("GET", "HEAD"))
        self.sess.mount("https://", HTTPAdapter(max_retries=retry))
        self.sess.mount("http://", HTTPAdapter(max_retries=retry))
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None | str] = {}
        self._last: dict[str, float] = {}

    def _wait(self, host: str) -> None:
        gap = time.monotonic() - self._last.get(host, 0.0)
        if gap < self.cfg.host_delay_s:
            time.sleep(self.cfg.host_delay_s - gap)
        self._last[host] = time.monotonic()

    def robots_ok(self, url: str) -> str:
        """'yes' | 'no' | 'unknown'. A missing robots.txt (404/HTML) means no published restriction."""
        p = urlsplit(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self._robots:
            try:
                self._wait(p.netloc)
                r = self.sess.get(base + "/robots.txt", timeout=20)
                if r.status_code == 200 and "html" not in r.headers.get("content-type", "").lower():
                    rp = urllib.robotparser.RobotFileParser()
                    rp.parse(r.text.splitlines())
                    self._robots[base] = rp
                else:
                    self._robots[base] = None
            except requests.RequestException:
                self._robots[base] = "unknown"
        rp = self._robots[base]
        if rp == "unknown":
            return "unknown"
        return "yes" if rp is None or rp.can_fetch(USER_AGENT, url) else "no"

    def get(self, url: str) -> FetchResult:
        url = safe_url(url)
        self._wait(urlsplit(url).netloc)
        with self.sess.get(url, timeout=self.cfg.timeout_s, stream=True) as r:
            r.raise_for_status()
            buf = bytearray()
            for chunk in r.iter_content(1 << 16):
                buf += chunk
                if len(buf) > self.cfg.max_bytes:
                    raise ValueError(f"response exceeds {self.cfg.max_bytes} bytes")
            return FetchResult(url, r.url, r.status_code, bytes(buf), r.headers.get("content-type", ""))


def decode_html(content: bytes, fallback: str = "latin-1") -> str:
    """Prefer UTF-8: `requests` falls back to ISO-8859-1 when no charset is declared, which garbles Indic text."""
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode(fallback, errors="replace")

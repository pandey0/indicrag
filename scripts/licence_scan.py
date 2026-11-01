#!/usr/bin/env python3
"""Find and extract copyright/terms clauses for each publisher in the manifest.

Writes data/licence_review/scan.json (clauses + source URLs). Verdicts are NOT decided here:
a human reviews the clauses and records allow/deny/unclear in data/licence_review/verdicts.csv.
"""
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
UA = "IndicRAG-research-spike/0.1 (contact: arpit242002@gmail.com)"
SITES = {
    "rti.gov.in": ["https://rti.gov.in/"],
    "ahara.karnataka.gov.in": ["https://ahara.karnataka.gov.in/"],
    "sevasindhu.karnataka.gov.in": ["https://sevasindhu.karnataka.gov.in/"],
    "ceg.karnataka.gov.in": ["https://ceg.karnataka.gov.in/"],
    "schooleducation.karnataka.gov.in": ["https://schooleducation.karnataka.gov.in/"],
    "nfsa.gov.in": ["https://nfsa.gov.in/"],
    "scholarships.gov.in": ["https://scholarships.gov.in/"],
    "serviceonline.bihar.gov.in": ["https://serviceonline.bihar.gov.in/"],
    "www.mygov.in": ["https://www.mygov.in/"],
    "www.myscheme.gov.in": ["https://www.myscheme.gov.in/copyright-policy", "https://www.myscheme.gov.in/terms-conditions", "https://www.myscheme.gov.in/disclaimer"],
}
POLICY = re.compile(r"copyright|terms|disclaimer|policy|policies|conditions|content|नियम|शर्त|अस्वीकरण|ನಿಯಮ|ಹಕ್ಕುಸ್ವಾಮ್ಯ|ಷರತ್ತು|ಹಕ್ಕು ನಿರಾಕರಣೆ", re.I)
KEY = re.compile(r"reproduc|copyright|licen[cs]e|permission|commercial|redistribut|republish|derivative|attribution|acknowledg|source|third.party|prohibit|without (the )?prior|पुनर्प्रस्तुत|अनुमति|कॉपीराइट|ಪುನರುತ್ಪಾದ|ಅನುಮತಿ", re.I)
LINKTXT = re.compile(r"copyright|terms|disclaimer|content polic|website polic|policies|hyperlink|नियम|शर्त|अस्वीकरण|ಹಕ್ಕು ನಿರಾಕರಣೆ|ನಿಯಮ", re.I)

def text_of(html):
    s = BeautifulSoup(html, "lxml")
    for t in s(["script", "style", "noscript"]): t.decompose()
    return s, " ".join(s.get_text(" ", strip=True).split())

def clauses(txt):
    sents = re.split(r"(?<=[.!?।])\s+", txt)
    return [s[:400] for s in sents if KEY.search(s) and 40 < len(s) < 600][:12]

out = {}
for host, seeds in SITES.items():
    pages, urls = [], []
    for u in seeds:
        try:
            r = requests.get(u, headers={"User-Agent": UA}, timeout=25); time.sleep(1.5)
            s, _ = text_of(r.content.decode("utf-8", "replace"))
            urls.append((u, r.content.decode("utf-8", "replace")))
            if len(seeds) == 1:  # discover policy links from the home page
                found = {}
                for a in s.find_all("a", href=True):
                    t = a.get_text(" ", strip=True)
                    h = urljoin(u, a["href"])
                    if LINKTXT.search(t) and urlsplit(h).netloc.endswith(host.replace("www.", "")) and h not in found:
                        found[h] = t[:60]
                for h, t in list(found.items())[:4]:
                    try:
                        rr = requests.get(h, headers={"User-Agent": UA}, timeout=25); time.sleep(1.5)
                        if rr.ok and "html" in rr.headers.get("content-type", ""): urls.append((h, rr.content.decode("utf-8", "replace")))
                    except requests.RequestException: pass
        except requests.RequestException:
            urls.append((u, ""))
    for u, html in urls[1:] if len(seeds) == 1 else urls:
        if not html: continue
        _, txt = text_of(html)
        c = clauses(txt)
        if c: pages.append({"url": u, "clauses": c})
    # also look at the footer/home page for inline copyright statements
    if len(seeds) == 1 and urls and urls[0][1]:
        _, txt = text_of(urls[0][1]); c = [x for x in clauses(txt) if re.search("copyright|reproduc|©|licen", x, re.I)][:4]
        if c: pages.append({"url": seeds[0] + " (home page)", "clauses": c})
    out[host] = pages
    print(host, [p["url"] for p in pages])
(ROOT / "data/licence_review").mkdir(exist_ok=True)
json.dump(out, open(ROOT / "data/licence_review/scan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

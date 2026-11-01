"""Map English topic titles to their Hindi/Kannada Wikipedia articles via interlanguage links.

Writes data/sources_wikipedia.csv (pipeline format). Serial, UA-identified API calls (Wikimedia API etiquette).
Content is CC BY-SA 4.0: attribute and share-alike if redistributed (docs/03).
"""
from __future__ import annotations

import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "IndicRAG-research/0.1 (non-commercial research benchmark)"
TOPICS = [
    "Right to Information Act, 2005", "Pradhan Mantri Kisan Samman Nidhi", "Ayushman Bharat", "Mahatma Gandhi National Rural Employment Guarantee Act, 2005",
    "Aadhaar", "Ration card (India)", "National Food Security Act, 2013", "Permanent account number", "Voter ID (India)", "Pradhan Mantri Jan Dhan Yojana",
    "Pradhan Mantri Ujjwala Yojana", "Swachh Bharat Mission", "Pradhan Mantri Awas Yojana", "DigiLocker", "UMANG (app)", "Sukanya Samriddhi Yojana",
    "Atal Pension Yojana", "Pradhan Mantri Mudra Yojana", "Beti Bachao, Beti Padhao", "National Pension System", "Employees' Provident Fund Organisation",
    "Consumer Protection Act, 2019", "Driving licence in India", "Indian passport", "Gram panchayat", "E-Shram", "Janani Suraksha Yojana", "Midday Meal Scheme",
    "Samagra Shiksha", "Anna Bhagya", "Gruha Lakshmi Scheme", "Gruha Jyothi", "Shakti (Karnataka scheme)", "Public distribution system (India)",
    "Pradhan Mantri Fasal Bima Yojana", "Kisan Credit Card", "National Social Assistance Programme", "Jan Aushadhi", "Pradhan Mantri Garib Kalyan Anna Yojana",
    "Unified Payments Interface", "Common Service Centres", "Digital India", "Pradhan Mantri Suraksha Bima Yojana", "Pradhan Mantri Jeevan Jyoti Bima Yojana",
    "Mission Indradhanush", "Integrated Child Development Services", "National Scholarship Portal", "Stand-Up India", "Pradhan Mantri Matru Vandana Yojana",
    "Old age pension in India",
]


def api(**p):
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"format": "json", "formatversion": 2, **p})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == 5:
                raise
            wait = int(e.headers.get("Retry-After", 0) or 0) or 10 * 2 ** attempt
            print(f"HTTP {e.code}, backing off {wait}s", file=sys.stderr)
            time.sleep(wait)


def main(out="data/sources_wikipedia.csv"):
    rows = []
    for t in TOPICS:
        d = api(action="query", titles=t, prop="langlinks", lllimit="max", redirects=1)
        pg = d["query"]["pages"][0]
        if pg.get("missing"):
            print("missing", t, file=sys.stderr); continue
        links = {l["lang"]: l["title"] for l in pg.get("langlinks", []) if l["lang"] in ("hi", "kn")}
        pid = "wp_" + "".join(c if c.isalnum() else "_" for c in pg["title"].lower())[:40].strip("_")
        for lang, title in [("en", pg["title"])] + sorted(links.items()):
            url = f"https://{lang}.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
            rows.append({"source_id": f"{pid}_{lang}", "url": url, "expected_lang": lang, "kind": "html",
                         "publisher": f"Wikipedia ({lang}) CC BY-SA 4.0", "topic": title, "fetch": "", "pair_id": pid})
        print(t, "->", sorted(links), file=sys.stderr)
        time.sleep(3.0)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("rows", len(rows), "hi", sum(r["expected_lang"] == "hi" for r in rows), "kn", sum(r["expected_lang"] == "kn" for r in rows))


if __name__ == "__main__":
    main()

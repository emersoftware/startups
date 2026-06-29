"""Pivot detection via month-to-month variation of the landing page (Wayback).

METHODOLOGY
-----------
1. For a domain, we take its monthly snapshots archived in
   data/wayback/<domain>/YYYYMM.html (full HTML of each month).
2. From each month we extract the VISIBLE TEXT (no script/style/svg).
3. We vectorize all months with TF-IDF (uni+bigrams). TF-IDF makes the stable
   boilerplate (nav, footer, cookies) have low IDF and weigh little: what
   matters are the words that DISTINGUISH one month from another (the pitch).
4. We measure the COSINE SIMILARITY between month_i and month_{i+1}.
   VARIATION = 1 - sim. (same family as matching similar transactions:
   vectorize and compare by cosine.)
5. The months with the highest variation = PIVOT CANDIDATES. We flag the peaks
   (variation > mean + k·std) to later review them by hand (what changed and
   whether it's a pivot or just a redesign/wording change).
6. In parallel we serialize the timeline of TITLES/H1 (rebranding) to read the
   evolution of the message and corroborate.

Usage:  uv run python pivot_detect.py blar.io
Output: prints the analysis; saves data/pivots/<domain>.json
"""

from __future__ import annotations

import glob
import json
import re
import sys

import numpy as np
from selectolax.parser import HTMLParser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import common

MES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]


def month_label(ym: str) -> str:
    return f"{MES[int(ym[4:6]) - 1]}-{ym[:4]}"


def visible_text(html: str) -> str:
    tree = HTMLParser(html)
    for sel in ("script", "style", "noscript", "svg"):
        for n in tree.css(sel):
            n.decompose()
    body = tree.body or tree
    txt = body.text(separator=" ") if body else ""
    return re.sub(r"\s+", " ", txt).strip().lower()


def page_title(html: str) -> str:
    t = HTMLParser(html).css_first("title")
    return " ".join(t.text().split())[:90] if t else ""


def page_h1(html: str) -> str:
    h = HTMLParser(html).css_first("h1")
    return " ".join(h.text().split())[:90] if h else ""


def analyze(domain: str) -> dict:
    files = sorted(glob.glob(str(common.DATA_DIR / "wayback" / domain / "*.html")))
    months = [(re.search(r"(\d{6})\.html$", f).group(1), f) for f in files]
    if len(months) < 2:
        raise SystemExit(f"{domain}: se necesitan ≥2 meses (hay {len(months)}).")

    htmls = [open(f, encoding="utf-8", errors="replace").read() for _, f in months]
    docs = [visible_text(h) for h in htmls]
    titles = [page_title(h) for h in htmls]
    h1s = [page_h1(h) for h in htmls]
    ym = [m for m, _ in months]

    # TF-IDF + cosine between consecutive months
    vec = TfidfVectorizer(ngram_range=(1, 2), max_features=6000, min_df=1, sublinear_tf=True)
    X = vec.fit_transform(docs)
    variation = [0.0] + [
        round(1 - float(cosine_similarity(X[i - 1], X[i])[0, 0]), 4)
        for i in range(1, len(docs))
    ]

    v = np.array(variation[1:])
    thr = float(v.mean() + 1.0 * v.std())  # peak threshold

    rows = []
    for i, m in enumerate(ym):
        title_changed = i > 0 and titles[i] != titles[i - 1]
        rows.append({
            "month": m, "label": month_label(m),
            "variation": variation[i],
            "title": titles[i], "h1": h1s[i],
            "title_changed": title_changed,
            "is_peak": i > 0 and variation[i] >= thr,
        })

    peaks = sorted([r for r in rows if r["is_peak"]], key=lambda r: -r["variation"])
    return {"domain": domain, "months": len(months), "threshold": round(thr, 4),
            "rows": rows, "candidates": peaks}


def main() -> None:
    domain = (sys.argv[1] if len(sys.argv) > 1 else "blar.io").replace("https://", "").strip("/")
    res = analyze(domain)

    print(f"=== {domain} · {res['months']} meses · umbral pico={res['threshold']} ===\n")
    print(f"{'mes':>9}  {'variación':>9}  {'Δtítulo':>7}  título")
    prev = None
    for r in res["rows"]:
        bar = "█" * int(r["variation"] * 40)
        flag = "PICO" if r["is_peak"] else ("·" if r["title_changed"] else "")
        show_title = r["title"] if r["title"] != prev else ""
        print(f"{r['label']:>9}  {r['variation']:>9.3f}  {flag:>7}  {bar} {show_title}")
        prev = r["title"]

    print("\n--- CANDIDATOS A PIVOTE (mayor variación) ---")
    for c in res["candidates"]:
        print(f"  {c['label']}  variación {c['variation']:.3f}")
        print(f"      título: {c['title']}")
        if c["h1"]:
            print(f"      h1    : {c['h1']}")

    out = common.DATA_DIR / "pivots"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{domain}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ guardado en data/pivots/{domain}.json")


if __name__ == "__main__":
    main()

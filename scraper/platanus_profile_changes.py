"""Change heuristic (month-to-month TF-IDF variation) over the FULL CONTENT
of the Platanus profiles of ALL startups.

Unlike platanus_profile_evolution.py (which only looks at the <title>), here we
vectorize the visible text of the profile (name, slogan, description, founders,
bios) and measure variation = 1 - cosine between consecutive months. The months
with the highest variation = big changes in how the startup describes itself =
pivot/rebrand candidates (first-hand signal: they edit it themselves).

Usage:  uv run python scraper/platanus_profile_changes.py [--all|<slug>]
Output: data/pivots/profile_<slug>.json + data/pivots/_profile_changes.json
"""
from __future__ import annotations
import glob, json, os, re, sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import common
from pivot_detect import visible_text, page_title, month_label

DIR = common.DATA_DIR / "wayback_platanus"
# Platanus site boilerplate that appears in every profile (filtered out)
NAV = re.compile(r"\b(home|program|portfolio|team|blog|demo day|hack|kernel|apply|"
                 r"founders?|website|platanus)\b", re.I)


def profile_text(html: str) -> str:
    t = visible_text(html)
    # remove the repeated navigation prefix to reduce noise
    return NAV.sub(" ", t)


def analyze(slug: str) -> dict:
    files = sorted(glob.glob(str(DIR / slug / "*.html")))
    months = [(re.search(r"(\d{6})\.html$", f).group(1), f) for f in files
              if re.search(r"(\d{6})\.html$", f)]
    if len(months) < 2:
        return {"slug": slug, "months": len(months), "rows": [], "candidates": []}

    htmls = [open(f, encoding="utf-8", errors="replace").read() for _, f in months]
    docs = [profile_text(h) for h in htmls]
    titles = [page_title(h) for h in htmls]
    ym = [m for m, _ in months]
    if sum(1 for d in docs if len(d.split()) >= 5) < 2:
        return {"slug": slug, "months": len(months), "rows": [], "candidates": [],
                "note": "texto insuficiente"}

    vec = TfidfVectorizer(ngram_range=(1, 2), max_features=6000, min_df=1, sublinear_tf=True)
    try:
        X = vec.fit_transform(docs)
    except ValueError:
        return {"slug": slug, "months": len(months), "rows": [], "candidates": []}
    variation = [0.0] + [round(1 - float(cosine_similarity(X[i-1], X[i])[0, 0]), 4)
                         for i in range(1, len(docs))]
    v = np.array(variation[1:])
    thr = float(v.mean() + 1.0 * v.std()) if len(v) else 1.0

    # wayback urls from the manifest
    mf = DIR / slug / "manifest.json"
    url_by_month = {}
    if mf.exists():
        for s in json.loads(mf.read_text(encoding="utf-8")).get("snapshots", []):
            url_by_month[s["timestamp"][:6]] = s.get("wayback_url")

    rows = []
    for i, m in enumerate(ym):
        rows.append({"month": m, "label": month_label(m), "variation": variation[i],
                     "title": titles[i], "title_changed": i > 0 and titles[i] != titles[i-1],
                     "is_peak": i > 0 and variation[i] >= thr,
                     "wayback_url": url_by_month.get(m)})
    cands = sorted([r for r in rows if r["is_peak"]], key=lambda r: -r["variation"])
    return {"slug": slug, "months": len(months), "threshold": round(thr, 4),
            "rows": rows, "candidates": cands}


def main() -> None:
    slugs = sorted(os.path.basename(os.path.dirname(p))
                   for p in glob.glob(str(DIR / "*" / "manifest.json")))
    if len(sys.argv) > 1 and sys.argv[1] != "--all":
        slugs = [sys.argv[1]]
    out_dir = common.DATA_DIR / "pivots"; out_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    for slug in slugs:
        res = analyze(slug)
        if res["months"] >= 2 and res.get("rows"):
            (out_dir / f"profile_{slug}.json").write_text(
                json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        summary.append({"slug": slug, "months": res["months"],
                        "n_candidates": len(res.get("candidates", [])),
                        "max_var": max([r["variation"] for r in res.get("rows", [])], default=0.0),
                        "candidates": [{"label": c["label"], "variation": c["variation"],
                                        "title": c["title"], "title_changed": c["title_changed"],
                                        "wayback_url": c["wayback_url"]}
                                       for c in res.get("candidates", [])[:5]]})
    summary.sort(key=lambda x: -x["max_var"])
    (out_dir / "_profile_changes.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    withc = [s for s in summary if s["n_candidates"]]
    print(f"✔ {len([s for s in summary if s['months']>=2])} perfiles analizados · "
          f"{len(withc)} con picos de cambio (heurística TF-IDF sobre contenido)\n")
    for s in withc:
        tag = "  [Δtítulo]" if any(c["title_changed"] for c in s["candidates"]) else ""
        print(f"### {s['slug']:18} {s['months']:>2}m · maxΔ={s['max_var']:.2f}{tag}")
        for c in s["candidates"]:
            flag = "Δtítulo" if c["title_changed"] else ""
            print(f"     {c['label']:>9}  var {c['variation']:.2f}  {flag:7} {c['title'][:46]}")


if __name__ == "__main__":
    main()

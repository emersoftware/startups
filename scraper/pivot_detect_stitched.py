"""STITCHED pivot/rebrand detector per startup.

Unlike pivot_detect.py (a single isolated domain), here we build the monthly
series of EACH startup by concatenating its ENTIRE chain of domains in
chronological order (each month tagged with the domain it comes from). This way:

- Product PIVOTS within a domain appear as variation peaks.
- REBRANDS (domain change) appear as (a) a domain boundary and
  (b) usually a variation peak at that boundary.

Variation = 1 - cosine(TF-IDF month_i, month_{i+1}) over the visible text.
Peak = variation >= mean + k·std (threshold) AND/OR domain boundary.

Usage:
  uv run python pivot_detect_stitched.py "Lummy"      # a single startup
  uv run python pivot_detect_stitched.py --all        # all, JSON summary
Output: data/pivots/<slug>.stitched.json  (+ prints a table)
"""
from __future__ import annotations

import glob
import json
import re
import sys

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import common
from pivot_detect import visible_text, page_title, page_h1, month_label

IDENT = common.DATA_DIR / "identity.json"


def load_identity() -> dict:
    return {s["name"]: s for s in json.loads(IDENT.read_text(encoding="utf-8"))["startups"]}


def domain_months(domain: str) -> list[tuple[str, str]]:
    """[(YYYYMM, filepath)] sorted, for a downloaded domain."""
    files = sorted(glob.glob(str(common.DATA_DIR / "wayback" / domain / "*.html")))
    out = []
    for f in files:
        m = re.search(r"(\d{6})\.html$", f)
        if m:
            out.append((m.group(1), f))
    return out


def build_series(startup: dict) -> list[dict]:
    """Monthly series stitched from the whole chain of domains (chronological order).

    Each confirmed domain contributes its months; we sort by (month, index in the
    chain) so that, when months tie, the predecessor comes before the successor.
    """
    chain = [d for d in startup["domains"] if d.get("confirmed", True)]
    rows = []
    for idx, d in enumerate(chain):
        for ym, fp in domain_months(d["domain"]):
            rows.append({"ym": ym, "chain_idx": idx, "domain": d["domain"],
                         "role": d.get("role"), "file": fp})
    rows.sort(key=lambda r: (r["ym"], r["chain_idx"]))
    return rows


def analyze(startup: dict) -> dict:
    rows = build_series(startup)
    if len(rows) < 2:
        return {"name": startup["name"], "months": len(rows), "rows": [], "candidates": [],
                "note": "serie insuficiente (<2 meses)"}

    docs, titles, h1s = [], [], []
    for r in rows:
        html = open(r["file"], encoding="utf-8", errors="replace").read()
        docs.append(visible_text(html))
        titles.append(page_title(html))
        h1s.append(page_h1(html))

    if sum(1 for d in docs if len(d.split()) >= 5) < 2:
        return {"name": startup["name"], "slug": startup["slug"], "months": len(rows),
                "rows": [], "candidates": [],
                "note": "texto visible insuficiente (páginas SPA/vacías)"}

    vec = TfidfVectorizer(ngram_range=(1, 2), max_features=6000, min_df=1, sublinear_tf=True)
    try:
        X = vec.fit_transform(docs)
    except ValueError:
        return {"name": startup["name"], "slug": startup["slug"], "months": len(rows),
                "rows": [], "candidates": [], "note": "vocabulario vacío (sin texto analizable)"}
    variation = [0.0] + [
        round(1 - float(cosine_similarity(X[i - 1], X[i])[0, 0]), 4) for i in range(1, len(docs))
    ]
    v = np.array(variation[1:])
    thr = float(v.mean() + 1.0 * v.std()) if len(v) else 1.0

    out_rows = []
    for i, r in enumerate(rows):
        domain_change = i > 0 and rows[i]["domain"] != rows[i - 1]["domain"]
        out_rows.append({
            "ym": r["ym"], "label": month_label(r["ym"]), "domain": r["domain"], "role": r["role"],
            "variation": variation[i], "title": titles[i], "h1": h1s[i],
            "domain_change": domain_change,
            "prev_domain": rows[i - 1]["domain"] if i > 0 else None,
            "is_peak": i > 0 and (variation[i] >= thr or domain_change),
        })

    cands = sorted([r for r in out_rows if r["is_peak"]], key=lambda r: -r["variation"])
    return {"name": startup["name"], "slug": startup["slug"], "months": len(rows),
            "threshold": round(thr, 4), "domains_in_series": sorted({r["domain"] for r in rows}),
            "rows": out_rows, "candidates": cands}


def print_report(res: dict) -> None:
    print(f"\n=== {res['name']} · {res['months']} meses · {len(res.get('domains_in_series',[]))} dominios · umbral={res.get('threshold')} ===")
    if not res["rows"]:
        print("  ", res.get("note", "sin datos"))
        return
    prev_t = prev_d = None
    for r in res["rows"]:
        bar = "█" * int(r["variation"] * 40)
        flag = "REBRAND→" if r["domain_change"] else ("PICO" if r["is_peak"] else "")
        dom = r["domain"] if r["domain"] != prev_d else ""
        t = r["title"][:54] if r["title"] != prev_t else ""
        print(f"  {r['label']:>9} {r['variation']:>6.3f} {flag:>9} {dom:<22} {bar} {t}")
        prev_t, prev_d = r["title"], r["domain"]


def main() -> None:
    ident = load_identity()
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        summary = []
        out_dir = common.DATA_DIR / "pivots"; out_dir.mkdir(parents=True, exist_ok=True)
        for name, s in ident.items():
            res = analyze(s)
            if res["months"] >= 2:
                (out_dir / f"{s['slug']}.stitched.json").write_text(
                    json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
            summary.append({"name": name, "slug": s["slug"], "months": res["months"],
                            "n_candidates": len(res.get("candidates", [])),
                            "candidates": [{"label": c["label"], "variation": c["variation"],
                                            "domain": c["domain"], "domain_change": c["domain_change"],
                                            "title": c["title"]} for c in res.get("candidates", [])[:6]]})
        summary.sort(key=lambda x: -x["n_candidates"])
        (out_dir / "_stitched_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        multi = [s for s in summary if s["months"] >= 2]
        print(f"✔ {len(multi)} startups con serie ≥2 meses · resumen en data/pivots/_stitched_summary.json")
        for s in summary[:25]:
            print(f"  {s['name']:<20} {s['months']:>3} meses  {s['n_candidates']:>2} candidatos")
    else:
        name = sys.argv[1] if len(sys.argv) > 1 else "Blar"
        s = ident.get(name) or next((v for v in ident.values() if v["slug"] == name), None)
        if not s:
            raise SystemExit(f"no encuentro startup '{name}'")
        res = analyze(s)
        print_report(res)
        out = common.DATA_DIR / "pivots" / f"{s['slug']}.stitched.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n→ {out}")


if __name__ == "__main__":
    main()

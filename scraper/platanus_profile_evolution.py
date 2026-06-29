"""Evolution of the title/slogan of each Platanus profile (first-hand pivot
signal: the startups themselves update it).

Reads data/wayback_platanus/<slug>/manifest.json and reports, per slug, the
timeline of distinct TITLES (the <title> carries 'Platanus | <Name>: <slogan>').
Flags the months where the title changed = pivot/rebrand candidate.

Usage:  uv run python scraper/platanus_profile_evolution.py [--all|<slug>]
Output: data/platanus_profile_evolution.json
"""
from __future__ import annotations
import glob, json, os, re
import common

DIR = common.DATA_DIR / "wayback_platanus"


def clean_title(t: str | None) -> str:
    if not t:
        return ""
    t = re.sub(r"^\s*Platanus\s*\|\s*", "", t)  # remove the site prefix
    return " ".join(t.split())


def evolution(slug: str) -> dict:
    mf = DIR / slug / "manifest.json"
    if not mf.exists():
        return {"slug": slug, "months": 0, "changes": [], "timeline": []}
    snaps = json.loads(mf.read_text(encoding="utf-8")).get("snapshots", [])
    tl, changes, prev = [], [], None
    for s in snaps:
        title = clean_title(s.get("title"))
        if not title or title.startswith("[error"):
            continue
        row = {"month": s["month"], "title": title, "wayback_url": s.get("wayback_url")}
        tl.append(row)
        if prev is not None and title != prev:
            changes.append({"month": s["month"], "from": prev, "to": title,
                            "wayback_url": s.get("wayback_url")})
        prev = title
    return {"slug": slug, "months": len(tl), "changes": changes, "timeline": tl}


def main() -> None:
    import sys
    slugs = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(str(DIR / "*" / "manifest.json")))
    if len(sys.argv) > 1 and sys.argv[1] != "--all":
        slugs = [sys.argv[1]]
    out = [evolution(s) for s in slugs]
    out = [o for o in out if o["months"]]
    (common.DATA_DIR / "platanus_profile_evolution.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    changed = [o for o in out if o["changes"]]
    print(f"✔ {len(out)} perfiles con datos · {len(changed)} con cambio de título (candidatos a pivot)\n")
    for o in sorted(changed, key=lambda o: -len(o["changes"])):
        print(f"### {o['slug']}  ({o['months']} meses, {len(o['changes'])} cambios)")
        for c in o["changes"]:
            print(f"    {c['month']}:  {c['from'][:48]}")
            print(f"             → {c['to'][:48]}")


if __name__ == "__main__":
    main()

"""Merge a PASSed trajectory-loop artifact into the canonical curated JSON.

For `<slug>` whose last critic verdict is PASS:
- copies the artifact of that tick to data/audit/<slug>/final.json
- upserts its pivot/rebrand phases into data/curated_trajectories.json
  (same schema the Platanus loop writes; old entries of the slug whose date is
  no longer in final.json are dropped)

Funding, founding, live_state and shutdown stay in final.json: the Kayyak
startups have no legacy timeline entry yet, so they are assembled from there.

Usage: uv run python kayyak_merge.py <slug> <tick>
"""

from __future__ import annotations

import json
import sys

import common

AUDIT = common.DATA_DIR / "audit"
CURATED = common.DATA_DIR / "curated_trajectories.json"


def domain_of(path: str | None, fallback: str) -> str:
    """data/wayback/galgo.com/latam/202305.html -> galgo.com/latam"""
    if path and path.startswith("data/wayback/"):
        return path.removeprefix("data/wayback/").rsplit("/", 1)[0]
    return fallback


def main() -> None:
    slug, tick = sys.argv[1], sys.argv[2]
    critic = json.loads((AUDIT / slug / f"tick-{tick}-critic.json").read_text(encoding="utf-8"))
    if critic.get("global_verdict") != "PASS":
        raise SystemExit(f"{slug} tick {tick}: global_verdict={critic.get('global_verdict')}, no se mergea")
    art = json.loads((AUDIT / slug / f"tick-{tick}.json").read_text(encoding="utf-8"))["artefacto"]
    (AUDIT / slug / "final.json").write_text(json.dumps(art, ensure_ascii=False, indent=2), encoding="utf-8")

    chain = art.get("domains_chain") or [""]
    new = [
        {
            "slug": slug,
            "type": p["type"],
            "date": p["date"],
            "domain": domain_of(p.get("body_snapshot_path"), chain[-1]),
            "title": p["title"],
            "prose": p["product_prose"],
        }
        for p in art.get("phases", [])
        if p["type"] in ("pivot", "rebrand")
    ]
    cur = json.loads(CURATED.read_text(encoding="utf-8")) if CURATED.exists() else []
    cur = [c for c in cur if c["slug"] != slug] + new
    CURATED.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✔ {slug}: final.json + {len(new)} pivots/rebrands → {CURATED.name} ({len(cur)} total)")
    for c in new:
        print(f"  {c['type']:8} {c['date']}  {c['domain']:22} {c['title']}")


if __name__ == "__main__":
    main()

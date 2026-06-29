"""Consolidates the scrapers into a unified dataset for analysis.

Merges Platanus + Start-Up Chile into a common schema and emits:
  - data/startups.json  (nested, with founders)
  - data/startups.csv   (one row per startup, flat)
  - data/founders.csv    (one row per founder)
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata

import common


def _read(name: str) -> list[dict]:
    path = common.DATA_DIR / name
    if not path.exists():
        print(f"  ! falta {name} (corre el scraper primero)")
        return []
    return json.loads(path.read_text(encoding="utf-8"))["startups"]


def _norm(name: str) -> str:
    """Dedup key: lowercase, no accents or symbols."""
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _blank_startup(**kw) -> dict:
    base = {
        "accelerator": "Start-Up Chile", "name": "", "slug": "", "batch": None,
        "country": None, "website": None, "slogan": None, "description": None,
        "tags": [], "program": None, "cohort": None, "profile_url": "",
        "founders": [],
    }
    base.update(kw)
    return base


def load() -> list[dict]:
    """Merges the 3 sources. SUP = portfolio (founders) + blog (cohorts), deduplicated."""
    platanus = _read("platanus.json")

    # Start-Up Chile: the blog has the large list by cohort; the portfolio
    # provides founders/tags. We merge by normalized name.
    sup: dict[str, dict] = {}
    for s in _read("startupchile_blog.json") + _read("startupchile_manual.json"):
        key = _norm(s["name"])
        if not key:
            continue
        cur = sup.setdefault(key, _blank_startup())
        cur.update({
            "name": cur["name"] or s["name"],
            "country": cur["country"] or s.get("country"),
            "website": cur["website"] or s.get("website"),
            "description": cur["description"] or s.get("description"),
            "program": cur["program"] or s.get("program"),
            "cohort": cur["cohort"] or s.get("cohort"),
            "batch": cur["batch"] or s.get("cohort"),
            "profile_url": cur["profile_url"] or s.get("source_url", ""),
        })
    for s in _read("startupchile.json"):  # curated portfolio (with founders)
        cur = sup.setdefault(_norm(s["name"]), _blank_startup(name=s["name"]))
        cur["slug"] = cur["slug"] or s.get("slug", "")
        cur["website"] = cur["website"] or s.get("website")
        cur["description"] = cur["description"] or s.get("description")
        cur["tags"] = s.get("tags") or cur["tags"]
        cur["profile_url"] = s.get("profile_url") or cur["profile_url"]
        if s.get("founders"):
            cur["founders"] = s["founders"]
        if not cur["batch"]:
            cur["batch"] = s.get("batch")  # portfolio year

    return platanus + list(sup.values())


def main() -> None:
    startups = load()

    # unified JSON
    payload = {
        "count": len(startups),
        "by_accelerator": {
            acc: sum(1 for s in startups if s["accelerator"] == acc)
            for acc in sorted({s["accelerator"] for s in startups})
        },
        "startups": startups,
    }
    common.save_json("startups.json", payload)

    # flat CSV of startups
    cols = [
        "accelerator", "name", "slug", "batch", "country",
        "website", "slogan", "n_founders", "founder_names", "profile_url",
    ]
    with (common.DATA_DIR / "startups.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for s in startups:
            founders = s.get("founders", [])
            w.writerow({
                "accelerator": s["accelerator"],
                "name": s["name"],
                "slug": s["slug"],
                "batch": s.get("batch") or "",
                "country": s.get("country") or "",
                "website": s.get("website") or "",
                "slogan": s.get("slogan") or "",
                "n_founders": len(founders),
                "founder_names": "; ".join(f["name"] for f in founders),
                "profile_url": s.get("profile_url") or "",
            })

    # CSV of founders (one per row)
    with (common.DATA_DIR / "founders.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["accelerator", "startup", "batch", "founder", "role", "socials"])
        for s in startups:
            for fr in s.get("founders", []):
                socials = " ".join(f"{k}={v}" for k, v in (fr.get("socials") or {}).items())
                w.writerow([
                    s["accelerator"], s["name"], s.get("batch") or "",
                    fr["name"], fr.get("role") or "", socials,
                ])

    n_founders = sum(len(s.get("founders", [])) for s in startups)
    print(f"✔ {len(startups)} startups · {n_founders} founders")
    print(f"  by_accelerator: {payload['by_accelerator']}")
    print("  → data/startups.json, data/startups.csv, data/founders.csv")


if __name__ == "__main__":
    main()

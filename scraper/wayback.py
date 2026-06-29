"""Timeline of a landing page via the Wayback Machine (one capture per year).

For a domain, queries archive.org's CDX API, picks one capture per year and
extracts the pitch (title + meta description + H1) of each one to evidence
pivots. Reusable across the whole portfolio.

Usage:  uv run python wayback.py blar.io
Output: data/wayback/<domain>.json
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass

import httpx
from selectolax.parser import HTMLParser

import common

CDX = "http://web.archive.org/cdx/search/cdx"


@dataclass
class Snapshot:
    year: int
    timestamp: str
    wayback_url: str
    title: str | None = None
    description: str | None = None
    headline: str | None = None


def list_snapshots(http: httpx.Client, domain: str) -> list[dict]:
    """HTML 200 captures of the domain (root page), sorted by date."""
    params = {
        "url": domain,
        "output": "json",
        "fl": "timestamp,original,statuscode,digest",
        "filter": ["statuscode:200", "mimetype:text/html"],
        "collapse": "digest",  # drop consecutive identical captures
    }
    r = common.polite_get(http, CDX, params=params, delay=0.3)
    rows = r.json()
    return [dict(zip(rows[0], row)) for row in rows[1:]] if rows else []


def pick_one_per_year(snaps: list[dict]) -> dict[int, dict]:
    """One capture per year: the one closest to mid-year (July 1)."""
    by_year: dict[int, list[dict]] = {}
    for s in snaps:
        year = int(s["timestamp"][:4])
        by_year.setdefault(year, []).append(s)
    chosen: dict[int, dict] = {}
    for year, items in by_year.items():
        target = f"{year}0701000000"
        chosen[year] = min(items, key=lambda s: abs(int(s["timestamp"]) - int(target)))
    return chosen


def characterize(http: httpx.Client, domain: str, timestamp: str) -> Snapshot:
    # `id_` returns the original HTML without the Wayback toolbar
    raw_url = f"https://web.archive.org/web/{timestamp}id_/http://{domain}/"
    view_url = f"https://web.archive.org/web/{timestamp}/http://{domain}/"
    snap = Snapshot(year=int(timestamp[:4]), timestamp=timestamp, wayback_url=view_url)
    try:
        r = common.polite_get(http, raw_url, delay=0.3, retries=2)
        tree = HTMLParser(r.text)
        if tree.css_first("title"):
            snap.title = " ".join(tree.css_first("title").text().split())[:160]
        meta = tree.css_first('meta[name="description"], meta[property="og:description"]')
        if meta:
            snap.description = " ".join((meta.attributes.get("content") or "").split())[:240]
        h1 = tree.css_first("h1")
        if h1:
            snap.headline = " ".join(h1.text().split())[:160]
    except Exception as exc:  # noqa: BLE001
        snap.title = f"[error: {type(exc).__name__}]"
    return snap


def timeline(domain: str) -> list[Snapshot]:
    with common.client(timeout=20.0) as http:
        snaps = list_snapshots(http, domain)
        chosen = pick_one_per_year(snaps)
        out: list[Snapshot] = []
        for year in sorted(chosen):
            out.append(characterize(http, domain, chosen[year]["timestamp"]))
        return out


def main() -> None:
    domain = sys.argv[1] if len(sys.argv) > 1 else "blar.io"
    domain = domain.replace("https://", "").replace("http://", "").strip("/")
    print(f"Wayback timeline para {domain}\n")
    snaps = timeline(domain)
    for s in snaps:
        print(f"  {s.year}  {s.wayback_url}")
        print(f"        title: {s.title}")
        if s.headline:
            print(f"        h1   : {s.headline}")
        if s.description:
            print(f"        desc : {s.description}")
        print()
    out_dir = common.DATA_DIR / "wayback"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{domain}.json"
    path.write_text(
        json.dumps({"domain": domain, "snapshots": [asdict(s) for s in snaps]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✔ {len(snaps)} años · guardado en {path}")


if __name__ == "__main__":
    main()

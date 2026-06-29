"""Archive the Platanus PROFILE pages (platan.us/startups/<slug>) month by month.

These pages are updated by the startups themselves, so their title/slogan/
description over time is a first-hand signal of pivots and rebrands —
independent of each startup's own landing page.

Saves data/wayback_platanus/<slug>/YYYYMM.html + manifest.json (same format
as wayback_archive.py, so the detector can be run on top of it).

Usage:  uv run python scraper/wayback_archive_platanus.py
"""
from __future__ import annotations
import json, time
from dataclasses import asdict

import common
from wayback_archive import MonthSnap, monthly_snapshots
from selectolax.parser import HTMLParser

BASE = "platan.us/startups/"


def archive_slug(slug: str) -> int:
    out_dir = common.DATA_DIR / "wayback_platanus" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    if (out_dir / "manifest.json").exists():
        print(f"  {slug}: ya existe, salto"); return 0
    saved: list[MonthSnap] = []
    with common.client(timeout=30.0) as http:
        snaps = monthly_snapshots(http, BASE + slug)
        print(f"  {slug}: {len(snaps)} meses", flush=True)
        for s in snaps:
            ts = s["timestamp"]
            month = f"{ts[:4]}-{ts[4:6]}"
            raw = f"https://web.archive.org/web/{ts}id_/https://platan.us/startups/{slug}"
            view = f"https://web.archive.org/web/{ts}/https://platan.us/startups/{slug}"
            ms = MonthSnap(month=month, timestamp=ts, wayback_url=view, file=f"{slug}/{ts[:6]}.html")
            try:
                r = common.polite_get(http, raw, delay=0.4, retries=2)
                html = r.text
                (out_dir / f"{ts[:6]}.html").write_text(html, encoding="utf-8", errors="replace")
                ms.bytes = len(html.encode("utf-8"))
                tree = HTMLParser(html)
                if tree.css_first("title"):
                    ms.title = " ".join(tree.css_first("title").text().split())[:160]
                if tree.css_first("h1"):
                    ms.headline = " ".join(tree.css_first("h1").text().split())[:160]
            except Exception as exc:  # noqa: BLE001
                ms.title = f"[error: {type(exc).__name__}]"
            saved.append(ms)
    (out_dir / "manifest.json").write_text(
        json.dumps({"slug": slug, "url": "https://platan.us/startups/" + slug,
                    "months": len(saved), "snapshots": [asdict(s) for s in saved]},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    return len([s for s in saved if s.bytes])


def main() -> None:
    slugs = [s["slug"] for s in json.loads(
        (common.DATA_DIR / "identity.json").read_text(encoding="utf-8"))["startups"]]
    print(f"Archivando perfiles Platanus de {len(slugs)} startups\n")
    done = 0
    for i, slug in enumerate(slugs, 1):
        print(f"[{i}/{len(slugs)}] {slug}", flush=True)
        try:
            done += archive_slug(slug)
        except Exception as exc:  # noqa: BLE001
            print(f"  FALLO {slug}: {type(exc).__name__}", flush=True)
        time.sleep(1.5)
    print(f"\n✔ listo · {done} páginas-mes guardadas en data/wayback_platanus/")


if __name__ == "__main__":
    main()

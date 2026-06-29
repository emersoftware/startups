"""Archive a full landing page from the Wayback Machine: one capture per MONTH.

For a domain, takes one capture for each available month from the CDX API and
downloads the full HTML of each one (`id_` version, without the Wayback toolbar).
Saves each page + a manifest with the metadata for pivot analysis.

Usage:  uv run python wayback_archive.py blar.io
Output: data/wayback/<domain>/YYYYMM.html  + manifest.json
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass

import httpx
from selectolax.parser import HTMLParser

import common

CDX = "http://web.archive.org/cdx/search/cdx"


@dataclass
class MonthSnap:
    month: str            # "YYYY-MM"
    timestamp: str        # YYYYMMDDhhmmss
    wayback_url: str      # browsable capture
    file: str             # relative path of the saved HTML
    bytes: int = 0
    title: str | None = None
    headline: str | None = None
    description: str | None = None


def monthly_snapshots(http: httpx.Client, domain: str) -> list[dict]:
    """One HTML 200 capture per month (collapse=timestamp:6 = YYYYMM)."""
    params = {
        "url": domain,
        "output": "json",
        "fl": "timestamp,original,statuscode,digest",
        "filter": ["statuscode:200", "mimetype:text/html"],
        "collapse": "timestamp:6",
    }
    r = common.polite_get(http, CDX, params=params, delay=0.3)
    rows = r.json()
    return [dict(zip(rows[0], row)) for row in rows[1:]] if rows else []


def archive_domain(domain: str) -> list[MonthSnap]:
    out_dir = common.DATA_DIR / "wayback" / domain
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[MonthSnap] = []
    with common.client(timeout=30.0) as http:
        snaps = monthly_snapshots(http, domain)
        print(f"  {domain}: {len(snaps)} meses disponibles")
        for s in snaps:
            ts = s["timestamp"]
            month = f"{ts[:4]}-{ts[4:6]}"
            raw_url = f"https://web.archive.org/web/{ts}id_/http://{domain}/"
            view_url = f"https://web.archive.org/web/{ts}/http://{domain}/"
            fname = f"{ts[:6]}.html"
            ms = MonthSnap(month=month, timestamp=ts, wayback_url=view_url,
                           file=f"{domain}/{fname}")
            try:
                r = common.polite_get(http, raw_url, delay=0.4, retries=2)
                html = r.text
                (out_dir / fname).write_text(html, encoding="utf-8", errors="replace")
                ms.bytes = len(html.encode("utf-8"))
                tree = HTMLParser(html)
                if tree.css_first("title"):
                    ms.title = " ".join(tree.css_first("title").text().split())[:160]
                if tree.css_first("h1"):
                    ms.headline = " ".join(tree.css_first("h1").text().split())[:160]
                meta = tree.css_first('meta[name="description"], meta[property="og:description"]')
                if meta:
                    ms.description = " ".join((meta.attributes.get("content") or "").split())[:240]
                print(f"    {month}  {ms.bytes:>7}B  {ms.title or ''}")
            except Exception as exc:  # noqa: BLE001
                ms.title = f"[error: {type(exc).__name__}]"
                print(f"    {month}  ERROR {type(exc).__name__}")
            saved.append(ms)

    manifest = out_dir / "manifest.json"
    manifest.write_text(
        json.dumps({"domain": domain, "months": len(saved),
                    "snapshots": [asdict(s) for s in saved]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return saved


def main() -> None:
    domain = (sys.argv[1] if len(sys.argv) > 1 else "blar.io")
    domain = domain.replace("https://", "").replace("http://", "").strip("/")
    print(f"Archivando {domain} (1 captura/mes, HTML completo)\n")
    saved = archive_domain(domain)
    ok = [s for s in saved if s.bytes]
    total = sum(s.bytes for s in saved)
    print(f"\n✔ {len(ok)}/{len(saved)} meses guardados · {round(total/1024)} KB")
    print(f"  en data/wayback/{domain}/  (+ manifest.json)")


if __name__ == "__main__":
    main()

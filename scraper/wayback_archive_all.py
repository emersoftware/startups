"""Archive (1 capture/month, full HTML) the landing pages of ALL Platanus startups.

Uses the ORIGINAL domain that Platanus listed for each startup, so that the ones
that died or got redirected (e.g. Bemmbo→buk) also bring their history along.
Resumable: if a domain's manifest already exists, it is skipped.

Usage:  uv run python wayback_archive_all.py
Output: data/wayback/<domain>/...  + data/wayback/index.json
"""

from __future__ import annotations

import json
from urllib.parse import urlparse

import common
from wayback_archive import archive_domain


def original_domain(website: str | None) -> str | None:
    if not website:
        return None
    netloc = urlparse(website if "//" in website else f"https://{website}").netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc or None


def main() -> None:
    plat = json.loads((common.DATA_DIR / "platanus.json").read_text(encoding="utf-8"))
    targets = []
    for s in plat["startups"]:
        dom = original_domain(s.get("website"))
        if dom:
            targets.append((s["name"], s["slug"], dom))

    print(f"Archivando {len(targets)} landings de Platanus (1/mes, HTML completo)\n")
    index = []
    for i, (name, slug, dom) in enumerate(targets, 1):
        manifest = common.DATA_DIR / "wayback" / dom / "manifest.json"
        if manifest.exists():
            m = json.loads(manifest.read_text(encoding="utf-8"))
            print(f"[{i}/{len(targets)}] {name} ({dom}) — ya archivado ({m['months']} meses), salto")
            index.append({"name": name, "slug": slug, "domain": dom, "months": m["months"]})
            continue
        print(f"[{i}/{len(targets)}] {name} ({dom})")
        try:
            saved = archive_domain(dom)
            index.append({"name": name, "slug": slug, "domain": dom,
                          "months": sum(1 for s in saved if s.bytes)})
        except Exception as exc:  # noqa: BLE001
            print(f"    ! falló {dom}: {type(exc).__name__}")
            index.append({"name": name, "slug": slug, "domain": dom, "months": 0,
                          "error": type(exc).__name__})
        # persist the index after each domain (resumable / visible progress)
        (common.DATA_DIR / "wayback" / "index.json").write_text(
            json.dumps({"count": len(index), "startups": index}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    total = sum(x["months"] for x in index)
    print(f"\n✔ {len(index)} dominios · {total} meses-página archivados en total")


if __name__ == "__main__":
    main()

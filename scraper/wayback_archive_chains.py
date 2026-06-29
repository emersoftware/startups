"""Download the missing monthly landing pages of the domain chains
(rebrand predecessors + brand-era primaries) for the stitched pivot analysis.

Order: PRIORITY (rebrand predecessors) first, then SECONDARY (twins/expansion).
Skips already-downloaded domains. Idempotent.

Usage:  uv run python scraper/wayback_archive_chains.py
"""
from __future__ import annotations
import sys, time
import common
from wayback_archive import archive_domain

PRIORITY = [
    "verso.ai", "fudata.com.mx", "appio.com.mx", "pronty.co", "wireworks.app",
    "getperhaps.com", "rentz.cl", "urvana.net", "telaio.finance", "clubdelbajon.com",
    "elclubdelbajon.com", "payhaus.app", "autentiz.com", "unacuarta.com", "bircle.io",
    "getblar.com", "blar.tech", "pipoll.com", "signatureapi.com", "watermelon.tools",
    "larnu.app", "jarofreight.com", "stradecustom.com", "getkapso.com",
]
SECONDARY = [
    "examedi.co", "examedi.mx", "fintoc.cl", "fintoc.mx", "urvana.cl", "blokay.co",
    "plutto.cl", "plutto.ai", "gokei.cl", "identyz.cl", "wasabil.cl", "divisso.cl",
    "carvuk.cl", "reversso.cl", "wallstate.co", "fireflux.dev", "fiscoclic.io", "kambia.pe",
]

def main() -> None:
    targets = PRIORITY + SECONDARY
    done = 0
    for i, dom in enumerate(targets, 1):
        out = common.DATA_DIR / "wayback" / dom
        if (out / "manifest.json").exists():
            print(f"[{i}/{len(targets)}] {dom} ya existe, salto")
            continue
        print(f"\n[{i}/{len(targets)}] === {dom} ===", flush=True)
        try:
            archive_domain(dom)
            done += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  FALLO {dom}: {type(exc).__name__} {exc}", flush=True)
        time.sleep(2.0)  # courtesy delay between domains (archive.org rate-limit)
    print(f"\n✔ listo. {done} dominios nuevos descargados.")

if __name__ == "__main__":
    main()

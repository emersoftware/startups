"""Seed identity entries for the Kayyak Ventures portfolio and archive their landings.

Reads data/kayyak.json and writes data/identity.json in the same shape as the
Platanus one (name, slug, names, domains[], status, chain[]), so the rest of the
pipeline (wayback_archive -> title_timeline_audit -> trajectory loop) runs
unchanged. Domains come from the Kayyak profile `website`, plus the surfaces
found by probing Wayback (predecessor brands, alt-TLDs, and paths the root
redirects to, e.g. galgo.com -> /latam).

Usage:
  uv run python kayyak_identity.py            # write data/identity.json
  uv run python kayyak_identity.py archive    # + download monthly landings
"""

from __future__ import annotations

import json
import sys
import time

import common
from wayback_archive import archive_domain

# slug -> [(domain or domain/path, role, note)]
SURFACES: dict[str, list[tuple[str, str, str]]] = {
    "xepelin": [("xepelin.com", "current", "")],
    "webdox": [
        ("webdox.cl", "former", "Primary domain until 2020-11; now 301 to webdoxclm.com."),
        ("webdoxclm.com", "current", "From 2020-12 (CLM positioning)."),
    ],
    "destacame": [("destacame.cl", "current", "")],
    "agrourbana": [("agrourbana.com", "current", "200 captures only 2013-2018; check live site/press.")],
    "coworklatam": [("coworklatam.com", "current", "")],
    "galgo": [
        ("migrante.cl", "former", "Migrante era (2014-2019)."),
        ("migrante.com", "former",
         "Today 301 -> galgo.com/cl (same company). Captures since 2010 may predate ownership."),
        ("galgo.com/latam", "current",
         "galgo.com root redirects here since 2023-05; pre-2023 root belonged to an unrelated site."),
        ("galgo.com/cl", "current", "Chile storefront (motorcycle financing)."),
    ],
    "f4f": [("f4f.cl", "current", "")],
    "wherex": [("wherex.com", "current", "Captures since 2003 may predate ownership.")],
    "chipax": [("chipax.com", "current", "")],
    "agendapro": [
        ("agendapro.cl", "alt-tld", "Captures 2014-2015."),
        ("agendapro.com", "current", "Root 200 until 2021-03, then redirects to /cl."),
        ("agendapro.com/cl", "current", "Chile site after the root redirect."),
    ],
    "wheeltheworld": [("wheeltheworld.com", "current", "")],
    "healthatom": [("healthatom.com", "current", "")],
    "enerlink": [
        ("enerlink.cl", "current", ""),
        ("enerlink.com", "current", "Captures since 1996 may predate ownership."),
    ],
    "timining": [("timining.com", "current", "")],
    "vmetrix": [("vmetrix.com", "current", "")],
    "rankmi": [("rankmi.com", "current", "")],
    "futurebeyond": [],  # founded 2026 by the ex-Spike team; no domain found yet
    "foodology": [
        ("foodology.com.co", "current",
         "foodology.com and foodology.co are expired domains (unrelated blog / parked)."),
    ],
    "fracttal": [("fracttal.com", "current", "Captures since 2004 may predate ownership.")],
    "1doc3": [("1doc3.com", "current", "")],
    "aptuno": [("aptuno.com", "current", "")],
    "cargamos": [("cargamos.com", "current", "")],
    "colektia": [("colektia.com", "current", "")],
    "fairplay": [("getfairplay.com", "current", "")],
    "henry": [("soyhenry.com", "current", "")],
    "marco": [("marcofi.com", "current", "Captures since 2010 may predate ownership.")],
    "miroculus": [("miroculus.com", "current",
                   "Today 301 -> integra-biosciences.com/en/ngs-automation/miro-canvas (acquisition?).")],
    "pulsar": [
        ("pulsarml.com", "current", "Root redirects to /en from 2025."),
        ("pulsarml.com/en", "current", ""),
    ],
    "sofiasalud": [("sofiasalud.com", "current", "")],
    "humatics": [("humatics.com", "current", "")],
    "cytovale": [("cytovale.com", "current", "")],
}


def seed() -> list[dict]:
    kayyak = json.loads((common.DATA_DIR / "kayyak.json").read_text(encoding="utf-8"))
    out = []
    for s in kayyak["startups"]:
        slug = s["slug"]
        if slug not in SURFACES:
            raise SystemExit(f"sin superficies definidas para {slug}")
        names = [s["name"], *s["former_names"]]
        out.append({
            "name": s["name"],
            "slug": slug,
            "names": names,
            "domains": [
                {"domain": d, "role": role, "confirmed": True,
                 "source": s["profile_url"] or s["first_seen_url"], "note": note}
                for d, role, note in SURFACES[slug]
            ],
            "rebrand": f"{' → '.join(reversed(names))}" if s["former_names"] else None,
            "status": "unknown" if s["status"] == "current" else "departed-portfolio",
            "chain": [],
            "accelerator": "Kayyak Ventures",
            "kayyak": {k: s[k] for k in (
                "status", "hq", "country", "chilean_hq", "founders", "website",
                "profile_url", "first_seen", "first_seen_url", "last_seen")},
        })
    return out


def archive(startups: list[dict]) -> None:
    targets = [d["domain"] for s in startups for d in s["domains"]]
    for i, dom in enumerate(targets, 1):
        if (common.DATA_DIR / "wayback" / dom / "manifest.json").exists():
            print(f"[{i}/{len(targets)}] {dom} ya existe, salto")
            continue
        print(f"\n[{i}/{len(targets)}] === {dom} ===", flush=True)
        try:
            archive_domain(dom)
        except Exception as exc:  # noqa: BLE001
            print(f"  FALLO {dom}: {type(exc).__name__} {exc}", flush=True)
        time.sleep(2.0)  # courtesy delay between domains (archive.org rate-limit)


def main() -> None:
    startups = seed()
    path = common.save_json("identity.json", {"startups": startups})
    n_dom = sum(len(s["domains"]) for s in startups)
    print(f"✔ {len(startups)} startups · {n_dom} superficies → {path}")
    curated = common.DATA_DIR / "pivots_curated.json"
    if not curated.exists():
        curated.write_text("[]", encoding="utf-8")
    if "archive" in sys.argv[1:]:
        archive(startups)


if __name__ == "__main__":
    main()

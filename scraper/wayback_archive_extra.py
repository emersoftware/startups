"""Archive in Wayback the NEW domains discovered in trajectory.json.

Renames/alternate domains (getskip.ai, faces.app, bloocks.com, etc.) that were
not in the original file. Reuses archive_domain (1 capture/month, full HTML).
Resumable (skips the ones that already have a manifest).

Usage: uv run python wayback_archive_extra.py
"""

from __future__ import annotations

import json

import common
from wayback_archive import archive_domain

# buk.cl excluded: it is Buk's corporate site (not Bemmbo's history,
# which is already archived under bemmbo.com) and would bring hundreds of irrelevant months.
EXCLUDE = {"buk.cl"}


def norm(d: str) -> str:
    return d.replace("https://", "").replace("http://", "").strip("/").replace("www.", "")


def main() -> None:
    traj = json.loads((common.DATA_DIR / "trajectory.json").read_text(encoding="utf-8"))
    wb = common.DATA_DIR / "wayback"

    # target domains = all those in trajectory that do NOT have a folder yet
    targets: list[tuple[str, str]] = []
    seen: set[str] = set()
    for s in traj["startups"]:
        for d in s.get("domains", []):
            dom = norm(d)
            if not dom or dom in seen or dom in EXCLUDE:
                continue
            seen.add(dom)
            if not (wb / dom).exists():
                targets.append((s["name"], dom))

    print(f"Dominios nuevos a archivar: {len(targets)} (excluidos: {EXCLUDE})\n")
    done = []
    for i, (name, dom) in enumerate(targets, 1):
        if (wb / dom / "manifest.json").exists():
            print(f"[{i}/{len(targets)}] {dom} ya archivado, salto")
            continue
        print(f"[{i}/{len(targets)}] {name} -> {dom}")
        try:
            saved = archive_domain(dom)
            done.append((dom, sum(1 for s in saved if s.bytes)))
        except Exception as exc:  # noqa: BLE001
            print(f"    ! falló {dom}: {type(exc).__name__}")
            done.append((dom, 0))

    total = sum(m for _, m in done)
    print(f"\n✔ {len(done)} dominios · {total} meses-página nuevos archivados")


if __name__ == "__main__":
    main()

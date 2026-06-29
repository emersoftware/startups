"""Motor de auditoría de trayectorias: reconstruye las FASES de cada startup a
partir de la secuencia de TÍTULOS (y descripciones) que ya tenemos archivadas, y
las compara con los pivots curados para detectar trayectorias SUB-capturadas.

Por qué: la curación previa anotó ~1 pivot por startup cuando las trayectorias
reales tienen 3-4 fases. Pero el title timeline de cada landing/perfil (que ya
está en los manifests) muestra TODAS las fases gratis. Este script lo hace
mecánico: si una startup tiene más fases de título distintas que pivots curados,
queda FLAG para re-curar.

Fuentes por startup (en orden de prioridad de DATACIÓN — gana la señal más temprana):
  - landings (data/wayback/<dom>/manifest.json)  → el landing LIDERA el cambio
  - perfil Platanus (data/wayback_platanus/<slug>/manifest.json) → suele REZAGAR

Salida:
  - data/title_audit.json   (estructura por startup: fases + candidatos + flag)
  - data/TITLE_AUDIT.md      (reporte legible para curación humana)
  - stdout: ranking de startups sub-capturadas

Uso: uv run python scraper/title_timeline_audit.py
"""
from __future__ import annotations
import json, re
import common

ROOT = common.ROOT
DATA = common.DATA_DIR


def norm_title(t: str | None, brand: str) -> str:
    """Normaliza un título a su 'tagline' comparable: quita el prefijo de marca
    y el chrome de Platanus, baja a minúsculas, colapsa espacios."""
    if not t:
        return ""
    t = t.strip()
    # 'Platanus | Blar: Tagline' -> 'Tagline' ; 'Blar | Tagline' / 'Gokei - Tagline' -> 'Tagline'
    t = re.sub(r"^platanus\s*\|\s*", "", t, flags=re.I)
    # corta en el primer separador de marca (| - : –) y toma lo que viene después si hay
    parts = re.split(r"\s*[|\-–:]\s*", t, maxsplit=1)
    tail = parts[1] if len(parts) > 1 else parts[0]
    tail = tail.strip().lower()
    # si quedó solo el nombre de marca (perfil sin slogan), trátalo como vacío de señal
    if norm_word(tail) == norm_word(brand):
        return ""
    return re.sub(r"\s+", " ", tail)


def norm_word(x: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (x or "").lower())


def collect_surface(snaps: list[dict], surface: str) -> list[dict]:
    """Devuelve filas (ym, ts, surface, title, description, wayback_url) ordenadas,
    saltando snapshots con error/sin título."""
    rows = []
    for s in snaps:
        ts = s.get("timestamp", "")
        if not ts:
            continue
        title = s.get("title") or ""
        if not title or title.startswith("[error") or "HTTPStatus" in title:
            continue
        rows.append({
            "ym": f"{ts[:4]}-{ts[4:6]}", "ts": ts, "surface": surface,
            "title": title, "description": (s.get("description") or "")[:240],
            "wayback_url": s.get("wayback_url"),
        })
    rows.sort(key=lambda r: r["ts"])
    return rows


def phases_for_surface(rows: list[dict], brand: str) -> list[dict]:
    """Comprime filas consecutivas con el MISMO título normalizado en fases con
    rango de fechas. Cada fase: {tag, first_ym, last_ym, first_url, title, desc}."""
    phases = []
    for r in rows:
        tag = norm_title(r["title"], brand)
        if tag == "":  # snapshot sin señal de tagline (solo marca) — no rompe fase
            continue
        if phases and phases[-1]["tag"] == tag:
            phases[-1]["last_ym"] = r["ym"]
        else:
            phases.append({"tag": tag, "first_ym": r["ym"], "last_ym": r["ym"],
                           "first_ts": r["ts"], "first_url": r["wayback_url"],
                           "title": r["title"], "desc": r["description"]})
    return phases


def main() -> None:
    ident = {s["slug"]: s for s in json.loads((DATA / "identity.json").read_text(encoding="utf-8"))["startups"]}
    curated = json.loads((DATA / "pivots_curated.json").read_text(encoding="utf-8"))
    cur_by_slug: dict[str, list] = {}
    for c in curated:
        cur_by_slug.setdefault(c["slug"], []).append(c)

    report = []
    for slug, s in ident.items():
        brand = s["name"].strip()
        doms = [d["domain"] for d in s.get("domains", []) if d.get("confirmed", True)]

        # --- recolecta todas las superficies ---
        surfaces = []  # (label, rows)
        for dom in doms:
            mf = DATA / "wayback" / dom / "manifest.json"
            if mf.exists():
                rows = collect_surface(json.loads(mf.read_text(encoding="utf-8")).get("snapshots", []), f"landing:{dom}")
                if rows:
                    surfaces.append((f"landing:{dom}", rows))
        pmf = DATA / "wayback_platanus" / slug / "manifest.json"
        if pmf.exists():
            rows = collect_surface(json.loads(pmf.read_text(encoding="utf-8")).get("snapshots", []), "profile")
            if rows:
                surfaces.append(("profile", rows))

        # fases por superficie
        per_surface = {label: phases_for_surface(rows, brand) for label, rows in surfaces}

        # universo de taglines distintas a través de TODAS las superficies (señal de fases)
        # ordena por primera aparición global (ts más temprano de cada tag, en cualquier superficie)
        first_seen = {}
        for label, ph in per_surface.items():
            for p in ph:
                if p["tag"] not in first_seen or p["first_ts"] < first_seen[p["tag"]]["first_ts"]:
                    first_seen[p["tag"]] = {**p, "surface": label}
        all_tags = [p for _, p in sorted(first_seen.items(), key=lambda kv: kv[1]["first_ts"])]

        n_distinct = len(all_tags)
        n_curated = len(cur_by_slug.get(slug, []))
        # transiciones = nº de fases - 1 (cambios de mensaje observados)
        n_transitions = max(0, n_distinct - 1)
        flag = n_transitions > n_curated  # más cambios observados que pivots curados

        report.append({
            "slug": slug, "name": brand, "status": s.get("status"),
            "n_surfaces": len(surfaces), "n_distinct_taglines": n_distinct,
            "n_transitions": n_transitions, "n_curated": n_curated, "flag": flag,
            "global_phases": [{"tag": p["tag"], "first_ym": p["first_ym"], "last_ym": p["last_ym"],
                                "surface": p["surface"], "title": p["title"], "desc": p["desc"],
                                "wayback_url": p["first_url"]} for p in all_tags],
            "per_surface": {label: [{"tag": p["tag"], "first_ym": p["first_ym"], "last_ym": p["last_ym"],
                                      "title": p["title"], "desc": p["desc"], "wayback_url": p["first_url"]}
                                     for p in ph] for label, ph in per_surface.items()},
            "curated": [{"type": c["type"], "date": c["date"], "title": c["title"]} for c in cur_by_slug.get(slug, [])],
        })

    report.sort(key=lambda r: (not r["flag"], -(r["n_transitions"] - r["n_curated"]), r["slug"]))
    (DATA / "title_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- reporte markdown ---
    md = ["# Auditoría de trayectorias por title-timeline\n",
          "Compara las **fases de mensaje** observadas en los títulos archivados (landing ∪ perfil) "
          "contra los **pivots curados**. `FLAG` = hay más transiciones de mensaje que pivots curados → "
          "trayectoria probablemente sub-capturada.\n",
          "> Datación: gana la señal más temprana entre superficies (el landing suele liderar; el perfil rezaga).\n"]
    flagged = [r for r in report if r["flag"]]
    md.append(f"\n**{len(flagged)} de {len(report)} startups marcadas para revisión.**\n")
    for r in report:
        mark = "🚩" if r["flag"] else "  "
        md.append(f"\n## {mark} {r['name']} (`{r['slug']}`) — {r['n_distinct_taglines']} taglines · "
                  f"{r['n_transitions']} transiciones vs {r['n_curated']} curados\n")
        if r["curated"]:
            md.append("**Pivots curados actuales:** " + "; ".join(f"{c['date']} {c['title']}" for c in r["curated"]) + "\n")
        md.append("\n**Fases observadas (orden global):**\n")
        for p in r["global_phases"]:
            rng = p["first_ym"] if p["first_ym"] == p["last_ym"] else f"{p['first_ym']}→{p['last_ym']}"
            md.append(f"- `{rng}` [{p['surface']}] **{p['title']}**"
                      + (f"  \n  _{p['desc']}_" if p["desc"] else "")
                      + (f"  \n  → {p['wayback_url']}" if p["wayback_url"] else ""))
    (DATA / "TITLE_AUDIT.md").write_text("\n".join(md), encoding="utf-8")

    print(f"✔ {len(report)} startups auditadas · {len(flagged)} marcadas (FLAG)\n")
    print(f"{'slug':16} {'taglines':>8} {'trans':>6} {'curados':>7}  gap")
    for r in flagged:
        print(f"{r['slug']:16} {r['n_distinct_taglines']:>8} {r['n_transitions']:>6} "
              f"{r['n_curated']:>7}  +{r['n_transitions']-r['n_curated']}")
    print(f"\n→ data/title_audit.json · data/TITLE_AUDIT.md")


if __name__ == "__main__":
    main()

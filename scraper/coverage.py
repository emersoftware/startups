"""Year-by-year coverage report for the goal (list up to 2026).

Maps cohorts -> year and emits data/COVERAGE.md with the per-year status of each
accelerator, including the gaps verified as non-public.
"""

from __future__ import annotations

import collections
import json

import common

# SUCh cohort -> year (based on the announcement post's date)
SUP_COHORT_YEAR = {
    "Build 3": 2022, "Ignite 3": 2022, "Growth 3": 2022,
    "Build 4": 2022, "Ignite 4": 2022, "Growth 4": 2022,
    "BIG 5": 2023, "BIG 6": 2023,
    "BIG 7": 2024, "BIG 8": 2024,
    "BIG 9": 2025, "BIG 10": 2025,
    "BIG 11": 2026,
}


def main() -> None:
    d = json.loads((common.DATA_DIR / "startups.json").read_text(encoding="utf-8"))
    plat = [s for s in d["startups"] if s["accelerator"] == "Platanus"]
    sup = [s for s in d["startups"] if s["accelerator"] == "Start-Up Chile"]

    # Platanus by year (batch "YYYY-N")
    plat_year: dict[int, int] = collections.Counter()
    for s in plat:
        b = s.get("batch") or ""
        if b[:4].isdigit():
            plat_year[int(b[:4])] += 1

    # SUCh by year via cohort
    sup_year: dict[int, collections.Counter] = collections.defaultdict(collections.Counter)
    for s in sup:
        coh = s.get("cohort") or s.get("batch")
        y = SUP_COHORT_YEAR.get(coh)
        if y is None and isinstance(coh, str) and coh[:4].isdigit():
            y = int(coh[:4])
        sup_year[y][coh] += 1

    lines: list[str] = []
    lines.append("# Cobertura por año — Start-Up Chile + Platanus (goal hasta 2026)\n")
    lines.append(f"Generado desde `data/startups.json` · {d['count']} startups totales\n")

    lines.append("## Platanus Ventures\n")
    lines.append("| Año | Startups | Estado |")
    lines.append("|---|---|---|")
    for y in range(2020, 2027):
        n = plat_year.get(y, 0)
        if n:
            st = "✅ portafolio público"
        elif y in (2025, 2026):
            st = "❌ no publicado (solo portal gated kalio; negativo verificado en blog+prensa)"
        else:
            st = "—"
        extra = " · ~6 startups, nombres no públicos (DF)" if y == 2026 else ""
        lines.append(f"| {y} | {n or '0'} | {st}{extra} |")
    lines.append(f"\n**Total Platanus: {len(plat)}** (batches 2020-1 → 2024-2).\n")

    lines.append("## Start-Up Chile (era moderna BIG / Build-Ignite-Growth)\n")
    lines.append("| Año | Cohortes | Startups | Estado |")
    lines.append("|---|---|---|---|")
    for y in range(2022, 2027):
        cohs = sup_year.get(y, {})
        n = sum(cohs.values())
        cohlist = ", ".join(f"{k} ({v})" for k, v in sorted(cohs.items()))
        st = "✅" if n else "—"
        if y == 2023:
            st = "✅ (BIG 6 solo 8 premiados; resto no publicado)"
        lines.append(f"| {y} | {cohlist or '—'} | {n} | {st} |")
    hist = sum(v for y, c in sup_year.items() if y is None for v in c.values())
    lines.append(f"\n**Total SUCh (moderna): {len(sup)}**"
                 f" · (alcance acordado: 2022-2026; histórico 2010-2021 fuera de alcance).\n")

    lines.append("## Gaps verificados (no son omisiones nuestras)\n")
    lines.append("- **Platanus 2025-1, 2025-2, 2026-1**: existen pero los nombres NO están "
                 "publicados en NINGUNA fuente accesible. Negativo verificado en 12 tipos de fuente: "
                 "(1) portafolio platan.us → máx 2024-2; (2) blog.platan.us → demo-day hasta may-2024, "
                 "selección hasta 2021; (3) prensa DF/Contxto/ecosistemastartup → solo cantidades; "
                 "(4) Crunchbase → 403; (5) Tracxn → solo inversiones follow-on; "
                 "(6) Wayback Machine → snapshot may-2026 idéntico (mismas 82); "
                 "(7) dominios puentos/puenteOS → no resuelven; (8) Google '\"PV 25-1\"' → sin resultados; "
                 "(9) LinkedIn (sesión logueada) → buscador bloquea automatización; "
                 "(10) kalio.platan.us → gated, sin API; (11) endpoints JSON → 406/404; "
                 "(12) YouTube (yt-dlp) → solo podcasts. "
                 "2026-1 = 6 startups (DF, 8-jun-2026), Demo Day aún no ocurre. "
                 "La data sólo existe en el portal gated o en perfiles LinkedIn de founders "
                 "auto-etiquetados 'PV 25-1' (cosechables sólo manualmente).")
    lines.append("- **SUCh BIG 6 (2023 H2)**: sin post-listado oficial; solo 8 premiados del "
                 "Demo Day (2 ene 2024) están públicos.")
    lines.append("- **puentOS**: no indexada en ninguna fuente pública; consistente con pertenecer "
                 "a una cohorte reciente de Platanus aún no publicada.")
    lines.append("- **SUCh BIG 7**: el listado oficial vive en `/blog/esta-es-nuestra-generacion-big-7/` "
                 "(no aparecía en el sitemap español por WPML); recuperadas 53 de 58.\n")

    path = common.DATA_DIR / "COVERAGE.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n→ escrito en {path}")


if __name__ == "__main__":
    main()

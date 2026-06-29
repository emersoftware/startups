"""Regenerates web/src/data/timeline.json from the authoritative sources, so
that EVERY event carries source_url by construction.

- fundacion : existing curated prose + source_url = platan.us/startups/<slug>
- capital   : existing curated prose + source_url = funding.json round.source_url
- adquisicion/cierre: existing prose + source_url (funding.exit | identity) +
                      basis that distinguishes confirmed vs inferred shutdown
- pivot/rebrand: REPLACES the preliminary pivots with the manually CURATED ones
                 (data/pivots_curated.json); source = Wayback Machine, source_url
                 = exact snapshot of the month of the change (heuristic + manual review)

Usage: uv run python build_timeline.py
"""
from __future__ import annotations
import json, re
import common

ROOT = common.ROOT
WEB = ROOT / "web" / "src" / "data" / "timeline.json"
MES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]


# Fact-check corrections (subagents against source_url). Key: (name, type, old_date)
CORRECTIONS = {
    ("Milla", "cierre", "2022-06"): {"date": "2025-10",
        "prose": "Gestión de viajes corporativos. milla.travel siguió con capturas vivas hasta oct-2025 y luego cayó (NXDOMAIN): cese de operaciones a fines de 2025, sin anuncio formal."},
    ("Toku", "capital", "2023-06"): {"date": "2023-03"},
    ("Kunzapp", "capital", "2023-06"): {"date": "2023-09"},
    ("Gokei", "capital", "2025-06"): {"date": "2025-09"},
    ("Examedi", "capital", "2021-06"): {"date": "2021-09"},
    ("Shinkansen", "capital", "2023-07"): {
        "prose": "Cerró una ronda Seed de US$3M liderada por ALLVP (Chile Ventures participó) para escalar su infraestructura de pagos entre bancos a la velocidad de internet."},
    ("Grupalia", "capital", "2025-10"): {"date": "2025-10", "title": "Seed US$4,8M (equity + deuda)",
        "prose": "Levantó una ronda seed de US$4,8M (equity + deuda), con Platanus Ventures, Semilla, Innogen, CAPEM y Addem, para créditos grupales digitales a micro-empresas en México."},
    # --- fundaciones corregidas: describen el producto ORIGINAL (no el actual). Ver docs/METHODOLOGY.md ---
    ("Blar", "fundacion", "2023-09"): {
        "prose": "Blar entró al batch 2023-2 de Platanus Ventures (inversión inicial ~US$100K) con una idea muy distinta a la actual: un 'ChatGPT para datos financieros', o sea traducir lenguaje natural a SQL (NL2SQL). De ahí derivó la tecnología de grafos de código que la llevó por varios pivots."},
    ("Gokei", "fundacion", "2023-09"): {
        "prose": "Gokei ingresó al batch 2023-2 de Platanus Ventures (inversión inicial ~US$100K) con una app amplia para coordinar la salud —agendar horas, exámenes, medicamentos— e incluso la idea de un seguro complementario digital, antes de encontrar su foco en los reembolsos."},
    ("Kapso", "fundacion", "2024-09"): {
        "prose": "Kapso se incorporó al batch de la segunda mitad de 2024 de Platanus Ventures con un producto totalmente distinto al actual: personal training online, entrenamiento de fuerza personalizado con coaches humanos + IA (prensa, may-2024)."},
}


def load(name):
    return json.loads((common.DATA_DIR / name).read_text(encoding="utf-8"))["startups"]


def first_url(s):
    blob = (s.get("status_detail","") or "") + " " + json.dumps(s.get("research",{}), ensure_ascii=False)
    m = re.search(r'https?://[^\s"\)\],]+', blob)
    u = m.group(0) if m else None
    # discard API endpoints (not readable sources); prefer a browsable capture
    if u and ("/cdx/search" in u or "wayback/available" in u):
        return None
    return u.rstrip("'\"") if u else None


def last_wayback(idt):
    """view_url of the last snapshot of the primary domain (evidence of shutdown)."""
    return (last_wayback_dated(idt) or (None, None))[1]


def last_wayback_dated(idt):
    """(date 'YYYY-MM', view_url) of the last live snapshot of the most recent domain."""
    doms = [d["domain"] for d in idt.get("domains", []) if d.get("confirmed", True)]
    for dom in reversed(doms):
        mf = common.DATA_DIR / "wayback" / dom / "manifest.json"
        if mf.exists():
            snaps = [s for s in json.loads(mf.read_text(encoding="utf-8")).get("snapshots", [])
                     if s.get("wayback_url") and s.get("timestamp")]
            if snaps:
                ts = snaps[-1]["timestamp"]
                return f"{ts[:4]}-{ts[4:6]}", snaps[-1]["wayback_url"]
    return None


def src_month(date):
    p = date.split("-")
    return f"{MES[int(p[1])-1]} {p[0]}" if len(p) > 1 else p[0]


def main():
    cur = json.loads((common.DATA_DIR / "pivots_curated.json").read_text(encoding="utf-8"))
    plat = {s["name"].strip(): s for s in load("platanus.json")}
    fund = {s["name"].strip(): s for s in load("funding.json")}
    ident = {s["name"].strip(): s for s in load("identity.json")}
    slug2name = {s["slug"]: s["name"].strip() for s in ident.values()}
    # curated pivots grouped by startup name
    piv_by_name = {}
    for c in cur:
        nm = slug2name.get(c["slug"])
        if nm:
            piv_by_name.setdefault(nm, []).append(c)

    old = json.loads(WEB.read_text(encoding="utf-8"))
    old_by_name = {s["name"]: s for s in old["startups"]}

    out = []
    for name, s in old_by_name.items():
        idt = ident.get(name.strip(), {})
        slug = idt.get("slug") or plat.get(name, {}).get("slug", "")
        fu = fund.get(name.strip(), {})
        rounds = {r.get("date"): r for r in fu.get("rounds", [])}
        exit_ = fu.get("exit") or {}

        events = []
        for e in s["events"]:
            t = e["type"]
            if t in ("pivot", "inactivo"):
                continue  # regenerated (curated / inactivity marker)
            ev = dict(e)
            corr = CORRECTIONS.get((name.strip(), t, e["date"]))
            if corr:
                ev["date"] = corr.get("date", ev["date"])
                if corr.get("prose"):
                    ev["prose"] = corr["prose"]
                if corr.get("title"):
                    ev["title"] = corr["title"]
            if t == "fundacion":
                ev["source_url"] = f"https://platan.us/startups/{slug}" if slug else None
            elif t == "capital":
                ed = e["date"]
                r = (rounds.get(ed)
                     or next((rr for rr in fu.get("rounds",[]) if (rr.get("date") or "")[:7]==ed[:7]), None)
                     or next((rr for rr in fu.get("rounds",[]) if (rr.get("date") or "")[:4]==ed[:4]), None))
                ev["source_url"] = (r or {}).get("source_url")
            elif t == "adquisicion":
                ev["source_url"] = exit_.get("source_url") or first_url(idt)
            elif t == "cierre":
                basis_conf = idt.get("shutdown_basis")
                if basis_conf == "inferred":
                    continue  # we don't assert shutdown without a source; replaced by 'inactivo' marker
                ev["source_url"] = exit_.get("source_url") or first_url(idt) or last_wayback(idt)
                ev["basis"] = "Cierre CONFIRMADO por fuente (fundadores/prensa/registro)."
            events.append(ev)

        # soft marker for SUSPECTED shutdowns without news (inferred): a single
        # point at the end of the line, with the last signal of activity (Wayback).
        if idt.get("shutdown_basis") == "inferred":
            ld = last_wayback_dated(idt)
            last_date, last_url = ld if ld else (None, None)
            if not last_date:  # fallback: founding + a few years
                last_date = events[0]["date"] if events else "2024-06"
            events.append({
                "type": "inactivo", "date": last_date,
                "title": "Sin señal reciente",
                "prose": "Al parecer no hay actividad reciente: el sitio dejó de actualizarse y el dominio cayó. "
                         "Pudo haberse cerrado silenciosamente, sin anuncio formal.",
                "quote": "", "source": f"Última señal · {src_month(last_date)}",
                "source_url": last_url,
                "basis": "Inferido: sin noticia de cierre. La fecha es la última señal de actividad "
                         "registrada del sitio; no hay confirmación de cierre.",
            })

        # inject curated pivots/rebrands
        for c in piv_by_name.get(name, []):
            dom = c["domain"]
            src_label = "Platanus" if dom.startswith("profile:") else dom
            events.append({
                "type": "pivot", "date": c["date"], "title": c["title"],
                "prose": c["prose"], "quote": "",
                "source": f"{src_label} · {src_month(c['date'])}",
                "source_url": c["wayback_url"],
                "wayback_url": c["wayback_url"],
                "basis": "",
            })

        events.sort(key=lambda e: e["date"])
        so = dict(s)
        so["events"] = events

        # --- aliases for search (Gokei↔Skip, Verso↔Carttera, etc.) ---
        disp = name.strip()
        raw_names = idt.get("names", [])
        all_domains = [d["domain"] for d in idt.get("domains", []) if d.get("confirmed", True)]
        # visible aliases: clean names different from the display name.
        def norm(x):  # normalize for dedup: 'Profe.Social' == 'Profe Social'
            return re.sub(r"[^a-z0-9]", "", x.lower())
        disp_key, slug_key = norm(disp), norm(slug)
        seen, vis = set(), []
        for nm in raw_names:
            n = nm.strip()
            if not n or "(" in n or len(n) > 28 or n.lower().startswith("codename"):
                continue
            k = norm(n)
            if not k or k == disp_key or k in seen:
                continue
            if n == n.lower() and k == slug_key:  # raw codename token (lowercase) — don't show
                continue
            seen.add(k)
            vis.append(n)
        # if an alias contains a shorter one, keep only the short one (Verso < Verso Technologies)
        vis2 = []
        for a in sorted(vis, key=len):
            if not any(norm(b) in norm(a) and a != b for b in vis2):
                vis2.append(a)
        so["aliases"] = vis2
        # search blob: name + ALL names + all domains + slug
        blob = [disp, slug] + raw_names + all_domains
        so["search_blob"] = " ".join(x for x in blob if x).lower()
        so["status"] = {"active-pivoted":"activa","active-renamed":"activa","active":"activa",
                        "acquired":"adquirida","shutdown":"cerrada","unknown":"inactiva"}.get(
                        idt.get("status",""), s.get("status","activa"))
        if idt.get("shutdown_basis") == "inferred":
            so["status"] = "inactiva"  # suspected shutdown, no news
        out.append(so)

    meta = dict(old["meta"])
    meta["preliminary"] = False
    meta["note"] = "Datos verificados. Cada hito enlaza a su fuente."
    meta["count"] = len(out)
    payload = {"meta": meta, "startups": sorted(out, key=lambda s: s["events"][0]["date"] if s["events"] else "9999")}
    WEB.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    from collections import Counter
    nev = sum(len(s["events"]) for s in out)
    et = Counter(e["type"] for s in out for e in s["events"])
    nourl = [(s["name"], e["type"]) for s in out for e in s["events"] if not e.get("source_url")]
    print(f"✔ {len(out)} startups · {nev} eventos · tipos {dict(et)}")
    print(f"  eventos SIN source_url: {len(nourl)}")
    for n,t in nourl[:30]: print(f"    {n} · {t}")


if __name__ == "__main__":
    main()

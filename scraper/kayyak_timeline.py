"""Adds the Kayyak Ventures startups to web/src/data/timeline.json.

Reads the artifacts that passed the trajectory loop (data/audit/<slug>/final.json)
and writes one timeline entry per startup with the same shape as the Platanus
ones (name, domain, status, tag, events[], aliases, search_blob) plus
`portafolio: "kayyak"`. Re-running replaces the previous Kayyak entries; the
Platanus entries are left untouched. Startups without final.json (pending human
review) are skipped.

Event mapping: founding -> fundacion · funding -> capital · pivot/rebrand as is ·
shutdown with an acquirer -> adquisicion (confirmed closures -> cierre).

Usage: uv run python kayyak_timeline.py
"""

from __future__ import annotations

import json
import re
import unicodedata
from urllib.parse import urlparse

import common

WEB = common.ROOT / "web" / "src" / "data" / "timeline.json"
AUDIT = common.DATA_DIR / "audit"
MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# Display names as the companies write them (the fund's site and the loop
# sometimes normalize casing).
NAMES = {
    "1doc3": "1DOC3", "coworklatam": "Co-Work Latam", "sofiasalud": "Sofía",
    "timining": "TIMining", "wheeltheworld": "Wheel the World", "wherex": "WherEx",
}
# Same vocabulary as the Platanus tags; new ones only where none fits.
TAGS = {
    "1doc3": "Healthtech", "agendapro": "SaaS", "agrourbana": "Agtech", "aptuno": "Proptech",
    "chipax": "Fintech", "colektia": "Fintech", "coworklatam": "Proptech", "cytovale": "Healthtech",
    "enerlink": "Energía", "f4f": "Agtech", "fairplay": "Fintech", "foodology": "Foodtech",
    "fracttal": "SaaS", "futurebeyond": "AI", "galgo": "Fintech", "healthatom": "Healthtech",
    "henry": "Edtech", "humatics": "Robótica", "marco": "Fintech", "miroculus": "Biotech",
    "pulsar": "Industria", "rankmi": "HR Tech", "sofiasalud": "Insurtech", "timining": "Minería",
    "vmetrix": "Fintech", "webdox": "Legaltech", "wheeltheworld": "Travel", "wherex": "Marketplace",
    "xepelin": "Fintech",
}
EXTRA_ALIASES = {"wherex": ["AQMarket"]}
# Productos que coexisten con la marca: se buscan, pero no son nombres anteriores.
SEARCH_ONLY = {"healthatom": ["Dentalink", "Medilink"]}
OUTLETS = {
    "df.cl": "Diario Financiero", "prnewswire.com": "PR Newswire", "startupslatam.com": "Startups Latam",
    "lavca.org": "LAVCA", "cbinsights.com": "CB Insights", "forbes.com.mx": "Forbes México",
    "forbes.co": "Forbes Colombia", "biospace.com": "BioSpace", "techcrunch.com": "TechCrunch",
    "diariosustentable.com": "Diario Sustentable", "expandemineria.cl": "Expande Minería",
    "fintechile.org": "FinteChile", "antler.co": "Antler", "latercera.com": "La Tercera",
    "ycombinator.com": "Y Combinator", "bloomberglinea.com": "Bloomberg Línea", "accion.org": "Accion",
    "bbva.com": "BBVA", "larepublica.co": "La República", "latamfintech.co": "LatamFintech",
    "elmostrador.cl": "El Mostrador", "hbs.edu": "Harvard Business School", "elespectador.com": "El Espectador",
    "portafolio.co": "Portafolio", "latamlist.com": "LatamList", "endeavor.org": "Endeavor",
    "colombia.endeavor.org": "Endeavor Colombia", "iproup.com": "iProUP", "lexlatin.com": "LexLatin",
    "startupchile.org": "Start-Up Chile", "eldefinido.cl": "El Definido", "bbvaspark.com": "BBVA Spark",
    "linkedin.com": "LinkedIn", "es.linkedin.com": "LinkedIn", "cl.linkedin.com": "LinkedIn",
    "medium.com": "Medium", "crunchbase.com": "Crunchbase", "kayyakventures.com": "Kayyak Ventures",
    "static1.squarespace.com": "Kayyak Ventures", "dplnews.com": "DPL News", "prweb.com": "PRWeb",
}
STAGE = {
    "pre-seed": "una ronda pre-semilla", "seed": "una ronda semilla", "series-a": "una Serie A",
    "series-b": "una Serie B", "series-c": "una Serie C", "series-d": "una Serie D",
    "bridge": "una ronda puente", "secondary": "una venta secundaria", "buyback": "una recompra",
    "restructuring": "una reestructuración",
}


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def host(url: str) -> str:
    return urlparse(url).netloc.lower().split(":")[0].removeprefix("www.")


def wayback_origin(url: str) -> str | None:
    m = re.match(r"https?://web\.archive\.org/web/\d+[a-z_]*/(.+)", url)
    return host(m.group(1) if "://" in m.group(1) else "http://" + m.group(1)) if m else None


def month_label(date: str) -> str:
    y, *m = date.split("-")
    return f"{MES[int(m[0]) - 1]} {y}" if m else y


def source_label(url: str | None, date: str) -> str:
    if not url:
        return ""
    origin = wayback_origin(url)
    if origin:
        return f"{origin} · {month_label(date)}"
    h = host(url)
    return OUTLETS.get(h) or OUTLETS.get(".".join(h.split(".")[-2:])) or h


def money(x: float | None) -> str:
    if not x:
        return ""
    if x >= 1e6:
        v = f"{x / 1e6:.1f}".replace(".", ",").removesuffix(",0")
        return f"US${v}M"
    if x >= 1e3:
        return f"US${round(x / 1e3)}K"
    return f"US${int(x)}"


def join(names: list[str], cap: int = 3) -> str:
    names = [n for n in names if n and n.lower() != "unknown"]
    if len(names) > cap:
        return ", ".join(names[:cap]) + " y otros"
    if len(names) <= 1:
        return names[0] if names else ""
    return ", ".join(names[:-1]) + " y " + names[-1]


def capital_prose(name: str, p: dict) -> str:
    ft, inv, amt = p.get("funding_type"), join(p.get("investors") or []), money(p.get("amount_usd"))
    con = f" con {inv}" if inv else ""
    if ft == "accelerator":
        return f"{name} entró a {inv or 'un programa de aceleración'}" + (f" y recibió {amt}." if amt else ".")
    if ft == "grant":
        return f"{name} recibió {amt or 'un aporte'} no reembolsable" + (f" de {inv}." if inv else ".")
    if ft == "strategic":
        return f"{inv} hizo una inversión estratégica en {name}" + (f" por {amt}." if amt else ".")
    if ft == "undisclosed":
        return f"{inv or 'Kayyak Ventures'} invirtió en {name}; la etapa y el monto no se informaron."
    if ft == "debt":
        return f"{name} obtuvo " + (f"deuda por {amt}" if amt else "financiamiento de deuda") + (f" de {inv}." if inv else ".")
    stage = STAGE.get(ft, "una ronda")
    return f"{name} levantó {stage}" + (f" de {amt}" if amt else "") + f"{con}."


def entry(slug: str, art: dict, ident: dict) -> dict:
    name = NAMES.get(slug) or art.get("display_name") or ident["name"]
    former = (ident.get("names", [])[1:] + EXTRA_ALIASES.get(slug, []))[:1]
    rebrand = next((p["date"] for p in art.get("phases", []) if p["type"] == "rebrand"), None)

    def name_at(date: str) -> str:
        """Antes del rebrand, la empresa se llamaba distinto (Migrante, AQMarket)."""
        return former[0] if former and rebrand and date < rebrand else name

    f = art["founding"]
    events = [{
        "type": "fundacion", "date": f["date"], "title": f"Nace {name_at(f['date'])}",
        "prose": f["product_prose"], "source": source_label(f.get("source_url"), f["date"]),
        "basis": "", "source_url": f.get("source_url"),
    }]
    kayyak_seen = False
    status = "activa"
    for p in art.get("phases", []):
        t, date = p["type"], p["date"]
        if t in ("pivot", "rebrand"):
            url = p.get("source_url")
            events.append({
                "type": t, "date": date, "title": p["title"], "prose": p["product_prose"], "quote": "",
                "source": source_label(url, date), "source_url": url,
                "wayback_url": url if url and "web.archive.org" in url else None, "basis": "",
            })
        elif t == "funding":
            prose = capital_prose(name_at(date), p)
            title = (p.get("title") or "").strip()
            if not p.get("amount_usd") and re.search(r"\d", title) and "kayyak" not in title.lower():
                # Sin monto en USD, el título trae el dato concreto (CLP, MXN, programa).
                prose = f"{prose[:-1]}: {title[0].lower() + title[1:]}."
            if not kayyak_seen and any("kayyak" in (i or "").lower() for i in p.get("investors") or []):
                # La entrada de Kayyak cuenta además en qué estaba el producto.
                kayyak_seen = True
                prose = f"{prose} {p['product_prose']}"
            events.append({
                "type": "capital", "date": date, "title": p.get("title") or "Levantó capital",
                "prose": prose, "source": source_label(p.get("source_url"), date),
                "basis": "", "source_url": p.get("source_url"),
            })
        elif t == "shutdown":
            acquired = "adquisición" in (p.get("title") or "").lower() or "adquiri" in (p.get("product_prose") or "").lower()
            status = "adquirida" if acquired else "cerrada"
            events.append({
                "type": "adquisicion" if acquired else "cierre", "date": date, "title": p.get("title") or "Cierre",
                "prose": p["product_prose"], "source": source_label(p.get("source_url"), date),
                "basis": "", "source_url": p.get("source_url"),
            })
    sd = art.get("shutdown")
    if isinstance(sd, dict) and sd.get("date"):
        if sd.get("confirmed"):
            status = "cerrada"
            events.append({"type": "cierre", "date": sd["date"], "title": "Cierre", "prose": sd.get("basis", ""),
                           "source": source_label(sd.get("source_url"), sd["date"]), "basis": "",
                           "source_url": sd.get("source_url")})
        else:
            status = "inactiva"
    events.sort(key=lambda e: e["date"])

    live = art.get("live_state") or {}
    domain = host(live["url_actual"]) if live.get("url_actual") else ident["domains"][-1]["domain"].split("/")[0]
    if slug == "miroculus":
        domain = "miroculus.com"  # hoy redirige al adquirente
    aliases = [n for n in ident.get("names", [])[1:] if n.lower() != name.lower()] + EXTRA_ALIASES.get(slug, [])
    doms = [d["domain"] for d in ident.get("domains", [])] + art.get("domains_chain", [])
    blob = [name, slug, *aliases, *SEARCH_ONLY.get(slug, []), *doms, domain]
    return {
        "name": name, "domain": domain, "status": status, "tag": TAGS.get(slug, ""),
        "events": events, "aliases": aliases,
        "search_blob": " ".join(dict.fromkeys(x.lower() for x in blob if x)),
        "portafolio": "kayyak",
    }


def main() -> None:
    ident = {s["slug"]: s for s in json.loads((common.DATA_DIR / "identity.json").read_text(encoding="utf-8"))["startups"]}
    tl = json.loads(WEB.read_text(encoding="utf-8"))
    platanus = [s for s in tl["startups"] if s.get("portafolio", "platanus") == "platanus"]
    taken = {slugify(s["name"]) for s in platanus}

    kayyak, skipped = [], []
    for slug in ident:
        final = AUDIT / slug / "final.json"
        if not final.exists():
            skipped.append(slug)
            continue
        e = entry(slug, json.loads(final.read_text(encoding="utf-8")), ident[slug])
        if slugify(e["name"]) in taken:
            raise SystemExit(f"slug repetido con Platanus: {e['name']}")
        kayyak.append(e)

    out = platanus + kayyak
    out.sort(key=lambda s: s["events"][0]["date"] if s["events"] else "9999")
    tl["startups"] = out
    tl["meta"]["count"] = len(out)
    first = min(int(e["date"][:4]) for s in out for e in s["events"])
    tl["meta"]["range"] = {"start": float(first), "end": 2027.0}
    tl["meta"]["ticks"] = list(range(first, 2027))
    WEB.write_text(json.dumps(tl, ensure_ascii=False, indent=2), encoding="utf-8")

    nev = sum(len(s["events"]) for s in kayyak)
    print(f"✔ {len(kayyak)} startups de Kayyak ({nev} eventos) + {len(platanus)} de Platanus → {WEB.name}")
    print(f"  eje {first}–2027 · sin final.json (pendientes): {', '.join(skipped) or '—'}")
    nourl = [(s["name"], e["type"]) for s in kayyak for e in s["events"] if not e.get("source_url")]
    print(f"  eventos sin source_url: {len(nourl)} {nourl[:5]}")


if __name__ == "__main__":
    main()

"""Kayyak Ventures scraper (https://www.kayyakventures.com).

Kayyak is a VC fund (Seed to Series B), not an accelerator: there are no
batches. The closest thing to a cohort is the month a startup first shows up
in the portfolio, which we reconstruct from the Wayback captures of the home.

The site had two eras:
- 2021-2024: a single page with a portfolio carousel (`.project__title`,
  `.project__quote`, `.project__quoter`, `.project__mision`, `href="/#slug"`).
- 2025+: Squarespace, one page per startup (`/<slug>`) with text blocks
  labelled HQ / Founders / Website.

Startups that vanish from the carousel are matched against the current
portfolio by their quoter (the founder quoted on the slide): same quoter under
a new name = rebrand candidate (e.g. Migrante -> Galgo), otherwise departed.

Output: data/kayyak.json (+ home captures cached in data/wayback_kayyak/)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import date

from selectolax.parser import HTMLParser

import common

BASE = "https://www.kayyakventures.com"
CDX = "https://web.archive.org/cdx/search/cdx"
WAYBACK_DIR = common.DATA_DIR / "wayback_kayyak"
# home links that are not portfolio pages (team pages are dropped later: they
# have no HQ block)
NON_PORTFOLIO = {"", "home", "contact", "contacto", "denuncias", "cart", "jobs"}


@dataclass
class Sighting:
    month: str  # YYYYMM
    url: str  # Wayback capture, or the live page for the current month
    name: str
    quoter: str | None = None
    mission: str | None = None


@dataclass
class Startup:
    accelerator: str = "Kayyak Ventures"
    name: str = ""
    slug: str = ""
    status: str = "current"  # current | departed
    hq: str | None = None
    country: str | None = None
    chilean_hq: bool = False
    website: str | None = None
    description: str | None = None
    founders: list[str] = field(default_factory=list)
    profile_url: str | None = None
    first_seen: str | None = None  # YYYYMM, upper bound (Wayback has gaps)
    first_seen_url: str | None = None
    last_seen: str | None = None
    former_names: list[str] = field(default_factory=list)
    sightings: list[Sighting] = field(default_factory=list)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _text(node) -> str:
    return " ".join(node.text(separator=" ").split()) if node else ""


def parse_detail(htmltext: str) -> dict:
    """HQ / Founders / Website / description from a Squarespace startup page."""
    tree = HTMLParser(htmltext)
    title = _text(tree.css_first("title"))
    out: dict = {"name": title.split(" — ")[0].strip(), "founders": []}
    free: list[str] = []
    for block in tree.css("[data-sqsp-text-block-content]"):
        strong = block.css_first("strong")
        label = _text(strong).lower()
        if label in {"hq", "founder", "founders", "website"}:
            raw = block.html or ""
            raw = raw.split("</strong>", 1)[-1]
            lines = [
                " ".join(HTMLParser(part).text().split())
                for part in re.split(r"<br\s*/?>", raw)
            ]
            lines = [x for x in lines if x]
            if label == "hq":
                out["hq"] = lines[0] if lines else None
            elif label == "website":
                out["website"] = lines[0] if lines else None
            else:
                out["founders"] = lines
        else:
            t = _text(block)
            if t and t != out["name"]:
                free.append(t)
    if free:
        out["description"] = "\n\n".join(free)
    return out


def portfolio_slugs(home_html: str) -> list[str]:
    slugs = []
    for a in HTMLParser(home_html).css("a[href]"):
        href = a.attributes.get("href") or ""
        m = re.fullmatch(r"/([a-z0-9\-]+)/?", href)
        if m and m.group(1) not in NON_PORTFOLIO and m.group(1) not in slugs:
            slugs.append(m.group(1))
    return slugs


def parse_carousel(htmltext: str) -> list[dict]:
    """Slides of the 2021-2024 single-page site."""
    slides = []
    for p in HTMLParser(htmltext).css(".project__wrapper"):
        name = _text(p.css_first(".project__title"))
        if not name:
            continue
        more = p.css_first(".project__more-button")
        anchor = (more.attributes.get("href") or "") if more else ""
        slides.append(
            {
                "name": name,
                "anchor": anchor.split("#")[-1] or None,
                "quoter": _text(p.css_first(".project__quoter")) or None,
                "mission": _text(p.css_first(".project__mision")) or None,
            }
        )
    return slides


def wayback_months(http) -> list[str]:
    resp = common.polite_get(
        http,
        CDX,
        params={
            "url": "kayyakventures.com",
            "fl": "timestamp",
            "filter": "statuscode:200",
            "collapse": "timestamp:6",
        },
    )
    return resp.text.split()


def fetch_capture(http, ts: str) -> str:
    WAYBACK_DIR.mkdir(parents=True, exist_ok=True)
    path = WAYBACK_DIR / f"{ts[:6]}.html"
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore")
    resp = common.polite_get(http, f"https://web.archive.org/web/{ts}id_/{BASE}/", delay=1.5)
    path.write_text(resp.text, encoding="utf-8")
    return resp.text


def match_slug(name: str, anchor: str | None, slugs: list[str]) -> str | None:
    for key in filter(None, (anchor, norm(name))):
        k = norm(key)
        for s in slugs:
            if norm(s) == k:
                return s
        for s in slugs:
            if norm(s).startswith(k) or k.startswith(norm(s)):
                return s
    return None


def scrape() -> list[Startup]:
    with common.client() as http:
        print(f"GET {BASE}")
        home = common.polite_get(http, BASE).text
        current: dict[str, Startup] = {}
        for slug in portfolio_slugs(home):
            url = f"{BASE}/{slug}"
            info = parse_detail(common.polite_get(http, url).text)
            if not info.get("hq"):
                continue  # team member page
            hq = info["hq"]
            country = hq.split(",")[-1].strip()
            current[slug] = Startup(
                name=info["name"],
                slug=slug,
                hq=hq,
                country=country,
                chilean_hq=norm(country) == "chile",
                website=info.get("website"),
                description=info.get("description"),
                founders=info["founders"],
                profile_url=url,
            )
            print(f"  {info['name']} ({slug}) · {hq}")

        # first/last sightings from the Wayback captures of the home
        departed: dict[str, Startup] = {}
        months = wayback_months(http)
        print(f"\nWayback: {len(months)} capturas mensuales")
        for ts in months:
            wb_url = f"https://web.archive.org/web/{ts}/{BASE}/"
            try:
                htmltext = fetch_capture(http, ts)
            except Exception as exc:  # noqa: BLE001
                print(f"  ! {ts[:6]} falló: {exc}")
                continue
            slides = parse_carousel(htmltext)
            if slides:
                for sl in slides:
                    sighting = Sighting(ts[:6], wb_url, sl["name"], sl["quoter"], sl["mission"])
                    slug = match_slug(sl["name"], sl["anchor"], list(current))
                    target = current.get(slug) if slug else None
                    if target is None:
                        key = norm(sl["name"])
                        target = departed.setdefault(
                            key, Startup(name=sl["name"], slug=norm(sl["anchor"] or key), status="departed")
                        )
                    target.sightings.append(sighting)
            else:
                present = set(portfolio_slugs(htmltext)) & set(current)
                for slug in present:
                    current[slug].sightings.append(Sighting(ts[:6], wb_url, current[slug].name))
            print(f"  {ts[:6]}: {len(slides) or 'squarespace'}")

        # same quoter, different name -> the departed one is a former name
        quoter_of = {
            norm(s.quoter): st
            for st in current.values()
            for s in st.sightings
            if s.quoter
        }
        for key, dep in list(departed.items()):
            quoters = {norm(s.quoter) for s in dep.sightings if s.quoter}
            heir = next((quoter_of[q] for q in quoters if q in quoter_of), None)
            if heir is None:
                heir = _heir_by_founder(dep, current.values())
            if heir is not None:
                heir.former_names.append(dep.name)
                heir.sightings = sorted(dep.sightings + heir.sightings, key=lambda s: s.month)
                del departed[key]

        # the live site counts as a sighting (only source for the newest additions)
        today = date.today().strftime("%Y%m")
        for st in current.values():
            st.sightings.append(Sighting(today, st.profile_url or BASE, st.name))

        startups = list(current.values()) + list(departed.values())
        for st in startups:
            st.sightings.sort(key=lambda s: s.month)
            if st.sightings:
                st.first_seen = st.sightings[0].month
                st.first_seen_url = st.sightings[0].url
                st.last_seen = st.sightings[-1].month
        return sorted(startups, key=lambda s: (s.first_seen or "999999", s.name))


def _heir_by_founder(dep: Startup, current) -> Startup | None:
    """Fallback: the departed slide's quoter is a founder of a current startup."""
    quoters = {norm(s.quoter) for s in dep.sightings if s.quoter}
    for st in current:
        if quoters & {norm(f) for f in st.founders}:
            return st
    return None


def main() -> None:
    startups = scrape()
    payload = {
        "accelerator": "Kayyak Ventures",
        "source": BASE,
        "note": "VC fund, no batches: first_seen is the first month in the portfolio "
        "(upper bound, Wayback has gaps).",
        "count": len(startups),
        "startups": [asdict(s) for s in startups],
    }
    path = common.save_json("kayyak.json", payload)
    cur = [s for s in startups if s.status == "current"]
    cl = [s for s in cur if s.chilean_hq]
    print(f"\n✔ {len(cur)} en portafolio ({len(cl)} con HQ en Chile) · "
          f"{len(startups) - len(cur)} salieron")
    for s in startups:
        flag = "CL" if s.chilean_hq else (s.country or "--")[:3]
        extra = f"  (antes: {', '.join(s.former_names)})" if s.former_names else ""
        print(f"  {s.first_seen}–{s.last_seen}  {flag:4} {s.status:8} {s.name}{extra}")
    print(f"  guardado en {path}")


if __name__ == "__main__":
    main()

"""Platanus Ventures scraper (https://platan.us/portafolio).

The portfolio page is a server-rendered Vue component that injects two JSON
arrays (`:batches` and `:companies`). The startups with their founders live in
the detail pages `/startups/<slug>`. Everything is static HTML: no headless
browser is needed.

Output: data/platanus.json
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field, asdict
from typing import Any

from selectolax.parser import HTMLParser

import common

BASE = "https://platan.us"
PORTFOLIO_URL = f"{BASE}/portafolio"


@dataclass
class Founder:
    name: str
    role: str | None = None
    socials: dict[str, str] = field(default_factory=dict)


@dataclass
class Startup:
    accelerator: str = "Platanus"
    name: str = ""
    slug: str = ""
    batch: str | None = None  # batch_season, e.g. "2022-1"
    batch_name: str | None = None  # e.g. "Generación 2022-1"
    country: str | None = None
    industry: str | None = None
    website: str | None = None
    slogan: str | None = None
    description: str | None = None
    profile_url: str = ""
    founders: list[Founder] = field(default_factory=list)


def parse_portfolio(htmltext: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (batches, companies) from the portfolio HTML."""
    unescaped = html.unescape(htmltext)
    batches = common.extract_camelize_array(unescaped, "batches")
    companies = common.extract_camelize_array(unescaped, "companies")
    return batches, companies


def _founder_socials(node) -> dict[str, str]:
    """Extracts the founder's socials from the `:social-media` prop of the web component."""
    raw = node.attributes.get(":social-media") if node else None
    if not raw:
        return {}
    obj = common.extract_camelize_object(html.unescape(raw))
    # filter out empty / None values and normalize to str
    return {k: str(v) for k, v in obj.items() if v}


def parse_founders(detail_html: str) -> list[Founder]:
    tree = HTMLParser(detail_html)
    # locate the <h2>Founders</h2>
    section = None
    for h2 in tree.css("h2"):
        if h2.text(strip=True).lower() == "founders":
            section = h2.parent
            break
    if section is None:
        return []

    founders: list[Founder] = []
    # each founder is a `div.flex.flex-col.gap-3` card within the grid
    for card in section.css("div.flex.flex-col.gap-3"):
        h3 = card.css_first("h3")
        if h3 is None:
            continue
        name = h3.text(strip=True)
        if not name or any(f.name == name for f in founders):
            continue
        socials = _founder_socials(card.css_first("kalio-social-media-icons"))
        # the role is in a <p>; the HTML nests <p> invalidly, so we take
        # the first <p> with real text inside the card
        role = None
        for p in card.css("p"):
            t = " ".join(p.text(separator=" ").split())
            if t:
                role = t
                break
        founders.append(Founder(name=name, role=role, socials=socials))
    return founders


def scrape() -> list[Startup]:
    with common.client() as http:
        print(f"GET {PORTFOLIO_URL}")
        resp = common.polite_get(http, PORTFOLIO_URL)
        batches, companies = parse_portfolio(resp.text)
        print(f"  batches={len(batches)}  companies={len(companies)}")

        startups: list[Startup] = []
        for i, c in enumerate(companies, 1):
            batch = c.get("batch") or {}
            slug = c.get("slug", "")
            s = Startup(
                name=c.get("name", ""),
                slug=slug,
                batch=batch.get("batch_season"),
                batch_name=batch.get("name"),
                country=c.get("country"),
                website=c.get("webpage"),
                slogan=c.get("slogan"),
                description=c.get("description"),
                profile_url=f"{BASE}{c.get('profile_path', '/startups/' + slug)}",
            )
            print(f"  [{i}/{len(companies)}] {s.name} ({slug})")
            try:
                detail = common.polite_get(http, s.profile_url)
                s.founders = parse_founders(detail.text)
            except Exception as exc:  # noqa: BLE001
                print(f"      ! detalle falló: {exc}")
            startups.append(s)
        return startups


def main() -> None:
    startups = scrape()
    payload = {
        "accelerator": "Platanus",
        "source": PORTFOLIO_URL,
        "count": len(startups),
        "startups": [asdict(s) for s in startups],
    }
    path = common.save_json("platanus.json", payload)
    n_founders = sum(len(s.founders) for s in startups)
    with_site = sum(1 for s in startups if s.website)
    print(f"\n✔ {len(startups)} startups · {n_founders} founders · {with_site} con web")
    print(f"  guardado en {path}")


if __name__ == "__main__":
    main()

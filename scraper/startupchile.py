"""Start-Up Chile scraper (https://startupchile.org/portafolio/).

The public portfolio is a Vue app that lists the companies via the WordPress
endpoint `admin-ajax.php?action=startups` (paginated JSON). The detail of each
company lives at `/portafolio/<slug>/` with founder(s), landing page and tags
(program + category). The year is obtained from the `year` filter of the same
endpoint.

NOTE: the public portfolio only exposes a curated selection (~20 startups,
including emblematic cases like NotCo); Start-Up Chile has accelerated 2500+
historically, but the rest is not published on this page.

Output: data/startupchile.json
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from urllib.parse import urlparse

from selectolax.parser import HTMLParser

import common

BASE = "https://startupchile.org"
AJAX = f"{BASE}/cms/wp-admin/admin-ajax.php"
YEARS = ("2020", "2021", "2022")


@dataclass
class Founder:
    name: str
    role: str | None = None
    socials: dict[str, str] = field(default_factory=dict)


@dataclass
class Startup:
    accelerator: str = "Start-Up Chile"
    name: str = ""
    slug: str = ""
    batch: str | None = None  # program year, e.g. "2021"
    batch_name: str | None = None
    country: str | None = None  # not exposed in the public portfolio
    industry: str | None = None
    website: str | None = None
    slogan: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)  # program + category
    profile_url: str = ""
    founders: list[Founder] = field(default_factory=list)


def _slug_from_link(link: str) -> str:
    return urlparse(link).path.strip("/").split("/")[-1]


def fetch_list(http) -> list[dict]:
    """Full list of companies from the public portfolio."""
    resp = common.polite_get(
        http, AJAX, params={"action": "startups", "ppp": 200, "page": 1}
    )
    return resp.json().get("posts", [])


def fetch_year_map(http) -> dict[str, str]:
    """Map slug -> year, using the `year` filter of the endpoint."""
    year_of: dict[str, str] = {}
    for year in YEARS:
        resp = common.polite_get(
            http, AJAX, params={"action": "startups", "ppp": 200, "year": year}
        )
        for post in resp.json().get("posts", []):
            year_of[_slug_from_link(post["link"])] = year
    return year_of


def parse_detail(html_text: str, startup: Startup) -> None:
    tree = HTMLParser(html_text)

    link = tree.css_first("a.hero-tertiary__link")
    if link:
        href = link.attributes.get("href")
        if href:
            startup.website = href.strip()

    tags = [
        t.text(strip=True)
        for t in tree.css("div.hero-tertiary__tag")
        if t.text(strip=True)
    ]
    startup.tags = tags

    desc = tree.css_first("div.hero-tertiary__paragraph")
    if desc:
        startup.description = " ".join(desc.text(separator=" ").split())

    # founders: the detail uses several inconsistent prefixes:
    #   "Founder: X", "Founders: X & Y", "Founded by: A, B and C".
    # (some pages only carry an email or carry no founders at all)
    for p in tree.css("div.hero-tertiary__mail p, p.paragraph"):
        txt = " ".join(p.text(separator=" ").split())
        m = re.match(r"(?:founders?|founded\s+by)\s*:\s*(.+)", txt, re.IGNORECASE)
        if m:
            startup.founders = [
                Founder(name=n.strip())
                for n in re.split(r"\s*(?:,|&|\sand\s|\sy\s)\s*", m.group(1))
                if n.strip()
            ]
            break


def scrape() -> list[Startup]:
    with common.client() as http:
        print(f"GET {AJAX} (action=startups)")
        posts = fetch_list(http)
        year_of = fetch_year_map(http)
        print(f"  {len(posts)} startups públicas")

        startups: list[Startup] = []
        for i, post in enumerate(posts, 1):
            slug = _slug_from_link(post["link"])
            s = Startup(
                name=post.get("title", ""),
                slug=slug,
                batch=year_of.get(slug),
                slogan=(post.get("paragraph") or "").strip() or None,
                profile_url=post["link"],
            )
            print(f"  [{i}/{len(posts)}] {s.name} ({slug}) · año {s.batch}")
            try:
                detail = common.polite_get(http, s.profile_url)
                parse_detail(detail.text, s)
            except Exception as exc:  # noqa: BLE001
                print(f"      ! detalle falló: {exc}")
            startups.append(s)
        return startups


def main() -> None:
    startups = scrape()
    payload = {
        "accelerator": "Start-Up Chile",
        "source": f"{BASE}/portafolio/",
        "note": "Sólo el portafolio público curado (~20). SUP ha acelerado 2500+ históricamente.",
        "count": len(startups),
        "startups": [asdict(s) for s in startups],
    }
    path = common.save_json("startupchile.json", payload)
    n_founders = sum(len(s.founders) for s in startups)
    with_site = sum(1 for s in startups if s.website)
    print(f"\n✔ {len(startups)} startups · {n_founders} founders · {with_site} con web")
    print(f"  guardado en {path}")


if __name__ == "__main__":
    main()

"""Mines the Start-Up Chile blog for the cohort announcements ("BIG N").

The public portfolio only exposes ~20 startups, but the blog publishes the full
list of selected companies of each generation (BIG 5, 7, 8, 9, 10, 11, ...), with
name, country (HQ), description and program (Build/Ignite/Growth). These posts are
the best source for the current list and per cohort.

Enumeration: sitemap of the `resources` CPT (where the blog posts live).
Output: data/startupchile_blog.json
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from selectolax.parser import HTMLParser

import common

BASE = "https://startupchile.org"
RESOURCES_SITEMAP = f"{BASE}/wp-sitemap-posts-resources-1.xml"

# Listing posts that exist but WPML does not include in the Spanish sitemap
# (e.g. BIG 7: the sitemap only carries the FAQ, not the list of selected companies).
SEED_URLS = [
    f"{BASE}/blog/esta-es-nuestra-generacion-big-7/",
]

# slugs of posts that are cohort / new-generation announcements
COHORT_SLUG_RE = re.compile(
    r"(big-?\d+"
    r"|seleccionad"
    r"|generacion-big"
    r"|(build|ignite|growth)-\d+-new-generation"  # per-program cohorts (pre-BIG)
    r"|welcomes-a-new-generation"
    r"|conoce-(a-)?las-startups)",
    re.IGNORECASE,
)


PROGRAMS = {"build", "ignite", "growth"}


@dataclass
class BlogStartup:
    accelerator: str = "Start-Up Chile"
    name: str = ""
    country: str | None = None
    website: str | None = None
    description: str | None = None
    program: str | None = None  # Build / Ignite / Growth
    cohort: str | None = None  # e.g. "BIG 10"
    date: str | None = None
    source_url: str = ""


def sitemap_urls(http) -> list[str]:
    resp = common.polite_get(http, RESOURCES_SITEMAP)
    return re.findall(r"<loc>([^<]+)</loc>", resp.text)


def cohort_posts(urls: list[str]) -> list[str]:
    return [u for u in urls if COHORT_SLUG_RE.search(u)]


def _cohort_name(title: str, slug: str) -> str | None:
    hay = f"{title} {slug}"
    m = re.search(r"big\s*-?\s*(\d+)", hay, re.IGNORECASE)
    if m:
        return f"BIG {m.group(1)}"
    m = re.search(r"(build|ignite|growth)-(\d+)-new-generation", slug, re.IGNORECASE)
    if m:
        return f"{m.group(1).title()} {m.group(2)}"
    return None


def _name_of(p) -> tuple[str, str | None] | None:
    """If the <p> starts a startup, returns (name, website|None).

    Covers two blog formats:
      - new (BIG 10/11): `<p><b>Name</b></p>` (all bold, no link)
      - old (BIG 5/8/9): `<p><a href>Name</a> description...</p>`
    """
    ptext = " ".join(p.text(separator=" ").split())
    if not ptext:
        return None

    # old format: link at the start whose text is the name
    a = p.css_first("a")
    if a is not None:
        atext = a.text(strip=True)
        href = (a.attributes.get("href") or "").strip()
        if (
            atext
            and ptext.startswith(atext)
            and 1 <= len(atext) <= 45
            and atext.lower() not in PROGRAMS
            and atext.lower() != "hq"
            and not atext.lower().startswith("http")
        ):
            return atext, (href if href.startswith("http") else None)

    # new format: fully bold and short paragraph
    bold = p.css_first("b, strong")
    if (
        bold is not None
        and ptext == bold.text(strip=True)
        and len(ptext) <= 60
        and not ptext.lower().startswith("hq")
    ):
        return ptext, None

    return None


def parse_post(html_text: str, url: str) -> tuple[str | None, str | None, list[BlogStartup]]:
    tree = HTMLParser(html_text)

    title_node = tree.css_first("h1")
    title = title_node.text(strip=True) if title_node else ""
    cohort = _cohort_name(title, url)

    date = None
    dnode = tree.css_first(".article-header__text-line")
    if dnode:
        date = re.sub(r"\s+", " ", dnode.text(strip=True)) or None

    body = tree.css_first("div.article__body") or tree
    program: str | None = None
    startups: list[BlogStartup] = []
    cur: BlogStartup | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal cur, buf
        if cur is not None:
            # "HQ:" usually comes in its own paragraph (BIG 8-11); otherwise it goes inline
            # after a <br> (BIG 5). We split it so as not to drag in description text.
            desc_items: list[str] = []
            for item in buf:
                if cur.country is None and re.match(r"\s*HQ\b", item, re.IGNORECASE):
                    m = re.search(r"HQ\s*:?\s*([A-Za-zÀ-ÿ]+(?:\s[A-Za-zÀ-ÿ]+)?)", item, re.IGNORECASE)
                    if m:
                        cur.country = m.group(1).strip(" .,-")
                        continue
                desc_items.append(item)
            text = " ".join(" ".join(desc_items).split())
            if cur.country is None:  # HQ inline within the description
                m = re.search(r"HQ\s*:?\s*([A-Za-zÀ-ÿ]+(?:\s[A-Za-zÀ-ÿ]+)?)", text, re.IGNORECASE)
                if m:
                    cur.country = m.group(1).strip(" .,-")
                    text = text[: m.start()] + " " + text[m.end():]
            cur.description = " ".join(text.split()).strip(" :–-·") or None
            startups.append(cur)
        cur = None
        buf = []

    # traverse preserves the document order (css with a comma does not guarantee it)
    for node in body.traverse(include_text=False):
        tag = node.tag
        if tag in ("h2", "h3"):
            label = node.text(strip=True).lower()
            if label in PROGRAMS:
                program = node.text(strip=True).title()
            continue
        if tag != "p":
            continue
        ptext = " ".join(node.text(separator=" ").split())
        if not ptext or ptext.replace("\xa0", "").strip() == "":
            continue
        nm = _name_of(node)
        if nm is not None:
            flush()
            name, website = nm
            cur = BlogStartup(
                name=name,
                website=website,
                program=program,
                cohort=cohort,
                date=date,
                source_url=url,
            )
            remainder = ptext[len(name):].strip(" :–-· ")
            if remainder:
                buf.append(remainder)
        elif cur is not None:
            buf.append(ptext)
    flush()
    return title, cohort, startups


def scrape() -> list[BlogStartup]:
    with common.client() as http:
        urls = cohort_posts(sitemap_urls(http))
        urls = list(dict.fromkeys(urls + SEED_URLS))  # add seeds, without duplicating
        print(f"posts de cohorte encontrados: {len(urls)}")
        all_startups: list[BlogStartup] = []
        for i, url in enumerate(urls, 1):
            resp = common.polite_get(http, url)
            _title, cohort, startups = parse_post(resp.text, url)
            kept = startups if len(startups) >= 5 else []
            flag = "" if kept else "  (omitido: no es un listado)"
            print(f"  [{i}/{len(urls)}] {cohort or '?'} · {len(startups):>3} startups{flag} · {url.split('/')[-2]}")
            all_startups.extend(kept)
        return all_startups


def main() -> None:
    startups = scrape()
    by_cohort: dict[str, int] = {}
    for s in startups:
        by_cohort[s.cohort or "?"] = by_cohort.get(s.cohort or "?", 0) + 1
    payload = {
        "accelerator": "Start-Up Chile",
        "source": "blog (anuncios de cohortes BIG)",
        "count": len(startups),
        "by_cohort": by_cohort,
        "startups": [asdict(s) for s in startups],
    }
    path = common.save_json("startupchile_blog.json", payload)
    print(f"\n✔ {len(startups)} startups en {len(by_cohort)} cohortes")
    print(f"  by_cohort: {by_cohort}")
    print(f"  guardado en {path}")


if __name__ == "__main__":
    main()

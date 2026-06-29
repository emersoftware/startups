"""Platanus enrichment: domains + landing status + social networks.

For each Platanus startup (data/platanus.json) visits its landing page, records
the canonical domain, whether the site is still alive, and extracts the COMPANY's
social media handles from the HTML (footer/header). Public data.

Output: data/platanus_socials.json
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from urllib.parse import urlparse

import httpx
from selectolax.parser import HTMLParser

import common

# platform -> domain pattern in the href
SOCIAL_PATTERNS = {
    "linkedin": r"linkedin\.com",
    "twitter": r"(twitter\.com|x\.com)",
    "instagram": r"instagram\.com",
    "facebook": r"facebook\.com",
    "youtube": r"(youtube\.com|youtu\.be)",
    "tiktok": r"tiktok\.com",
    "github": r"github\.com",
    "telegram": r"(t\.me|telegram\.me)",
    "whatsapp": r"(wa\.me|api\.whatsapp\.com|chat\.whatsapp\.com)",
}
# paths to ignore (share buttons, not profiles)
IGNORE = re.compile(
    r"(sharer|/share|/intent/|/share_|/dialog/|/sharing/|plugins/|platan\.us|platanus)",
    re.IGNORECASE,
)


@dataclass
class SiteInfo:
    name: str
    slug: str
    website: str | None = None
    domain: str | None = None
    final_url: str | None = None
    alive: bool = False
    status: int | None = None
    socials: dict[str, str] = field(default_factory=dict)


def domain_of(url: str | None) -> str | None:
    if not url:
        return None
    netloc = urlparse(url if "//" in url else f"https://{url}").netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc or None


def extract_socials(html_text: str, base_domain: str | None) -> dict[str, str]:
    tree = HTMLParser(html_text)
    found: dict[str, str] = {}
    for a in tree.css("a[href]"):
        href = (a.attributes.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:")) or IGNORE.search(href):
            continue
        for platform, pat in SOCIAL_PATTERNS.items():
            if platform in found:
                continue
            if re.search(pat, href, re.IGNORECASE):
                # normalize protocol-relative and odd relative paths
                if href.startswith("//"):
                    href = "https:" + href
                found[platform] = href
                break
    return found


def enrich_one(http: httpx.Client, name: str, slug: str, website: str | None) -> SiteInfo:
    info = SiteInfo(name=name, slug=slug, website=website, domain=domain_of(website))
    if not website:
        return info
    try:
        resp = common.polite_get(http, website, delay=0.4, retries=2)
        info.status = resp.status_code
        info.alive = resp.is_success
        info.final_url = str(resp.url)
        info.domain = domain_of(info.final_url) or info.domain
        if resp.is_success and "text/html" in resp.headers.get("content-type", ""):
            info.socials = extract_socials(resp.text, info.domain)
    except Exception as exc:  # noqa: BLE001
        info.status = None
        info.alive = False
        info.socials = {"_error": type(exc).__name__}
        info.socials.pop("_error", None)  # we don't store the error as a network
    return info


def main() -> None:
    data = json.loads((common.DATA_DIR / "platanus.json").read_text(encoding="utf-8"))
    startups = data["startups"]
    results: list[SiteInfo] = []
    with common.client(timeout=12.0) as http:
        for i, s in enumerate(startups, 1):
            info = enrich_one(http, s["name"], s["slug"], s.get("website"))
            mark = "·" if info.alive else "✗"
            socials = ",".join(info.socials) or "—"
            print(f"  [{i}/{len(startups)}] {mark} {info.name:18} {info.domain or '—':28} redes: {socials}")
            results.append(info)

    payload = {
        "accelerator": "Platanus",
        "count": len(results),
        "alive": sum(1 for r in results if r.alive),
        "with_socials": sum(1 for r in results if r.socials),
        "startups": [asdict(r) for r in results],
    }
    path = common.save_json("platanus_socials.json", payload)

    # summary by platform
    from collections import Counter
    plat = Counter(p for r in results for p in r.socials)
    print(f"\n✔ {len(results)} startups · {payload['alive']} vivas · "
          f"{payload['with_socials']} con alguna red")
    print("  por plataforma:", dict(plat.most_common()))
    print(f"  guardado en {path}")


if __name__ == "__main__":
    main()

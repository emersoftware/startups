"""Shared utilities for the Chilean startup ecosystem scrapers.

Public data from accelerator portfolios, collected with rate-limiting and an
identifiable User-Agent, for internal analysis.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

# Repo root: .../startup-doxxing-chile
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

USER_AGENT = (
    "startup-ecosystem-research/0.1 (+internal analysis; contact: hola@emersoftware.cl)"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
}


def client(**kwargs: Any) -> httpx.Client:
    """httpx client with polite headers and follow_redirects."""
    opts: dict[str, Any] = dict(
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=30.0,
    )
    opts.update(kwargs)
    return httpx.Client(**opts)


def polite_get(
    http: httpx.Client,
    url: str,
    *,
    delay: float = 0.7,
    retries: int = 3,
    **kwargs: Any,
) -> httpx.Response:
    """GET with rate-limiting and simple exponential retries."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            resp = http.get(url, **kwargs)
            resp.raise_for_status()
            time.sleep(delay)
            return resp
        except (httpx.HTTPError,) as exc:  # noqa: PERF203
            last = exc
            time.sleep(delay * (2**attempt))
    assert last is not None
    raise last


def extract_camelize_array(text: str, prop: str) -> list[dict[str, Any]]:
    """Extracts the JSON array inside `:prop="$filters.camelizeKeys([...])"`.

    Platanus's Vue pages inject data as expressions, not pure JSON; we do
    balanced-bracket matching starting from the prop's token.
    """
    token = f':{prop}="$filters.camelizeKeys('
    start = text.find(token)
    if start == -1:
        raise ValueError(f"prop no encontrada: {prop}")
    open_idx = text.find("[", start)
    depth = 0
    for i in range(open_idx, len(text)):
        ch = text[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return json.loads(text[open_idx : i + 1])
    raise ValueError(f"array sin cerrar para prop: {prop}")


def extract_camelize_object(fragment: str) -> dict[str, Any]:
    """Same as above but for `camelizeKeys({...})` (object)."""
    open_idx = fragment.find("{")
    depth = 0
    for i in range(open_idx, len(fragment)):
        ch = fragment[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(fragment[open_idx : i + 1])
    return {}


def save_json(name: str, payload: Any) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

from __future__ import annotations

from urllib.parse import quote


def quote_path(value: str) -> str:
    return quote(value, safe="")

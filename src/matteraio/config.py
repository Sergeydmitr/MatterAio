from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True, slots=True)
class MattermostConfig:
    base_url: str
    token: str
    timeout: float = 10.0
    connect_timeout: float = 5.0
    max_connections: int = 20
    max_keepalive_connections: int = 10

    @property
    def api_base_url(self) -> str:
        normalized = self.base_url.rstrip("/")
        if normalized.endswith("/api/v4"):
            return normalized
        return f"{normalized}/api/v4"

    @property
    def websocket_url(self) -> str:
        parsed = urlsplit(self.api_base_url)
        scheme = {
            "http": "ws",
            "https": "wss",
            "ws": "ws",
            "wss": "wss",
        }.get(parsed.scheme, parsed.scheme)
        return urlunsplit((scheme, parsed.netloc, f"{parsed.path}/websocket", parsed.query, ""))

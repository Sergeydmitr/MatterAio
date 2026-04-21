from __future__ import annotations

from dataclasses import dataclass


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

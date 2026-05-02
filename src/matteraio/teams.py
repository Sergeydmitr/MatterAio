from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Team, TeamCreateRequest

if TYPE_CHECKING:
    from .client import MattermostClient


class TeamsResource:
    def __init__(self, client: MattermostClient) -> None:
        self._client = client

    async def get(self, team_id: str) -> Team:
        return await self._client._request_model("GET", f"/teams/{team_id}", Team)

    async def get_by_name(self, name: str) -> Team:
        return await self._client._request_model("GET", f"/teams/name/{name}", Team)

    async def create(
        self,
        *,
        name: str,
        display_name: str,
        type: str = "O",
    ) -> Team:
        payload = TeamCreateRequest(
            name=name,
            display_name=display_name,
            type=type,
        )
        return await self._client._request_model(
            "POST",
            "/teams",
            Team,
            json=payload.model_dump(),
        )

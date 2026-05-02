from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Channel, ChannelCreateRequest

if TYPE_CHECKING:
    from .client import MattermostClient


class ChannelsResource:
    def __init__(self, client: MattermostClient) -> None:
        self._client = client

    async def get(self, channel_id: str) -> Channel:
        return await self._client._request_model("GET", f"/channels/{channel_id}", Channel)

    async def get_by_name(self, team_id: str, channel_name: str) -> Channel:
        return await self._client._request_model(
            "GET",
            f"/teams/{team_id}/channels/name/{channel_name}",
            Channel,
        )

    async def create(
        self,
        *,
        team_id: str,
        name: str,
        display_name: str,
        type: str = "O",
        purpose: str | None = None,
        header: str | None = None,
    ) -> Channel:
        payload = ChannelCreateRequest(
            team_id=team_id,
            name=name,
            display_name=display_name,
            type=type,
            purpose=purpose,
            header=header,
        )
        return await self._client._request_model(
            "POST",
            "/channels",
            Channel,
            json=payload.model_dump(exclude_none=True),
        )

    async def list(
        self,
        team_id: str,
        *,
        page: int = 0,
        per_page: int = 60,
    ) -> list[Channel]:
        response = await self._client._request(
            "GET",
            f"/teams/{team_id}/channels",
            params={"page": page, "per_page": per_page},
        )
        return [Channel.model_validate(item) for item in response.json()]

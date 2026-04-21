from __future__ import annotations

from .models import Channel


class ChannelsResource:
    def __init__(self, client: object) -> None:
        self._client = client

    async def get(self, channel_id: str) -> Channel:
        return await self._client._request_model("GET", f"/channels/{channel_id}", Channel)

    async def get_by_name(self, team_id: str, channel_name: str) -> Channel:
        return await self._client._request_model(
            "GET",
            f"/teams/{team_id}/channels/name/{channel_name}",
            Channel,
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

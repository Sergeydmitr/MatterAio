from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from ._paths import quote_path
from .models import Reaction, ReactionCreateRequest, StatusOK

if TYPE_CHECKING:
    from .client import MattermostClient


class ReactionsResource:
    def __init__(self, client: MattermostClient) -> None:
        self._client = client

    async def add(self, *, user_id: str, post_id: str, emoji_name: str) -> Reaction:
        payload = ReactionCreateRequest(
            user_id=user_id,
            post_id=post_id,
            emoji_name=emoji_name,
        )
        return await self._client._request_model(
            "POST",
            "/reactions",
            Reaction,
            json=payload.model_dump(),
        )

    async def remove(self, user_id: str, post_id: str, emoji_name: str) -> StatusOK:
        return await self._client._request_model(
            "DELETE",
            (
                f"/users/{quote_path(user_id)}/posts/{quote_path(post_id)}/"
                f"reactions/{quote_path(emoji_name)}"
            ),
            StatusOK,
        )

    async def list(self, post_id: str) -> builtins.list[Reaction]:
        response = await self._client._request("GET", f"/posts/{quote_path(post_id)}/reactions")
        return self._client._validate_model_list_data(
            response,
            Reaction,
            self._client._response_json(response),
        )

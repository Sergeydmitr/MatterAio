from __future__ import annotations

from typing import TYPE_CHECKING

from .models import User

if TYPE_CHECKING:
    from .client import MattermostClient


class UsersResource:
    def __init__(self, client: MattermostClient) -> None:
        self._client = client

    async def me(self) -> User:
        return await self._client._request_model("GET", "/users/me", User)

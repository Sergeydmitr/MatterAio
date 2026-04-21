from __future__ import annotations

from .models import User


class UsersResource:
    def __init__(self, client: object) -> None:
        self._client = client

    async def me(self) -> User:
        return await self._client._request_model("GET", "/users/me", User)

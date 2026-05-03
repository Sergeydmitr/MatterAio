from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from .exceptions import MattermostError
from .models import LoginResponse, User, UserLoginRequest, UserSearchRequest

if TYPE_CHECKING:
    from .client import MattermostClient


class UsersResource:
    def __init__(self, client: MattermostClient) -> None:
        self._client = client

    async def login(
        self,
        *,
        login_id: str,
        password: str,
        token: str | None = None,
    ) -> LoginResponse:
        self._client._ensure_login_allowed()
        payload = UserLoginRequest(
            login_id=login_id,
            password=password,
            token=token,
        )
        response = await self._client._request(
            "POST",
            "/users/login",
            json=payload.model_dump(exclude_none=True),
        )
        session_token = response.headers.get("Token")
        if session_token is None:
            raise MattermostError("Mattermost login response did not include a Token header.")

        user = User.model_validate(response.json())
        self._client._set_token(session_token)
        self._client._set_bot_session(user)
        return LoginResponse(
            user=user,
            token=session_token,
        )

    async def me(self) -> User:
        return await self._client._request_model("GET", "/users/me", User)

    async def get(self, user_id: str) -> User:
        return await self._client._request_model("GET", f"/users/{user_id}", User)

    async def get_by_username(self, username: str) -> User:
        return await self._client._request_model("GET", f"/users/username/{username}", User)

    async def get_by_email(self, email: str) -> User:
        return await self._client._request_model(
            "GET", f"/users/email/{quote(email, safe='')}", User
        )

    async def search(
        self,
        term: str,
        *,
        team_id: str | None = None,
        not_in_team_id: str | None = None,
        in_channel_id: str | None = None,
        not_in_channel_id: str | None = None,
        in_group_id: str | None = None,
        group_constrained: bool | None = None,
        allow_inactive: bool | None = None,
        without_team: bool | None = None,
        limit: int | None = None,
    ) -> list[User]:
        payload = UserSearchRequest(
            term=term,
            team_id=team_id,
            not_in_team_id=not_in_team_id,
            in_channel_id=in_channel_id,
            not_in_channel_id=not_in_channel_id,
            in_group_id=in_group_id,
            group_constrained=group_constrained,
            allow_inactive=allow_inactive,
            without_team=without_team,
            limit=limit,
        )
        response = await self._client._request(
            "POST",
            "/users/search",
            json=payload.model_dump(exclude_none=True),
        )
        return [User.model_validate(item) for item in response.json()]

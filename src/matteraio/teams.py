from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from .models import (
    StatusOK,
    Team,
    TeamCreateRequest,
    TeamMember,
    TeamMemberAddRequest,
    TeamMemberRolesRequest,
    TeamPatchRequest,
    TeamSearchRequest,
    TeamUpdateRequest,
)

if TYPE_CHECKING:
    from .client import MattermostClient


class TeamsResource:
    def __init__(self, client: MattermostClient) -> None:
        self._client = client

    async def get(self, team_id: str) -> Team:
        return await self._client._request_model("GET", f"/teams/{team_id}", Team)

    async def get_by_name(self, name: str) -> Team:
        return await self._client._request_model("GET", f"/teams/name/{name}", Team)

    async def list(
        self,
        *,
        page: int = 0,
        per_page: int = 60,
        exclude_policy_constrained: bool = False,
    ) -> builtins.list[Team]:
        response = await self._client._request(
            "GET",
            "/teams",
            params={
                "page": page,
                "per_page": per_page,
                "exclude_policy_constrained": exclude_policy_constrained,
            },
        )
        return [Team.model_validate(item) for item in response.json()]

    async def search(
        self,
        term: str,
        *,
        page: int | None = None,
        per_page: int | None = None,
        allow_open_invite: bool | None = None,
        group_constrained: bool | None = None,
        exclude_policy_constrained: bool | None = None,
    ) -> builtins.list[Team]:
        payload = TeamSearchRequest(
            term=term,
            page=page,
            per_page=per_page,
            allow_open_invite=allow_open_invite,
            group_constrained=group_constrained,
            exclude_policy_constrained=exclude_policy_constrained,
        )
        response = await self._client._request(
            "POST",
            "/teams/search",
            json=payload.model_dump(exclude_none=True),
        )
        data = response.json()
        teams = data["teams"] if isinstance(data, dict) else data
        return [Team.model_validate(item) for item in teams]

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

    async def update(
        self,
        team_id: str,
        *,
        display_name: str,
        description: str,
        company_name: str,
        allowed_domains: str,
        invite_id: str,
        allow_open_invite: bool,
    ) -> Team:
        payload = TeamUpdateRequest(
            id=team_id,
            display_name=display_name,
            description=description,
            company_name=company_name,
            allowed_domains=allowed_domains,
            invite_id=invite_id,
            allow_open_invite=allow_open_invite,
        )
        return await self._client._request_model(
            "PUT",
            f"/teams/{team_id}",
            Team,
            json=payload.model_dump(),
        )

    async def patch(
        self,
        team_id: str,
        *,
        display_name: str | None = None,
        description: str | None = None,
        company_name: str | None = None,
        invite_id: str | None = None,
        allow_open_invite: bool | None = None,
    ) -> Team:
        payload = TeamPatchRequest(
            display_name=display_name,
            description=description,
            company_name=company_name,
            invite_id=invite_id,
            allow_open_invite=allow_open_invite,
        )
        return await self._client._request_model(
            "PUT",
            f"/teams/{team_id}/patch",
            Team,
            json=payload.model_dump(exclude_none=True),
        )

    async def delete(self, team_id: str, *, permanent: bool = False) -> StatusOK:
        return await self._client._request_model(
            "DELETE",
            f"/teams/{team_id}",
            StatusOK,
            params={"permanent": permanent},
        )

    async def restore(self, team_id: str) -> Team:
        return await self._client._request_model("POST", f"/teams/{team_id}/restore", Team)

    async def list_members(
        self,
        team_id: str,
        *,
        page: int = 0,
        per_page: int = 60,
        sort: str = "",
        exclude_deleted_users: bool = False,
    ) -> builtins.list[TeamMember]:
        response = await self._client._request(
            "GET",
            f"/teams/{team_id}/members",
            params={
                "page": page,
                "per_page": per_page,
                "sort": sort,
                "exclude_deleted_users": exclude_deleted_users,
            },
        )
        return [TeamMember.model_validate(item) for item in response.json()]

    async def add_member(self, team_id: str, user_id: str) -> TeamMember:
        payload = TeamMemberAddRequest(team_id=team_id, user_id=user_id)
        return await self._client._request_model(
            "POST",
            f"/teams/{team_id}/members",
            TeamMember,
            json=payload.model_dump(),
        )

    async def get_member(self, team_id: str, user_id: str) -> TeamMember:
        return await self._client._request_model(
            "GET",
            f"/teams/{team_id}/members/{user_id}",
            TeamMember,
        )

    async def remove_member(self, team_id: str, user_id: str) -> StatusOK:
        return await self._client._request_model(
            "DELETE",
            f"/teams/{team_id}/members/{user_id}",
            StatusOK,
        )

    async def update_member_roles(self, team_id: str, user_id: str, roles: str) -> StatusOK:
        payload = TeamMemberRolesRequest(roles=roles)
        return await self._client._request_model(
            "PUT",
            f"/teams/{team_id}/members/{user_id}/roles",
            StatusOK,
            json=payload.model_dump(),
        )

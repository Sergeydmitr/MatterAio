from __future__ import annotations

import builtins
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from ._pagination import validate_optional_page_args, validate_page_args
from ._paths import quote_path
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
        return await self._client._request_model("GET", f"/teams/{quote_path(team_id)}", Team)

    async def get_by_name(self, name: str) -> Team:
        return await self._client._request_model("GET", f"/teams/name/{quote_path(name)}", Team)

    async def list(
        self,
        *,
        page: int = 0,
        per_page: int = 60,
        exclude_policy_constrained: bool = False,
    ) -> builtins.list[Team]:
        validate_page_args(page, per_page)
        response = await self._client._request(
            "GET",
            "/teams",
            params={
                "page": page,
                "per_page": per_page,
                "exclude_policy_constrained": exclude_policy_constrained,
            },
        )
        return self._client._validate_model_list_data(
            response,
            Team,
            self._client._response_json(response),
        )

    async def iter_all(
        self,
        *,
        page: int = 0,
        per_page: int = 60,
        exclude_policy_constrained: bool = False,
    ) -> AsyncIterator[Team]:
        validate_page_args(page, per_page)
        current_page = page
        while True:
            teams = await self.list(
                page=current_page,
                per_page=per_page,
                exclude_policy_constrained=exclude_policy_constrained,
            )
            if not teams:
                break

            for team in teams:
                yield team

            if len(teams) < per_page:
                break
            current_page += 1

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
        validate_optional_page_args(page, per_page)
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
        data = self._client._response_json(response)
        teams = data.get("teams") if isinstance(data, dict) else data
        return self._client._validate_model_list_data(response, Team, teams)

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
            f"/teams/{quote_path(team_id)}",
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
            f"/teams/{quote_path(team_id)}/patch",
            Team,
            json=payload.model_dump(exclude_none=True),
        )

    async def delete(self, team_id: str, *, permanent: bool = False) -> StatusOK:
        return await self._client._request_model(
            "DELETE",
            f"/teams/{quote_path(team_id)}",
            StatusOK,
            params={"permanent": permanent},
        )

    async def restore(self, team_id: str) -> Team:
        return await self._client._request_model(
            "POST", f"/teams/{quote_path(team_id)}/restore", Team
        )

    async def list_members(
        self,
        team_id: str,
        *,
        page: int = 0,
        per_page: int = 60,
        sort: str = "",
        exclude_deleted_users: bool = False,
    ) -> builtins.list[TeamMember]:
        validate_page_args(page, per_page)
        response = await self._client._request(
            "GET",
            f"/teams/{quote_path(team_id)}/members",
            params={
                "page": page,
                "per_page": per_page,
                "sort": sort,
                "exclude_deleted_users": exclude_deleted_users,
            },
        )
        return self._client._validate_model_list_data(
            response,
            TeamMember,
            self._client._response_json(response),
        )

    async def iter_members(
        self,
        team_id: str,
        *,
        page: int = 0,
        per_page: int = 60,
        sort: str = "",
        exclude_deleted_users: bool = False,
    ) -> AsyncIterator[TeamMember]:
        validate_page_args(page, per_page)
        current_page = page
        while True:
            members = await self.list_members(
                team_id,
                page=current_page,
                per_page=per_page,
                sort=sort,
                exclude_deleted_users=exclude_deleted_users,
            )
            if not members:
                break

            for member in members:
                yield member

            if len(members) < per_page:
                break
            current_page += 1

    async def add_member(self, team_id: str, user_id: str) -> TeamMember:
        payload = TeamMemberAddRequest(team_id=team_id, user_id=user_id)
        return await self._client._request_model(
            "POST",
            f"/teams/{quote_path(team_id)}/members",
            TeamMember,
            json=payload.model_dump(),
        )

    async def get_member(self, team_id: str, user_id: str) -> TeamMember:
        return await self._client._request_model(
            "GET",
            f"/teams/{quote_path(team_id)}/members/{quote_path(user_id)}",
            TeamMember,
        )

    async def remove_member(self, team_id: str, user_id: str) -> StatusOK:
        return await self._client._request_model(
            "DELETE",
            f"/teams/{quote_path(team_id)}/members/{quote_path(user_id)}",
            StatusOK,
        )

    async def update_member_roles(self, team_id: str, user_id: str, roles: str) -> StatusOK:
        payload = TeamMemberRolesRequest(roles=roles)
        return await self._client._request_model(
            "PUT",
            f"/teams/{quote_path(team_id)}/members/{quote_path(user_id)}/roles",
            StatusOK,
            json=payload.model_dump(),
        )

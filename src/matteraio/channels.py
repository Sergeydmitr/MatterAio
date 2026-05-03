from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from .models import (
    Channel,
    ChannelCreateRequest,
    ChannelMember,
    ChannelMemberAddRequest,
    ChannelPatchRequest,
    ChannelSearchAllRequest,
    ChannelSearchRequest,
    ChannelStats,
    ChannelUnread,
    ChannelUpdateRequest,
    PostList,
    StatusOK,
)

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
    ) -> builtins.list[Channel]:
        response = await self._client._request(
            "GET",
            f"/teams/{team_id}/channels",
            params={"page": page, "per_page": per_page},
        )
        return [Channel.model_validate(item) for item in response.json()]

    async def update(
        self,
        channel_id: str,
        *,
        name: str,
        display_name: str,
        purpose: str,
        header: str,
    ) -> Channel:
        payload = ChannelUpdateRequest(
            id=channel_id,
            name=name,
            display_name=display_name,
            purpose=purpose,
            header=header,
        )
        return await self._client._request_model(
            "PUT",
            f"/channels/{channel_id}",
            Channel,
            json=payload.model_dump(),
        )

    async def patch(
        self,
        channel_id: str,
        *,
        name: str | None = None,
        display_name: str | None = None,
        purpose: str | None = None,
        header: str | None = None,
        group_constrained: bool | None = None,
        autotranslation: bool | None = None,
        managed_category_name: str | None = None,
    ) -> Channel:
        payload = ChannelPatchRequest(
            name=name,
            display_name=display_name,
            purpose=purpose,
            header=header,
            group_constrained=group_constrained,
            autotranslation=autotranslation,
            managed_category_name=managed_category_name,
        )
        return await self._client._request_model(
            "PUT",
            f"/channels/{channel_id}/patch",
            Channel,
            json=payload.model_dump(exclude_none=True),
        )

    async def delete(self, channel_id: str, *, permanent: bool = False) -> StatusOK:
        return await self._client._request_model(
            "DELETE",
            f"/channels/{channel_id}",
            StatusOK,
            params={"permanent": permanent},
        )

    async def restore(self, channel_id: str) -> Channel:
        return await self._client._request_model("POST", f"/channels/{channel_id}/restore", Channel)

    async def archive(self, channel_id: str, *, permanent: bool = False) -> StatusOK:
        return await self.delete(channel_id, permanent=permanent)

    async def unarchive(self, channel_id: str) -> Channel:
        return await self.restore(channel_id)

    async def join(
        self,
        channel_id: str,
        user_id: str,
        *,
        post_root_id: str | None = None,
    ) -> ChannelMember:
        return await self.add_member(channel_id, user_id, post_root_id=post_root_id)

    async def leave(self, channel_id: str, user_id: str) -> StatusOK:
        return await self.remove_member(channel_id, user_id)

    async def list_members(
        self,
        channel_id: str,
        *,
        page: int = 0,
        per_page: int = 60,
    ) -> builtins.list[ChannelMember]:
        response = await self._client._request(
            "GET",
            f"/channels/{channel_id}/members",
            params={"page": page, "per_page": per_page},
        )
        return [ChannelMember.model_validate(item) for item in response.json()]

    async def add_member(
        self,
        channel_id: str,
        user_id: str,
        *,
        post_root_id: str | None = None,
    ) -> ChannelMember:
        payload = ChannelMemberAddRequest(user_id=user_id, post_root_id=post_root_id)
        return await self._client._request_model(
            "POST",
            f"/channels/{channel_id}/members",
            ChannelMember,
            json=payload.model_dump(exclude_none=True),
        )

    async def remove_member(self, channel_id: str, user_id: str) -> StatusOK:
        return await self._client._request_model(
            "DELETE",
            f"/channels/{channel_id}/members/{user_id}",
            StatusOK,
        )

    async def create_direct(self, user_id: str, other_user_id: str) -> Channel:
        return await self._client._request_model(
            "POST",
            "/channels/direct",
            Channel,
            json=[user_id, other_user_id],
        )

    async def create_group(self, user_ids: builtins.list[str]) -> Channel:
        return await self._client._request_model(
            "POST",
            "/channels/group",
            Channel,
            json=user_ids,
        )

    async def search(self, team_id: str, term: str) -> builtins.list[Channel]:
        payload = ChannelSearchRequest(term=term)
        response = await self._client._request(
            "POST",
            f"/teams/{team_id}/channels/search",
            json=payload.model_dump(),
        )
        return [Channel.model_validate(item) for item in response.json()]

    async def search_all(
        self,
        term: str,
        *,
        system_console: bool = True,
        not_associated_to_group: str | None = None,
        exclude_default_channels: bool | None = None,
        team_ids: builtins.list[str] | None = None,
        group_constrained: bool | None = None,
        exclude_group_constrained: bool | None = None,
        public: bool | None = None,
        private: bool | None = None,
        deleted: bool | None = None,
        page: int | None = None,
        per_page: int | None = None,
        exclude_policy_constrained: bool | None = None,
        include_search_by_id: bool | None = None,
        exclude_remote: bool | None = None,
    ) -> builtins.list[Channel]:
        payload = ChannelSearchAllRequest(
            term=term,
            not_associated_to_group=not_associated_to_group,
            exclude_default_channels=exclude_default_channels,
            team_ids=team_ids,
            group_constrained=group_constrained,
            exclude_group_constrained=exclude_group_constrained,
            public=public,
            private=private,
            deleted=deleted,
            page=page,
            per_page=per_page,
            exclude_policy_constrained=exclude_policy_constrained,
            include_search_by_id=include_search_by_id,
            exclude_remote=exclude_remote,
        )
        response = await self._client._request(
            "POST",
            "/channels/search",
            params={"system_console": system_console},
            json=payload.model_dump(exclude_none=True),
        )
        data = response.json()
        channels = data["channels"] if isinstance(data, dict) else data
        return [Channel.model_validate(item) for item in channels]

    async def search_group(self, term: str) -> builtins.list[Channel]:
        payload = ChannelSearchRequest(term=term)
        response = await self._client._request(
            "POST",
            "/channels/group/search",
            json=payload.model_dump(),
        )
        return [Channel.model_validate(item) for item in response.json()]

    async def stats(self, channel_id: str) -> ChannelStats:
        return await self._client._request_model(
            "GET", f"/channels/{channel_id}/stats", ChannelStats
        )

    async def unread(self, user_id: str, channel_id: str) -> ChannelUnread:
        return await self._client._request_model(
            "GET",
            f"/users/{user_id}/channels/{channel_id}/unread",
            ChannelUnread,
        )

    async def pinned_posts(self, channel_id: str) -> PostList:
        return await self._client._request_model("GET", f"/channels/{channel_id}/pinned", PostList)

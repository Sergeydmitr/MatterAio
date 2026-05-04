from __future__ import annotations

import builtins
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from ._pagination import validate_optional_page_args, validate_page_args
from ._paths import quote_path
from .models import (
    FileInfo,
    Post,
    PostCreateRequest,
    PostList,
    PostPatchRequest,
    PostSearchRequest,
    PostSearchResponse,
    PostUpdateRequest,
    StatusOK,
)

if TYPE_CHECKING:
    from .client import MattermostClient


class PostsResource:
    def __init__(self, client: MattermostClient) -> None:
        self._client = client

    async def get(self, post_id: str, *, include_deleted: bool = False) -> Post:
        return await self._client._request_model(
            "GET",
            f"/posts/{quote_path(post_id)}",
            Post,
            params={"include_deleted": include_deleted},
        )

    async def create(
        self,
        *,
        channel_id: str,
        message: str,
        root_id: str | None = None,
        file_ids: list[str] | None = None,
    ) -> Post:
        payload = PostCreateRequest(
            channel_id=channel_id,
            message=message,
            root_id=root_id,
            file_ids=file_ids,
        )
        return await self._client._request_model(
            "POST",
            "/posts",
            Post,
            json=payload.model_dump(exclude_none=True),
        )

    async def update(
        self,
        post_id: str,
        *,
        message: str,
        is_pinned: bool | None = None,
        has_reactions: bool | None = None,
        props: dict[str, object] | None = None,
    ) -> Post:
        payload = PostUpdateRequest(
            id=post_id,
            message=message,
            is_pinned=is_pinned,
            has_reactions=has_reactions,
            props=props,
        )
        return await self._client._request_model(
            "PUT",
            f"/posts/{quote_path(post_id)}",
            Post,
            json=payload.model_dump(exclude_none=True),
        )

    async def patch(
        self,
        post_id: str,
        *,
        is_pinned: bool | None = None,
        message: str | None = None,
        file_ids: builtins.list[str] | None = None,
        has_reactions: bool | None = None,
        props: dict[str, object] | None = None,
    ) -> Post:
        payload = PostPatchRequest(
            is_pinned=is_pinned,
            message=message,
            file_ids=file_ids,
            has_reactions=has_reactions,
            props=props,
        )
        return await self._client._request_model(
            "PUT",
            f"/posts/{quote_path(post_id)}/patch",
            Post,
            json=payload.model_dump(exclude_none=True),
        )

    async def delete(self, post_id: str) -> StatusOK:
        return await self._client._request_model(
            "DELETE", f"/posts/{quote_path(post_id)}", StatusOK
        )

    async def thread(
        self,
        post_id: str,
        *,
        per_page: int | None = None,
        from_post: str | None = None,
        from_create_at: int | None = None,
        from_update_at: int | None = None,
        direction: str | None = None,
        skip_fetch_threads: bool | None = None,
        collapsed_threads: bool | None = None,
        collapsed_threads_extended: bool | None = None,
        updates_only: bool | None = None,
    ) -> PostList:
        validate_optional_page_args(None, per_page)
        params: dict[str, object] = {}
        if per_page is not None:
            params["perPage"] = per_page
        if from_post is not None:
            params["fromPost"] = from_post
        if from_create_at is not None:
            params["fromCreateAt"] = from_create_at
        if from_update_at is not None:
            params["fromUpdateAt"] = from_update_at
        if direction is not None:
            params["direction"] = direction
        if skip_fetch_threads is not None:
            params["skipFetchThreads"] = skip_fetch_threads
        if collapsed_threads is not None:
            params["collapsedThreads"] = collapsed_threads
        if collapsed_threads_extended is not None:
            params["collapsedThreadsExtended"] = collapsed_threads_extended
        if updates_only is not None:
            params["updatesOnly"] = updates_only

        return await self._client._request_model(
            "GET",
            f"/posts/{quote_path(post_id)}/thread",
            PostList,
            params=params,
        )

    async def list(
        self,
        channel_id: str,
        *,
        page: int | None = None,
        per_page: int | None = None,
        since: int | None = None,
        before: str | None = None,
        after: str | None = None,
        include_deleted: bool = False,
        type: str | None = None,
    ) -> PostList:
        if since is not None and (
            page is not None or per_page is not None or before is not None or after is not None
        ):
            raise ValueError("since cannot be used with page, per_page, before, or after")

        resolved_page = 0 if page is None else page
        resolved_per_page = 60 if per_page is None else per_page
        validate_page_args(resolved_page, resolved_per_page)

        params: dict[str, object] = {"include_deleted": include_deleted}
        if since is None:
            params["page"] = resolved_page
            params["per_page"] = resolved_per_page
        else:
            params["since"] = since
        if before is not None:
            params["before"] = before
        if after is not None:
            params["after"] = after
        if type is not None:
            params["type"] = type

        return await self._client._request_model(
            "GET",
            f"/channels/{quote_path(channel_id)}/posts",
            PostList,
            params=params,
        )

    async def iter_channel(
        self,
        channel_id: str,
        *,
        page: int = 0,
        per_page: int = 60,
        include_deleted: bool = False,
        type: str | None = None,
    ) -> AsyncIterator[Post]:
        validate_page_args(page, per_page)
        current_page = page
        while True:
            post_list = await self.list(
                channel_id,
                page=current_page,
                per_page=per_page,
                include_deleted=include_deleted,
                type=type,
            )
            if not post_list.order:
                break

            for post_id in post_list.order:
                post = post_list.posts.get(post_id)
                if post is not None:
                    yield post

            if len(post_list.order) < per_page:
                break
            current_page += 1

    async def search(
        self,
        team_id: str,
        terms: str,
        *,
        is_or_search: bool = False,
        time_zone_offset: int | None = None,
        include_deleted_channels: bool | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PostSearchResponse:
        validate_optional_page_args(page, per_page)
        payload = PostSearchRequest(
            terms=terms,
            is_or_search=is_or_search,
            time_zone_offset=time_zone_offset,
            include_deleted_channels=include_deleted_channels,
            page=page,
            per_page=per_page,
        )
        return await self._client._request_model(
            "POST",
            f"/teams/{quote_path(team_id)}/posts/search",
            PostSearchResponse,
            json=payload.model_dump(exclude_none=True),
        )

    async def pin(self, post_id: str) -> StatusOK:
        return await self._client._request_model(
            "POST", f"/posts/{quote_path(post_id)}/pin", StatusOK
        )

    async def unpin(self, post_id: str) -> StatusOK:
        return await self._client._request_model(
            "POST", f"/posts/{quote_path(post_id)}/unpin", StatusOK
        )

    async def get_by_ids(self, post_ids: builtins.list[str]) -> builtins.list[Post]:
        response = await self._client._request("POST", "/posts/ids", json=post_ids)
        return self._client._validate_model_list_data(
            response,
            Post,
            self._client._response_json(response),
        )

    async def files_info(
        self,
        post_id: str,
        *,
        include_deleted: bool = False,
    ) -> builtins.list[FileInfo]:
        response = await self._client._request(
            "GET",
            f"/posts/{quote_path(post_id)}/files/info",
            params={"include_deleted": include_deleted},
        )
        return self._client._validate_model_list_data(
            response,
            FileInfo,
            self._client._response_json(response),
        )

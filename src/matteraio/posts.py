from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Post, PostCreateRequest

if TYPE_CHECKING:
    from .client import MattermostClient


class PostsResource:
    def __init__(self, client: MattermostClient) -> None:
        self._client = client

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

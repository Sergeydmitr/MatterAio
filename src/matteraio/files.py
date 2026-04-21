from __future__ import annotations

from typing import TYPE_CHECKING

from .models import FileUploadResponse

if TYPE_CHECKING:
    from .client import MattermostClient


class FilesResource:
    def __init__(self, client: MattermostClient) -> None:
        self._client = client

    async def upload(
        self,
        *,
        channel_id: str,
        filename: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        client_id: str | None = None,
    ) -> FileUploadResponse:
        data = {"channel_id": channel_id}
        if client_id is not None:
            data["client_ids"] = client_id
        return await self._client._request_model(
            "POST",
            "/files",
            FileUploadResponse,
            data=data,
            files={"files": (filename, content, content_type)},
        )

from __future__ import annotations

from .models import FileUploadResponse


class FilesResource:
    def __init__(self, client: object) -> None:
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

        files = {
            "files": (filename, content, content_type),
        }
        return await self._client._request_model(
            "POST",
            "/files",
            FileUploadResponse,
            data=data,
            files=files,
        )

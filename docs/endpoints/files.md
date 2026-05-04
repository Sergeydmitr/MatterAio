# Files

[Endpoint reference](../endpoints.md)

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.files.info(file_id)` | `GET /files/{file_id}/info` | Get stored file metadata. |
| `client.files.download(file_id)` | `GET /files/{file_id}` | Download file content as bytes. |
| `client.files.upload(...)` | `POST /files` | Upload a file with multipart form data. Pass returned file IDs to `client.posts.create(...)`. |

## Returned Data

`info(file_id)` returns `FileInfo`; `upload(...)` returns `FileUploadResponse`.

| Field | Type | Description |
| --- | --- | --- |
| `id` | `str` | Mattermost file ID. |
| `user_id` | `str or None` | Uploading user ID. |
| `channel_id` | `str or None` | Channel ID associated with the file. |
| `post_id` | `str or None` | Post ID once attached to a post. |
| `name` | `str` | Original filename. |
| `extension` | `str or None` | File extension. |
| `size` | `int or None` | Size in bytes. |
| `mime_type` | `str or None` | MIME type. |
| `width` | `int or None` | Image width when applicable. |
| `height` | `int or None` | Image height when applicable. |
| `has_preview_image` | `bool or None` | Whether Mattermost generated a preview image. |

`FileUploadResponse` contains:

| Field | Type | Description |
| --- | --- | --- |
| `file_infos` | `list[FileInfo]` | Metadata for uploaded files. |
| `client_ids` | `list[str]` | Client IDs returned by Mattermost. |

`download(file_id)` returns raw `bytes`.

## Examples

```python
from matteraio import MattermostClient


async def main() -> None:
    async with MattermostClient(
        base_url="https://mattermost.example.com",
        token="YOUR_BOT_TOKEN",
    ) as client:
        channel = await client.channels.get("channel-id")

        upload = await client.files.upload(
            channel_id=channel.id,
            filename="deploy-log.txt",
            content=b"deploy completed\n",
            content_type="text/plain",
        )
        file_id = upload.file_infos[0].id

        await client.posts.create(
            channel_id=channel.id,
            message="Deploy log attached.",
            file_ids=[file_id],
        )

        info = await client.files.info(file_id)
        content = await client.files.download(file_id)

        print(info.name, len(content))
```

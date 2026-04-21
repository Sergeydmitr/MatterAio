# MatterAio

Async Python client for the Mattermost REST API.

The library is intentionally small and explicit:

- async-only
- thin wrapper over Mattermost API v4
- no convenience methods that combine multiple API calls

## Installation

With `uv`:

```bash
uv sync
```

From another project:

```bash
uv add /path/to/MatterAio
```

With `pip`:

```bash
pip install -e .
```

## Quick Start

```python
import asyncio

from matteraio import MattermostClient


async def main() -> None:
    async with MattermostClient(
            base_url="https://mattermost.example.com",
            token="YOUR_BOT_TOKEN",
    ) as client:
        me = await client.users.me()
        print(me.username)

        channel = await client.channels.get_by_name("team-id", "town-square")

        post = await client.posts.create(
            channel_id=channel.id,
            message="Hello from matteraio",
        )
        print(post.id)


asyncio.run(main())
```

## Design

- `MattermostClient` owns one shared `httpx.AsyncClient`
- resources are exposed as `client.users`, `client.channels`, `client.posts`, `client.files`
- methods stay close to underlying Mattermost endpoints
- multi-step workflows are explicit at call site

## Public API

### `MattermostClient`

Create a client with:

```python
MattermostClient(
    base_url: str,
token: str,
*,
timeout: float = 10.0,
connect_timeout: float = 5.0,
max_connections: int = 20,
max_keepalive_connections: int = 10,
transport: httpx.AsyncBaseTransport | None = None,
)
```

Notes:

- `base_url` may be either the server root, like `https://mm.example.com`, or a full API base ending in `/api/v4`
- authentication uses `Authorization: Bearer <token>`
- the client is intended to be used as an async context manager

Lifecycle methods:

- `async with MattermostClient(...) as client`
- `await client.aclose()`

### `client.users`

#### `await client.users.me() -> User`

Get the current authenticated user.

Example:

```python
me = await client.users.me()
print(me.id, me.username, me.email)
```

### `client.channels`

#### `await client.channels.get(channel_id: str) -> Channel`

Get a channel by ID.

#### `await client.channels.get_by_name(team_id: str, channel_name: str) -> Channel`

Get a channel by channel name inside a team.

#### `await client.channels.list(team_id: str, *, page: int = 0, per_page: int = 60) -> list[Channel]`

List channels for a team.

Example:

```python
channel = await client.channels.get("channel-id")
channel = await client.channels.get_by_name("team-id", "engineering")
channels = await client.channels.list("team-id", page=0, per_page=50)
```

### `client.posts`

####
`await client.posts.create(*, channel_id: str, message: str, root_id: str | None = None, file_ids: list[str] | None = None) -> Post`

Create a post in a channel.

Use `root_id` for thread replies and `file_ids` for already uploaded files.

Examples:

```python
post = await client.posts.create(
    channel_id="channel-id",
    message="plain message",
)

reply = await client.posts.create(
    channel_id="channel-id",
    message="thread reply",
    root_id="parent-post-id",
)
```

### `client.files`

####
`await client.files.upload(*, channel_id: str, filename: str, content: bytes, content_type: str = "application/octet-stream", client_id: str | None = None) -> FileUploadResponse`

Upload a file with multipart form data.

The returned `FileUploadResponse.file_infos` contains the uploaded file metadata. Pass the resulting file IDs into
`client.posts.create(..., file_ids=[...])`.

Example:

```python
upload = await client.files.upload(
    channel_id="channel-id",
    filename="note.txt",
    content=b"hello",
    content_type="text/plain",
)

post = await client.posts.create(
    channel_id="channel-id",
    message="file attached",
    file_ids=[file_info.id for file_info in upload.file_infos],
)
```

This explicit two-step flow is intentional. The library does not provide convenience methods that hide upload and post
creation inside one call.

## Models

Current typed response/request models include:

- `User`
- `Channel`
- `Post`
- `PostCreateRequest`
- `FileInfo`
- `FileUploadResponse`

Pydantic models ignore unknown Mattermost fields, so the client can parse larger server responses without requiring
every field to be modeled.

## Errors

The client raises these exceptions:

- `MattermostError` — base exception for library errors
- `TransportError` — network/transport failure before a valid API response
- `ApiError` — non-2xx Mattermost API response
- `AuthError` — authentication or authorization failure (`401`/`403`)
- `RateLimitError` — rate limiting (`429`)

`ApiError` includes:

- `message`
- `status_code`
- `error_id`
- `request_id`
- `detailed_error`
- `retry_after`

Example:

```python
from matteraio import AuthError, TransportError

try:
    await client.users.me()
except AuthError as exc:
    print(exc.status_code, exc.request_id)
except TransportError:
    print("Mattermost is unreachable")
```

## Current Scope

Implemented resources:

- users: `me`
- channels: `get`, `get_by_name`, `list`
- posts: `create`
- files: `upload`

Not implemented yet:

- broader channel, team, user, and post APIs
- websocket support
- higher-level workflow helpers

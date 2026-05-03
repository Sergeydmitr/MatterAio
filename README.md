# MatterAio

Async Python client for the Mattermost REST API and WebSocket events.

The library is intentionally small and explicit:
- async-only
- thin wrapper over Mattermost API v4
- no convenience methods that combine multiple API calls

## Installation

With `uv`:

```bash
uv sync
```

For development:

```bash
uv sync --all-groups
uv run ruff format .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

## Integration Tests

The repository includes an opt-in live integration setup against a local Mattermost preview server.

Start the local server:

```bash
docker compose -f docker-compose.integration.yml up -d
```

Run the live tests:

```bash
MATTERAIO_RUN_INTEGRATION=1 uv run pytest tests/integration -m integration
```

Override the default base URL if needed:

```bash
MATTERAIO_BASE_URL=http://127.0.0.1:8065 MATTERAIO_RUN_INTEGRATION=1 uv run pytest tests/integration -m integration
```

Stop the local server when you are done:

```bash
docker compose -f docker-compose.integration.yml down -v
```

Notes:
- the live suite is skipped by default during `uv run pytest`
- the integration fixtures bootstrap their own user, team, and channel with raw REST calls so setup stays independent from the client under test
- `docker-compose.integration.yml` uses the official `mattermost/mattermost-preview` image for local testing only

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

Minimal WebSocket usage:

```python
import asyncio

from matteraio import MattermostWebSocketClient


async def main() -> None:
    client = MattermostWebSocketClient(
        base_url="https://mattermost.example.com",
        token="YOUR_BOT_TOKEN",
    )

    await client.connect()
    await client.authenticate()

    try:
        while True:
            event = await client.receive_event()
            print(type(event).__name__, getattr(event, "event", None))
    finally:
        await client.aclose()


asyncio.run(main())
```

## Design

- `MattermostClient` owns one shared `httpx.AsyncClient`
- `MattermostWebSocketClient` manages one explicit WebSocket connection
- resources are exposed as `client.teams`, `client.users`, `client.channels`, `client.posts`, `client.files`
- methods stay close to underlying Mattermost endpoints
- multi-step workflows are explicit at call site

## Public API

### `MattermostClient`

Create a client with:

```python
MattermostClient(
    base_url: str,
    token: str = "",
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
- authentication uses `Authorization: Bearer <token>` when `token` is provided
- `client.users.login(...)` can be used to obtain and store a session token after construction
- the client is intended to be used as an async context manager

Lifecycle methods:
- `async with MattermostClient(...) as client`
- `await client.aclose()`

### `MattermostWebSocketClient`

Create a WebSocket client with:

```python
MattermostWebSocketClient(
    base_url: str,
    token: str,
    *,
    open_timeout: float = 10.0,
    ping_interval: float | None = 20.0,
    ping_timeout: float | None = 20.0,
    close_timeout: float = 10.0,
    max_size: int | None = 1_048_576,
    reconnect_initial_delay: float = 1.0,
    reconnect_max_delay: float = 16.0,
    reconnect_max_attempts: int | None = None,
    additional_headers: dict[str, str] | None = None,
)
```

Notes:
- the WebSocket URL is derived from `base_url` as `/api/v4/websocket`
- authentication is explicit and happens after `connect()`
- reconnect is explicit via `reconnect()`
- keepalive uses the underlying library ping configuration plus an explicit `ping()` method

Lifecycle methods:
- `async with MattermostWebSocketClient(...) as client`
- `await client.connect()`
- `await client.reconnect()`
- `await client.aclose()`

Core methods:
- `await client.authenticate() -> int`
- `await client.send_command(action, data=None) -> int`
- `await client.ping(data=None) -> float`
- `await client.receive_json(timeout=None) -> dict[str, Any]`
- `await client.receive_message(timeout=None) -> WebSocketMessage`
- `await client.receive_event(timeout=None) -> TypedWebSocketEvent | WebSocketMessage`

Typed event parsing:
- `receive_message()` always returns the generic `WebSocketMessage`
- `receive_event()` returns typed models for supported events and falls back to `WebSocketMessage` for unknown events

### `client.users`

#### `await client.users.login(*, login_id: str, password: str, token: str | None = None) -> LoginResponse`

Log in with email, username, or LDAP ID. The returned `LoginResponse.token` is also stored on the client, so later REST
calls use the session token automatically.

#### `await client.users.me() -> User`

Get the current authenticated user.

#### `await client.users.get(user_id: str) -> User`

Get a user by ID. Mattermost also accepts `"me"` for the current user.

#### `await client.users.get_by_username(username: str) -> User`

Get a user by username.

#### `await client.users.get_by_email(email: str) -> User`

Get a user by email address.

#### `await client.users.search(term: str, *, team_id: str | None = None, not_in_team_id: str | None = None, in_channel_id: str | None = None, not_in_channel_id: str | None = None, in_group_id: str | None = None, group_constrained: bool | None = None, allow_inactive: bool | None = None, without_team: bool | None = None, limit: int | None = None) -> list[User]`

Search users by username, full name, nickname, or email, optionally scoped to a team, channel, or group.

Example:

```python
login = await client.users.login(login_id="bot@example.com", password="secret")
me = await client.users.me()
users = await client.users.search("ali", team_id="team-id", limit=10)
print(me.id, me.username, me.email)
```

### `client.teams`

#### `await client.teams.get(team_id: str) -> Team`

Get a team by ID.

#### `await client.teams.get_by_name(name: str) -> Team`

Get a team by URL-safe team name.

#### `await client.teams.create(*, name: str, display_name: str, type: str = "O") -> Team`

Create a team. Use `type="O"` for open teams and `type="I"` for invite-only teams.

#### `await client.teams.list(*, page: int = 0, per_page: int = 60, exclude_policy_constrained: bool = False) -> list[Team]`

List teams visible to the current user.

#### `await client.teams.search(term: str, *, page: int | None = None, per_page: int | None = None, allow_open_invite: bool | None = None, group_constrained: bool | None = None, exclude_policy_constrained: bool | None = None) -> list[Team]`

Search teams by name or display name.

#### `await client.teams.update(team_id: str, *, display_name: str, description: str, company_name: str, allowed_domains: str, invite_id: str, allow_open_invite: bool) -> Team`

Update the full editable team profile.

#### `await client.teams.patch(team_id: str, *, display_name: str | None = None, description: str | None = None, company_name: str | None = None, invite_id: str | None = None, allow_open_invite: bool | None = None) -> Team`

Patch only the provided editable team fields.

#### `await client.teams.delete(team_id: str, *, permanent: bool = False) -> StatusOK`

Soft-delete a team by default. Use `permanent=True` only when the server is configured for permanent team deletion.

#### `await client.teams.restore(team_id: str) -> Team`

Restore a previously soft-deleted team.

#### `await client.teams.list_members(team_id: str, *, page: int = 0, per_page: int = 60, sort: str = "", exclude_deleted_users: bool = False) -> list[TeamMember]`

List team members. Use `sort="Username"` to sort by username.

#### `await client.teams.add_member(team_id: str, user_id: str) -> TeamMember`

Add a user to a team.

#### `await client.teams.get_member(team_id: str, user_id: str) -> TeamMember`

Get a team member. Current team roles are available as `member.roles`.

#### `await client.teams.remove_member(team_id: str, user_id: str) -> StatusOK`

Remove a user from a team.

#### `await client.teams.update_member_roles(team_id: str, user_id: str, roles: str) -> StatusOK`

Overwrite team roles with a space-delimited value such as `"team_user team_admin"`.

Example:

```python
team = await client.teams.get_by_name("engineering")
team = await client.teams.create(name="ops", display_name="Operations")
teams = await client.teams.search("ops", page=0, per_page=10)
member = await client.teams.get_member(team.id, "user-id")
await client.teams.update_member_roles(team.id, "user-id", "team_user team_admin")
```

### `client.channels`

#### `await client.channels.get(channel_id: str) -> Channel`

Get a channel by ID.

#### `await client.channels.get_by_name(team_id: str, channel_name: str) -> Channel`

Get a channel by channel name inside a team.

#### `await client.channels.create(*, team_id: str, name: str, display_name: str, type: str = "O", purpose: str | None = None, header: str | None = None) -> Channel`

Create a channel. Use `type="O"` for public channels and `type="P"` for private channels.

#### `await client.channels.list(team_id: str, *, page: int = 0, per_page: int = 60) -> list[Channel]`

List channels for a team.

Example:

```python
channel = await client.channels.get("channel-id")
channel = await client.channels.get_by_name("team-id", "engineering")
channel = await client.channels.create(
    team_id="team-id",
    name="incidents",
    display_name="Incidents",
)
channels = await client.channels.list("team-id", page=0, per_page=50)
```

### `client.posts`

#### `await client.posts.get(post_id: str, *, include_deleted: bool = False) -> Post`

Get a post by ID.

#### `await client.posts.create(*, channel_id: str, message: str, root_id: str | None = None, file_ids: list[str] | None = None) -> Post`

Create a post in a channel.

Use `root_id` for thread replies and `file_ids` for already uploaded files.

Examples:

```python
post = await client.posts.create(
    channel_id="channel-id",
    message="plain message",
)
same_post = await client.posts.get(post.id)

reply = await client.posts.create(
    channel_id="channel-id",
    message="thread reply",
    root_id="parent-post-id",
)
```

### `client.files`

#### `await client.files.info(file_id: str) -> FileInfo`

Get stored file metadata.

#### `await client.files.download(file_id: str) -> bytes`

Download file content as bytes.

#### `await client.files.upload(*, channel_id: str, filename: str, content: bytes, content_type: str = "application/octet-stream", client_id: str | None = None) -> FileUploadResponse`

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
file_info = await client.files.info(upload.file_infos[0].id)
content = await client.files.download(file_info.id)

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
- `UserLoginRequest`
- `LoginResponse`
- `UserSearchRequest`
- `Team`
- `TeamCreateRequest`
- `TeamSearchRequest`
- `TeamUpdateRequest`
- `TeamPatchRequest`
- `TeamMember`
- `TeamMemberAddRequest`
- `TeamMemberRolesRequest`
- `StatusOK`
- `Channel`
- `ChannelCreateRequest`
- `Post`
- `PostCreateRequest`
- `FileInfo`
- `FileUploadResponse`
- `WebSocketBroadcast`
- `WebSocketCommand`
- `WebSocketMessage`
- `HelloEvent`
- `PostedEvent`
- `StatusChangeEvent`
- `TypedWebSocketEvent`

Pydantic models ignore unknown Mattermost fields, so the client can parse larger server responses without requiring
every field to be modeled.

## Errors

The client raises these exceptions:

- `MattermostError` — base exception for library errors
- `TransportError` — network/transport failure before a valid API response
- `ApiError` — non-2xx Mattermost API response
- `AuthError` — authentication or authorization failure (`401`/`403`)
- `RateLimitError` — rate limiting (`429`)
- `WebSocketError` — base exception for WebSocket-specific failures
- `WebSocketConnectionError` — connection open/send/receive failure
- `WebSocketDisconnectedError` — the server closed the connection; includes `close_code` and `close_reason`
- `WebSocketNotConnectedError` — command or receive attempted before `connect()`
- `WebSocketProtocolError` — invalid or unexpected WebSocket payload
- `WebSocketTimeoutError` — recv timeout expired while waiting for a message

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

- users: `login`, `me`, `get`, `get_by_username`, `get_by_email`, `search`
- teams: `get`, `get_by_name`, `create`, `list`, `search`, `update`, `patch`, `delete`, `restore`,
  `list_members`, `add_member`, `get_member`, `remove_member`, `update_member_roles`
- channels: `get`, `get_by_name`, `create`, `list`
- posts: `get`, `create`
- files: `info`, `download`, `upload`
- websocket: `connect`, `reconnect`, `authenticate`, `send_command`, `ping`, `receive_json`, `receive_message`
- typed websocket events: `hello`, `posted`, `status_change`
- integration coverage: opt-in live REST and WebSocket tests against a local Mattermost instance

Not implemented yet:

- broader channel, team, user, post, and file APIs
- richer event typing for important Mattermost events
- higher-level workflow helpers

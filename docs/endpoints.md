# Endpoint Reference

MatterAio exposes one async resource object per Mattermost API area. Methods stay close to
Mattermost API v4 paths and return typed Pydantic models.

REST documentation is split by Mattermost API area, with one file per resource.
Returned structures are Pydantic models. Mattermost response fields that are not listed in
these models are ignored by MatterAio.

## Client Lifecycle

| SDK method | Description |
| --- | --- |
| `async with MattermostClient(...) as client` | Open and close the shared HTTP client. |
| `await client.init_session()` | Fetch `/users/me` once and cache the authenticated bot session. |
| `client.require_session()` | Return the cached bot session or raise `MattermostError`. |
| `await client.aclose()` | Close the underlying HTTP client. |

`base_url` may be a server root such as `https://mm.example.com` or a full API base ending in
`/api/v4`. Authentication uses `Authorization: Bearer <token>` when a token is provided.

## REST Resources

| Area | Description |
| --- | --- |
| [Users and Auth](endpoints/users.md) | Login, current user, user lookup, and user search methods. |
| [Teams](endpoints/teams.md) | Team lookup, creation, updates, deletion, restore, and membership methods. |
| [Channels](endpoints/channels.md) | Channel lookup, creation, updates, archive/restore, membership, direct/group channels, search, stats, unread, and pinned posts. |
| [Posts](endpoints/posts.md) | Post lookup, creation, update, deletion, threads, channel history, search, pinning, batch lookup, and attached file metadata. |
| [Reactions](endpoints/reactions.md) | Add, remove, and list post reactions. |
| [Files](endpoints/files.md) | File metadata, download, and upload methods. |

## WebSocket

- [WebSocket client and event handlers](endpoints/websocket.md)

## Errors

REST methods raise `TransportError` for network failures and `ApiError` for non-2xx responses.
`AuthError` covers `401` and `403`; `RateLimitError` covers `429`. WebSocket methods raise
`WebSocketError` subclasses for connection, protocol, timeout, and closed-connection failures.

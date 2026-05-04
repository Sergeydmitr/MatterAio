# Endpoint Reference

MatterAio exposes one async resource object per Mattermost API area. Methods stay close to
Mattermost API v4 paths and return typed Pydantic models.

## Client Lifecycle

| SDK method | Description |
| --- | --- |
| `async with MattermostClient(...) as client` | Open and close the shared HTTP client. |
| `await client.init_session()` | Fetch `/users/me` once and cache the authenticated bot session. |
| `client.require_session()` | Return the cached bot session or raise `MattermostError`. |
| `await client.aclose()` | Close the underlying HTTP client. |

`base_url` may be a server root such as `https://mm.example.com` or a full API base ending in
`/api/v4`. Authentication uses `Authorization: Bearer <token>` when a token is provided.

## Users and Auth

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.users.login(...)` | `POST /users/login` | Log in with email, username, or LDAP ID. Stores the returned session token when the client was created without a token. |
| `client.users.me()` | `GET /users/me` | Get the authenticated user. |
| `client.users.get(user_id)` | `GET /users/{user_id}` | Get a user by ID. Mattermost also accepts `me`. |
| `client.users.get_by_username(username)` | `GET /users/username/{username}` | Get a user by username. |
| `client.users.get_by_email(email)` | `GET /users/email/{email}` | Get a user by email address. |
| `client.users.search(term, ...)` | `POST /users/search` | Search users by name, username, nickname, or email with optional team/channel filters. |

## Teams

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.teams.get(team_id)` | `GET /teams/{team_id}` | Get a team by ID. |
| `client.teams.get_by_name(name)` | `GET /teams/name/{name}` | Get a team by URL-safe name. |
| `client.teams.list(...)` | `GET /teams` | List teams visible to the current user. |
| `client.teams.search(term, ...)` | `POST /teams/search` | Search teams by name or display name. |
| `client.teams.create(...)` | `POST /teams` | Create a team. Use `type="O"` for open teams and `type="I"` for invite-only teams. |
| `client.teams.update(team_id, ...)` | `PUT /teams/{team_id}` | Replace the editable team profile. |
| `client.teams.patch(team_id, ...)` | `PUT /teams/{team_id}/patch` | Patch provided team fields. |
| `client.teams.delete(team_id, permanent=False)` | `DELETE /teams/{team_id}` | Soft-delete a team by default. |
| `client.teams.restore(team_id)` | `POST /teams/{team_id}/restore` | Restore a soft-deleted team. |
| `client.teams.list_members(team_id, ...)` | `GET /teams/{team_id}/members` | List team members. |
| `client.teams.add_member(team_id, user_id)` | `POST /teams/{team_id}/members` | Add a user to a team. |
| `client.teams.get_member(team_id, user_id)` | `GET /teams/{team_id}/members/{user_id}` | Get a team member and their roles. |
| `client.teams.remove_member(team_id, user_id)` | `DELETE /teams/{team_id}/members/{user_id}` | Remove a user from a team. |
| `client.teams.update_member_roles(team_id, user_id, roles)` | `PUT /teams/{team_id}/members/{user_id}/roles` | Overwrite team roles, for example `team_user team_admin`. |

## Channels

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.channels.get(channel_id)` | `GET /channels/{channel_id}` | Get a channel by ID. |
| `client.channels.get_by_name(team_id, channel_name)` | `GET /teams/{team_id}/channels/name/{channel_name}` | Get a channel by name inside a team. |
| `client.channels.create(...)` | `POST /channels` | Create a public or private channel. |
| `client.channels.list(team_id, ...)` | `GET /teams/{team_id}/channels` | List channels for a team. |
| `client.channels.update(channel_id, ...)` | `PUT /channels/{channel_id}` | Replace the editable channel profile. |
| `client.channels.patch(channel_id, ...)` | `PUT /channels/{channel_id}/patch` | Patch provided channel fields. |
| `client.channels.delete(channel_id, permanent=False)` | `DELETE /channels/{channel_id}` | Archive a channel by default. |
| `client.channels.restore(channel_id)` | `POST /channels/{channel_id}/restore` | Restore an archived channel. |
| `client.channels.archive(channel_id, ...)` | `DELETE /channels/{channel_id}` | Alias for `delete(...)`. |
| `client.channels.unarchive(channel_id)` | `POST /channels/{channel_id}/restore` | Alias for `restore(...)`. |
| `client.channels.list_members(channel_id, ...)` | `GET /channels/{channel_id}/members` | List channel members. |
| `client.channels.add_member(channel_id, user_id, ...)` | `POST /channels/{channel_id}/members` | Add a user to a channel. |
| `client.channels.remove_member(channel_id, user_id)` | `DELETE /channels/{channel_id}/members/{user_id}` | Remove a user from a channel. |
| `client.channels.join(channel_id, user_id, ...)` | `POST /channels/{channel_id}/members` | Alias for `add_member(...)`. |
| `client.channels.leave(channel_id, user_id)` | `DELETE /channels/{channel_id}/members/{user_id}` | Alias for `remove_member(...)`. |
| `client.channels.create_direct(user_id, other_user_id)` | `POST /channels/direct` | Create or get a direct message channel. |
| `client.channels.create_group(user_ids)` | `POST /channels/group` | Create or get a group message channel for 3 to 8 users. |
| `client.channels.search(team_id, term)` | `POST /teams/{team_id}/channels/search` | Search public channels inside a team. |
| `client.channels.search_all(term, ...)` | `POST /channels/search` | Search open and private channels across teams. |
| `client.channels.search_group(term)` | `POST /channels/group/search` | Search group message channels by member username. |
| `client.channels.stats(channel_id)` | `GET /channels/{channel_id}/stats` | Get channel statistics. |
| `client.channels.unread(user_id, channel_id)` | `GET /users/{user_id}/channels/{channel_id}/unread` | Get unread message and mention counts. |
| `client.channels.pinned_posts(channel_id)` | `GET /channels/{channel_id}/pinned` | Get pinned posts for a channel. |

## Posts

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.posts.get(post_id, ...)` | `GET /posts/{post_id}` | Get a post by ID. |
| `client.posts.create(...)` | `POST /posts` | Create a post in a channel. Use `root_id` for thread replies and `file_ids` for uploaded files. |
| `client.posts.update(post_id, ...)` | `PUT /posts/{post_id}` | Replace the editable post body. |
| `client.posts.patch(post_id, ...)` | `PUT /posts/{post_id}/patch` | Patch provided post fields. |
| `client.posts.delete(post_id)` | `DELETE /posts/{post_id}` | Soft-delete a post. |
| `client.posts.thread(post_id, ...)` | `GET /posts/{post_id}/thread` | Get a post thread. |
| `client.posts.list(channel_id, ...)` | `GET /channels/{channel_id}/posts` | Get channel post history. |
| `client.posts.search(team_id, terms, ...)` | `POST /teams/{team_id}/posts/search` | Search team posts using Mattermost search syntax. |
| `client.posts.pin(post_id)` | `POST /posts/{post_id}/pin` | Pin a post to its channel. |
| `client.posts.unpin(post_id)` | `POST /posts/{post_id}/unpin` | Unpin a post from its channel. |
| `client.posts.get_by_ids(post_ids)` | `POST /posts/ids` | Fetch posts by a batch of post IDs. |
| `client.posts.files_info(post_id, ...)` | `GET /posts/{post_id}/files/info` | Get file metadata attached to a post. |

## Reactions

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.reactions.add(...)` | `POST /reactions` | Add a reaction to a post. |
| `client.reactions.remove(user_id, post_id, emoji_name)` | `DELETE /users/{user_id}/posts/{post_id}/reactions/{emoji_name}` | Remove one user's reaction. |
| `client.reactions.list(post_id)` | `GET /posts/{post_id}/reactions` | List reactions for a post. |

## Files

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.files.info(file_id)` | `GET /files/{file_id}/info` | Get stored file metadata. |
| `client.files.download(file_id)` | `GET /files/{file_id}` | Download file content as bytes. |
| `client.files.upload(...)` | `POST /files` | Upload a file with multipart form data. Pass returned file IDs to `client.posts.create(...)`. |

## WebSocket

`MattermostWebSocketClient` connects to `/api/v4/websocket`.

| SDK method | Description |
| --- | --- |
| `async with MattermostWebSocketClient(...) as client` | Open and close one WebSocket connection. |
| `client.is_connected` | Return whether the connection is currently open. |
| `client.close_code` / `client.close_reason` | Inspect the latest close details. |
| `await client.connect()` | Open the connection. |
| `await client.reconnect()` | Reopen with backoff and re-authenticate if needed. |
| `await client.aclose()` | Close the connection. |
| `await client.authenticate()` | Send the Mattermost authentication challenge. |
| `await client.send_command(action, data=None)` | Send a raw WebSocket command and return its sequence number. |
| `await client.ping(data=None)` | Send a ping and return the pong latency. |
| `await client.receive_json(timeout=None)` | Receive a decoded JSON object. |
| `await client.receive_message(timeout=None)` | Receive a generic `WebSocketMessage`. |
| `await client.receive_event(timeout=None)` | Receive a typed event when supported, otherwise a generic message. |

Typed events currently include `hello`, `posted`, and `status_change`.

## Errors

REST methods raise `TransportError` for network failures and `ApiError` for non-2xx responses.
`AuthError` covers `401` and `403`; `RateLimitError` covers `429`. WebSocket methods raise
`WebSocketError` subclasses for connection, protocol, timeout, and closed-connection failures.

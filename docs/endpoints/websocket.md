# WebSocket

[Endpoint reference](../endpoints.md)

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

## Returned Data

`receive_json(...)` returns the decoded Mattermost payload as `dict[str, object]`.
`receive_message(...)` returns `WebSocketMessage`.

| Field | Type | Description |
| --- | --- | --- |
| `event` | `str or None` | Event name for server events. |
| `data` | `dict[str, object]` | Raw event or reply payload. |
| `broadcast` | `WebSocketBroadcast or None` | Broadcast routing metadata when present. |
| `seq` | `int or None` | Sequence number from Mattermost. |
| `status` | `str or None` | Reply status for command responses. |
| `seq_reply` | `int or None` | Sequence number of the command being answered. |

`receive_event(...)` returns a typed event for supported event names, otherwise the generic
`WebSocketMessage`.

| Event class | `event` | Data fields |
| --- | --- | --- |
| `HelloEvent` | `hello` | `connection_id`, `server_version` |
| `PostedEvent` | `posted` | `post`, `mentions`, `channel_display_name`, `channel_name`, `channel_type`, `sender_name`, `set_online`, `team_id` |
| `StatusChangeEvent` | `status_change` | `status`, `user_id` |

`send_command(...)`, `authenticate(...)`, and `ping(...)` return plain values: command sequence
numbers as `int`, and ping latency as `float`.

## Examples

```python
from matteraio import MattermostWebSocketClient, PostedEvent


async def main() -> None:
    async with MattermostWebSocketClient(
        base_url="https://mattermost.example.com",
        token="YOUR_BOT_TOKEN",
    ) as websocket:
        await websocket.authenticate()
        await websocket.send_command("user_typing", {"channel_id": "channel-id"})

        event = await websocket.receive_event(timeout=30)
        if isinstance(event, PostedEvent):
            print(event.data.post.id, event.data.post.message)
```

## Event Handlers

`MattermostEventRouter` and `MattermostEventDispatcher` provide decorator-based event
handling for incoming WebSocket events.

```python
from matteraio import MattermostEventDispatcher, MattermostEventRouter, PostedEvent

posts = MattermostEventRouter(name="posts")


@posts.on(PostedEvent)
async def on_typed_post(event: PostedEvent) -> None:
    print(event.data.post.id)


@posts.event("posted")
async def on_named_post(event: PostedEvent) -> None:
    print(event.data.post.message)


dispatcher = MattermostEventDispatcher()
dispatcher.include_router(posts)
```

| SDK method | Description |
| --- | --- |
| `router.on(selector, *filters)` | Register an async handler by event class, event name, or `None` for all messages. |
| `router.event(selector, *filters)` | Alias for `router.on(...)`. |
| `router.register(callback, selector=..., filters=...)` | Register a handler without decorator syntax. |
| `router.include_router(router)` | Attach a child router. |
| `router.dispatch(event)` | Dispatch one already-received event and return the number of handlers called. |
| `dispatcher.feed_event(event)` | Alias-style entry point for dispatching one event. |
| `dispatcher.dispatch_next(client, timeout=None)` | Read one event from `MattermostWebSocketClient` and dispatch it. |
| `dispatcher.start(client, authenticate=True, timeout=None)` | Connect if needed, optionally authenticate, then dispatch events until cancelled or disconnected. |

# MatterAio

Async Python client for the Mattermost REST API and WebSocket events.

MatterAio is intentionally small and explicit:

- async-only
- thin wrapper over Mattermost API v4
- no hidden multi-step workflows
- typed responses with Pydantic models

## Installation

With `pip`:

```bash
pip install matteraio
```

With Poetry:

```bash
poetry add matteraio
```

With `uv`:

```bash
uv add matteraio
```

## Quick Start

Create a bot token in Mattermost and pass it to `MattermostClient`.

```python
import asyncio

from matteraio import MattermostClient


async def main() -> None:
    async with MattermostClient(
        base_url="https://mattermost.example.com",
        token="YOUR_BOT_TOKEN",
    ) as client:
        bot = await client.init_session()
        print(bot.username)

        team = await client.teams.get_by_name("engineering")
        channel = await client.channels.get_by_name(team.id, "town-square")

        post = await client.posts.create(
            channel_id=channel.id,
            message="Hello from matteraio",
        )

        thread = await client.posts.thread(post.id)
        users = await client.users.search("alice", team_id=team.id, limit=10)

        print(post.id, len(thread.posts), [user.username for user in users])


asyncio.run(main())
```

If you need login/password authentication instead of a bot token, construct the client without
`token` and call `client.users.login(...)`. Token changes inside one client instance are not
supported; create a new client when credentials change.

## WebSocket Handlers

Use routers and decorators to handle incoming WebSocket events.

```python
from matteraio import MattermostEventDispatcher, MattermostWebSocketClient, PostedEvent

dispatcher = MattermostEventDispatcher()


@dispatcher.on(PostedEvent)
async def on_posted(event: PostedEvent) -> None:
    print(event.data.post.message)


async def main() -> None:
    async with MattermostWebSocketClient(
        base_url="https://mattermost.example.com",
        token="YOUR_BOT_TOKEN",
    ) as websocket:
        await dispatcher.start(websocket)
```

## Documentation

- [Endpoint reference](https://github.com/Sergeydmitr/MatterAio/blob/main/docs/endpoints.md):
  REST docs split by Mattermost API area, plus WebSocket and handler references.

## Development

Install development dependencies:

```bash
uv sync --all-groups
```

Run local checks:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

Run opt-in integration tests against a local Mattermost preview server:

```bash
docker compose -f docker-compose.integration.yml up -d
MATTERAIO_RUN_INTEGRATION=1 uv run pytest tests/integration -m integration
docker compose -f docker-compose.integration.yml down -v
```

Set `MATTERAIO_BASE_URL` to override the default integration server URL.

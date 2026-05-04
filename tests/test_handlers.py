from __future__ import annotations

import unittest
from typing import Any, cast

from matteraio import (
    MattermostEventDispatcher,
    MattermostEventRouter,
    MattermostWebSocketClient,
    PostedEvent,
    WebSocketHandlerEvent,
    WebSocketMessage,
)


def _posted_event(*, team_id: str = "team-1") -> PostedEvent:
    return PostedEvent.model_validate(
        {
            "event": "posted",
            "data": {
                "post": {
                    "id": "post-1",
                    "channel_id": "channel-1",
                    "message": "hello",
                    "user_id": "user-1",
                },
                "team_id": team_id,
            },
            "broadcast": {"channel_id": "channel-1", "team_id": team_id},
            "seq": 1,
        }
    )


class FakeEventClient:
    def __init__(self, events: list[WebSocketHandlerEvent]) -> None:
        self.events = events
        self.timeouts: list[float | None] = []

    async def receive_event(self, *, timeout: float | None = None) -> WebSocketHandlerEvent:
        self.timeouts.append(timeout)
        return self.events.pop(0)


class MattermostEventRouterTests(unittest.IsolatedAsyncioTestCase):
    async def test_on_decorator_dispatches_matching_typed_event(self) -> None:
        router = MattermostEventRouter()
        handled_post_ids: list[str] = []

        @router.on(PostedEvent)
        async def on_posted(event: PostedEvent) -> None:
            handled_post_ids.append(event.data.post.id)

        handled = await router.dispatch(_posted_event())
        skipped = await router.dispatch(WebSocketMessage(status="OK", seq_reply=1))

        self.assertEqual(handled, 1)
        self.assertEqual(skipped, 0)
        self.assertEqual(handled_post_ids, ["post-1"])

    async def test_event_alias_dispatches_matching_event_name_with_filters(self) -> None:
        router = MattermostEventRouter()
        handled_teams: list[str | None] = []

        async def only_team_one(event: WebSocketHandlerEvent) -> bool:
            return event.event == "posted" and cast(PostedEvent, event).data.team_id == "team-1"

        @router.event("posted", only_team_one)
        async def on_team_post(event: WebSocketHandlerEvent) -> None:
            handled_teams.append(cast(PostedEvent, event).data.team_id)

        handled = await router.dispatch(_posted_event(team_id="team-1"))
        skipped = await router.dispatch(_posted_event(team_id="team-2"))

        self.assertEqual(handled, 1)
        self.assertEqual(skipped, 0)
        self.assertEqual(handled_teams, ["team-1"])

    async def test_include_router_dispatches_child_handlers(self) -> None:
        root = MattermostEventDispatcher()
        child = MattermostEventRouter(name="posts")
        root.include_router(child)

        handled_events: list[str] = []

        @child.on("posted")
        async def on_child_post(event: WebSocketHandlerEvent) -> None:
            handled_events.append(cast(PostedEvent, event).event)

        handled = await root.feed_event(_posted_event())

        self.assertEqual(handled, 1)
        self.assertEqual(handled_events, ["posted"])

    async def test_dispatch_next_receives_event_from_websocket_client(self) -> None:
        dispatcher = MattermostEventDispatcher()
        received: list[str] = []

        @dispatcher.on("posted")
        async def on_posted(event: WebSocketHandlerEvent) -> None:
            received.append(cast(PostedEvent, event).data.post.id)

        client = FakeEventClient([_posted_event()])

        handled = await dispatcher.dispatch_next(
            cast(MattermostWebSocketClient, client),
            timeout=0.5,
        )

        self.assertEqual(handled, 1)
        self.assertEqual(received, ["post-1"])
        self.assertEqual(client.timeouts, [0.5])

    async def test_sync_handler_raises_type_error_at_dispatch_time(self) -> None:
        router = MattermostEventRouter()

        def on_posted(event: WebSocketHandlerEvent) -> None:
            _ = event

        router.register(cast(Any, on_posted), selector="posted")

        with self.assertRaisesRegex(TypeError, "async callables"):
            await router.dispatch(_posted_event())

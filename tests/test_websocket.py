from __future__ import annotations

import asyncio
import json
import unittest
from collections.abc import Awaitable
from typing import Any, cast
from unittest.mock import patch

from matteraio import (
    HelloEvent,
    MattermostWebSocketClient,
    PostedEvent,
    WebSocketDisconnectedError,
    WebSocketMessage,
    WebSocketNotConnectedError,
    WebSocketProtocolError,
    WebSocketTimeoutError,
    parse_websocket_event,
)


class FakeWebSocketConnection:
    def __init__(self, incoming: list[Any]) -> None:
        self.incoming = incoming
        self.sent: list[str] = []
        self.closed = False
        self.close_code: int | None = None
        self.close_reason: str | None = None
        self.ping_payloads: list[str | bytes | bytearray | memoryview | None] = []

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def recv(self) -> Any:
        return self.incoming.pop(0)

    async def ping(
        self,
        data: str | bytes | bytearray | memoryview | None = None,
    ) -> Awaitable[float]:
        self.ping_payloads.append(data)

        async def waiter() -> float:
            return 0.05

        return waiter()

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = True
        self.close_code = code
        self.close_reason = reason


class MattermostWebSocketClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_authenticate_sends_expected_command_and_parses_messages(self) -> None:
        fake_connection = FakeWebSocketConnection(
            incoming=[
                json.dumps(
                    {
                        "event": "hello",
                        "data": {
                            "connection_id": "conn-1",
                            "server_version": "11.6.0",
                        },
                        "seq": 0,
                    }
                ),
                json.dumps({"status": "OK", "seq_reply": 1}),
            ]
        )

        async def fake_connect(uri: str, **kwargs: Any) -> FakeWebSocketConnection:
            self.assertEqual(uri, "wss://mattermost.example.com/api/v4/websocket")
            self.assertEqual(kwargs["ping_interval"], 20.0)
            return fake_connection

        with patch("matteraio.websocket.connect", new=fake_connect):
            client = MattermostWebSocketClient(
                "https://mattermost.example.com",
                "token-123",
            )
            await client.connect()
            seq = await client.authenticate()
            hello = await client.receive_message()
            ack = await client.receive_message()
            await client.aclose()

        self.assertEqual(seq, 1)
        self.assertEqual(
            json.loads(fake_connection.sent[0]),
            {
                "seq": 1,
                "action": "authentication_challenge",
                "data": {"token": "token-123"},
            },
        )
        self.assertTrue(hello.is_event)
        self.assertEqual(hello.event, "hello")
        self.assertEqual(hello.data["connection_id"], "conn-1")
        self.assertTrue(ack.is_reply)
        self.assertEqual(ack.status, "OK")
        self.assertEqual(ack.seq_reply, 1)
        self.assertTrue(fake_connection.closed)

    async def test_send_command_requires_open_connection(self) -> None:
        client = MattermostWebSocketClient(
            "https://mattermost.example.com",
            "token-123",
        )

        with self.assertRaises(WebSocketNotConnectedError):
            await client.send_command("authentication_challenge", {"token": "token-123"})

    async def test_receive_json_rejects_binary_frames(self) -> None:
        fake_connection = FakeWebSocketConnection(incoming=[b"\x00\x01"])

        async def fake_connect(uri: str, **kwargs: Any) -> FakeWebSocketConnection:
            return fake_connection

        with patch("matteraio.websocket.connect", new=fake_connect):
            client = MattermostWebSocketClient(
                "https://mattermost.example.com",
                "token-123",
            )
            await client.connect()
            with self.assertRaises(WebSocketProtocolError):
                await client.receive_json()

    async def test_reconnect_retries_with_backoff(self) -> None:
        connected = FakeWebSocketConnection(incoming=[])
        sleep_calls: list[float] = []
        attempts = 0

        async def fake_connect(uri: str, **kwargs: Any) -> FakeWebSocketConnection:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise OSError("temporary failure")
            return connected

        async def fake_sleep(delay: float) -> None:
            sleep_calls.append(delay)

        with (
            patch("matteraio.websocket.connect", new=fake_connect),
            patch("matteraio.websocket.asyncio.sleep", new=fake_sleep),
        ):
            client = MattermostWebSocketClient(
                "https://mattermost.example.com",
                "token-123",
                reconnect_initial_delay=1.0,
                reconnect_max_delay=4.0,
                reconnect_max_attempts=3,
            )
            await client.reconnect()

        self.assertTrue(client.is_connected)
        self.assertEqual(attempts, 3)
        self.assertEqual(sleep_calls, [1.0, 2.0])

    async def test_reconnect_restores_authentication_if_it_was_requested(self) -> None:
        first = FakeWebSocketConnection(incoming=[])
        second = FakeWebSocketConnection(incoming=[])
        connections = [first, second]

        async def fake_connect(uri: str, **kwargs: Any) -> FakeWebSocketConnection:
            return connections.pop(0)

        with patch("matteraio.websocket.connect", new=fake_connect):
            client = MattermostWebSocketClient(
                "https://mattermost.example.com",
                "token-123",
            )
            await client.connect()
            await client.authenticate()
            await client.reconnect()

        self.assertTrue(first.closed)
        self.assertEqual(
            json.loads(second.sent[0]),
            {
                "seq": 2,
                "action": "authentication_challenge",
                "data": {"token": "token-123"},
            },
        )

    async def test_ping_returns_latency(self) -> None:
        fake_connection = FakeWebSocketConnection(incoming=[])

        async def fake_connect(uri: str, **kwargs: Any) -> FakeWebSocketConnection:
            return fake_connection

        with patch("matteraio.websocket.connect", new=fake_connect):
            client = MattermostWebSocketClient(
                "https://mattermost.example.com",
                "token-123",
            )
            await client.connect()
            latency = await client.ping("heartbeat")

        self.assertEqual(latency, 0.05)
        self.assertEqual(fake_connection.ping_payloads, ["heartbeat"])

    async def test_receive_json_raises_timeout_error(self) -> None:
        class SlowWebSocketConnection(FakeWebSocketConnection):
            async def recv(self) -> Any:
                await asyncio.sleep(1)
                return {}

        fake_connection = SlowWebSocketConnection(incoming=[])

        async def fake_connect(uri: str, **kwargs: Any) -> FakeWebSocketConnection:
            return fake_connection

        with patch("matteraio.websocket.connect", new=fake_connect):
            client = MattermostWebSocketClient(
                "https://mattermost.example.com",
                "token-123",
            )
            await client.connect()
            with self.assertRaises(WebSocketTimeoutError):
                await client.receive_json(timeout=0.01)

    async def test_receive_json_marks_connection_closed(self) -> None:
        fake_connection = FakeWebSocketConnection(incoming=[])

        async def fake_connect(uri: str, **kwargs: Any) -> FakeWebSocketConnection:
            return fake_connection

        with patch("matteraio.websocket.connect", new=fake_connect):
            client = MattermostWebSocketClient(
                "https://mattermost.example.com",
                "token-123",
            )
            await client.connect()

        fake_connection.close_code = 1001
        fake_connection.close_reason = "server restart"

        with self.assertRaises(WebSocketDisconnectedError) as exc_info:
            await client.send_command("user_typing")

        self.assertEqual(exc_info.exception.close_code, 1001)
        self.assertEqual(exc_info.exception.close_reason, "server restart")

    async def test_receive_event_parses_hello_event(self) -> None:
        fake_connection = FakeWebSocketConnection(
            incoming=[
                json.dumps(
                    {
                        "event": "hello",
                        "data": {
                            "connection_id": "conn-1",
                            "server_version": "11.6.0",
                        },
                        "broadcast": {
                            "user_id": "user-1",
                            "channel_id": "",
                            "team_id": "",
                            "connection_id": "",
                            "omit_connection_id": "",
                        },
                        "seq": 7,
                    }
                )
            ]
        )

        async def fake_connect(uri: str, **kwargs: Any) -> FakeWebSocketConnection:
            return fake_connection

        with patch("matteraio.websocket.connect", new=fake_connect):
            client = MattermostWebSocketClient(
                "https://mattermost.example.com",
                "token-123",
            )
            await client.connect()
            event = cast(HelloEvent, await client.receive_event())

        self.assertIsInstance(event, HelloEvent)
        self.assertEqual(event.data.connection_id, "conn-1")
        self.assertEqual(event.seq, 7)

    async def test_receive_event_parses_posted_event(self) -> None:
        fake_connection = FakeWebSocketConnection(
            incoming=[
                json.dumps(
                    {
                        "event": "posted",
                        "data": {
                            "channel_display_name": "Town Square",
                            "channel_name": "town-square",
                            "channel_type": "O",
                            "mentions": "[\"user-1\"]",
                            "post": json.dumps(
                                {
                                    "id": "post-1",
                                    "channel_id": "channel-1",
                                    "message": "hello",
                                    "user_id": "user-2",
                                }
                            ),
                            "sender_name": "alice",
                            "set_online": True,
                            "team_id": "team-1",
                        },
                        "broadcast": {
                            "channel_id": "channel-1",
                            "user_id": "",
                        },
                        "seq": 8,
                    }
                )
            ]
        )

        async def fake_connect(uri: str, **kwargs: Any) -> FakeWebSocketConnection:
            return fake_connection

        with patch("matteraio.websocket.connect", new=fake_connect):
            client = MattermostWebSocketClient(
                "https://mattermost.example.com",
                "token-123",
            )
            await client.connect()
            event = cast(PostedEvent, await client.receive_event())

        self.assertIsInstance(event, PostedEvent)
        self.assertEqual(event.data.post.id, "post-1")
        self.assertEqual(event.data.post.message, "hello")
        self.assertEqual(event.data.mentions, ["user-1"])
        self.assertEqual(event.data.team_id, "team-1")

    def test_parse_websocket_event_returns_generic_message_for_unknown_event(self) -> None:
        message = WebSocketMessage.model_validate(
            {
                "event": "preferences_changed",
                "data": {"user_id": "user-1"},
                "seq": 9,
            }
        )

        parsed = parse_websocket_event(message)

        self.assertIs(parsed, message)

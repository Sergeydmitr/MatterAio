from __future__ import annotations

import json
import unittest
from typing import Any
from unittest.mock import patch

from matteraio import (
    MattermostWebSocketClient,
    WebSocketNotConnectedError,
    WebSocketProtocolError,
)


class FakeWebSocketConnection:
    def __init__(self, incoming: list[Any]) -> None:
        self.incoming = incoming
        self.sent: list[str] = []
        self.closed = False

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def recv(self) -> Any:
        return self.incoming.pop(0)

    async def close(self) -> None:
        self.closed = True


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

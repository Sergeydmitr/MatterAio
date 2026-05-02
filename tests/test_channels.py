from __future__ import annotations

import unittest

import httpx

from matteraio import MattermostClient


class ChannelsResourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_channel_returns_typed_channel(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/channels/channel-1")
            return httpx.Response(
                200,
                json={
                    "id": "channel-1",
                    "team_id": "team-1",
                    "name": "town-square",
                    "display_name": "Town Square",
                    "type": "O",
                    "purpose": "Company-wide updates",
                    "header": "Welcome",
                    "total_msg_count": 42,
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            channel = await client.channels.get("channel-1")

        self.assertEqual(channel.id, "channel-1")
        self.assertEqual(channel.display_name, "Town Square")
        self.assertEqual(channel.total_msg_count, 42)

    async def test_list_channels_uses_team_endpoint_and_pagination(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/teams/team-1/channels")
            self.assertEqual(request.url.params["page"], "2")
            self.assertEqual(request.url.params["per_page"], "10")
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "channel-1",
                        "team_id": "team-1",
                        "name": "engineering",
                        "display_name": "Engineering",
                        "type": "O",
                    },
                    {
                        "id": "channel-2",
                        "team_id": "team-1",
                        "name": "incidents",
                        "display_name": "Incidents",
                        "type": "P",
                    },
                ],
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            channels = await client.channels.list("team-1", page=2, per_page=10)

        self.assertEqual(len(channels), 2)
        self.assertEqual(channels[0].name, "engineering")
        self.assertEqual(channels[1].type, "P")

    async def test_get_channel_by_name_uses_team_lookup_endpoint(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/teams/team-1/channels/name/town-square")
            return httpx.Response(
                200,
                json={
                    "id": "channel-1",
                    "team_id": "team-1",
                    "name": "town-square",
                    "display_name": "Town Square",
                    "type": "O",
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            channel = await client.channels.get_by_name("team-1", "town-square")

        self.assertEqual(channel.id, "channel-1")
        self.assertEqual(channel.name, "town-square")

    async def test_create_channel_sends_expected_payload(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/channels")
            self.assertEqual(
                request.read(),
                (
                    b'{"team_id":"team-1","name":"incidents",'
                    b'"display_name":"Incidents","type":"P","purpose":"On-call"}'
                ),
            )
            return httpx.Response(
                201,
                json={
                    "id": "channel-1",
                    "team_id": "team-1",
                    "name": "incidents",
                    "display_name": "Incidents",
                    "type": "P",
                    "purpose": "On-call",
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            channel = await client.channels.create(
                team_id="team-1",
                name="incidents",
                display_name="Incidents",
                type="P",
                purpose="On-call",
            )

        self.assertEqual(channel.id, "channel-1")
        self.assertEqual(channel.type, "P")

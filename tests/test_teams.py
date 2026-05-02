from __future__ import annotations

import unittest

import httpx

from matteraio import MattermostClient


class TeamsResourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_team_returns_typed_team(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/teams/team-1")
            return httpx.Response(
                200,
                json={
                    "id": "team-1",
                    "name": "engineering",
                    "display_name": "Engineering",
                    "type": "O",
                    "description": "Engineering team",
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            team = await client.teams.get("team-1")

        self.assertEqual(team.id, "team-1")
        self.assertEqual(team.display_name, "Engineering")
        self.assertEqual(team.description, "Engineering team")

    async def test_get_team_by_name_uses_name_lookup_endpoint(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/teams/name/engineering")
            return httpx.Response(
                200,
                json={
                    "id": "team-1",
                    "name": "engineering",
                    "display_name": "Engineering",
                    "type": "O",
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            team = await client.teams.get_by_name("engineering")

        self.assertEqual(team.id, "team-1")
        self.assertEqual(team.name, "engineering")

    async def test_create_team_sends_expected_payload(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/teams")
            self.assertEqual(
                request.read(),
                b'{"name":"engineering","display_name":"Engineering","type":"O"}',
            )
            return httpx.Response(
                201,
                json={
                    "id": "team-1",
                    "name": "engineering",
                    "display_name": "Engineering",
                    "type": "O",
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            team = await client.teams.create(
                name="engineering",
                display_name="Engineering",
            )

        self.assertEqual(team.id, "team-1")
        self.assertEqual(team.type, "O")

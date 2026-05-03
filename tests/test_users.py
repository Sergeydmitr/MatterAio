from __future__ import annotations

import json
import unittest

import httpx

from matteraio import MattermostClient, MattermostError


class UsersResourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_login_sends_credentials_and_stores_session_token(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/api/v4/users/login":
                self.assertEqual(request.method, "POST")
                self.assertNotIn("Authorization", request.headers)
                self.assertEqual(
                    request.read(),
                    b'{"login_id":"alice@example.com","password":"secret","token":"123456"}',
                )
                return httpx.Response(
                    201,
                    headers={"Token": "session-token"},
                    json={"id": "user-1", "username": "alice", "email": "alice@example.com"},
                )

            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/users/me")
            self.assertEqual(request.headers["Authorization"], "Bearer session-token")
            return httpx.Response(
                200,
                json={"id": "user-1", "username": "alice", "email": "alice@example.com"},
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            transport=transport,
        ) as client:
            login = await client.users.login(
                login_id="alice@example.com",
                password="secret",
                token="123456",
            )
            user = await client.users.me()

        self.assertEqual(login.token, "session-token")
        self.assertEqual(login.user.username, "alice")
        self.assertEqual(user.id, "user-1")

    async def test_login_requires_token_header(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                201,
                json={"id": "user-1", "username": "alice", "email": "alice@example.com"},
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            transport=transport,
        ) as client:
            with self.assertRaises(MattermostError):
                await client.users.login(login_id="alice@example.com", password="secret")

    async def test_get_user_lookup_endpoints_return_typed_users(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/api/v4/users/user-1":
                return httpx.Response(200, json={"id": "user-1", "username": "alice"})

            if request.url.path == "/api/v4/users/username/alice":
                return httpx.Response(200, json={"id": "user-1", "username": "alice"})

            self.assertEqual(request.url.raw_path, b"/api/v4/users/email/alice%40example.com")
            return httpx.Response(
                200,
                json={"id": "user-1", "username": "alice", "email": "alice@example.com"},
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            by_id = await client.users.get("user-1")
            by_username = await client.users.get_by_username("alice")
            by_email = await client.users.get_by_email("alice@example.com")

        self.assertEqual(by_id.username, "alice")
        self.assertEqual(by_username.id, "user-1")
        self.assertEqual(by_email.email, "alice@example.com")

    async def test_search_users_sends_expected_criteria(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/users/search")
            self.assertEqual(
                json.loads(request.read()),
                {
                    "term": "ali",
                    "team_id": "team-1",
                    "not_in_channel_id": "channel-1",
                    "allow_inactive": True,
                    "limit": 5,
                },
            )
            return httpx.Response(
                200,
                json=[
                    {"id": "user-1", "username": "alice", "email": "alice@example.com"},
                    {"id": "user-2", "username": "alina", "email": "alina@example.com"},
                ],
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            users = await client.users.search(
                "ali",
                team_id="team-1",
                not_in_channel_id="channel-1",
                allow_inactive=True,
                limit=5,
            )

        self.assertEqual([user.username for user in users], ["alice", "alina"])

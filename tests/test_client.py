from __future__ import annotations

import unittest

import httpx

from matteraio import (
    AuthError,
    MattermostClient,
    MattermostError,
    ResponseValidationError,
    TransportError,
)


class MattermostClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_users_me_uses_bearer_auth(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api/v4/users/me")
            self.assertEqual(request.headers["Authorization"], "Bearer token-123")
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
            user = await client.users.me()

        self.assertEqual(user.id, "user-1")
        self.assertEqual(user.username, "alice")

    async def test_init_session_fetches_and_caches_current_bot(self) -> None:
        request_count = 0

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal request_count
            request_count += 1
            self.assertEqual(request.url.path, "/api/v4/users/me")
            self.assertEqual(request.headers["Authorization"], "Bearer token-123")
            return httpx.Response(
                200,
                json={"id": "bot-1", "username": "release-bot", "email": "bot@example.com"},
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            first = await client.init_session()
            second = await client.init_session()
            required = client.require_session()

        self.assertIs(first, second)
        self.assertIs(first, required)
        self.assertEqual(first.user_id, "bot-1")
        self.assertEqual(first.username, "release-bot")
        self.assertEqual(first.email, "bot@example.com")
        self.assertEqual(request_count, 1)

    async def test_require_session_requires_init_session(self) -> None:
        transport = httpx.MockTransport(lambda request: httpx.Response(500))

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            with self.assertRaises(MattermostError):
                client.require_session()

    async def test_auth_error_is_raised_with_payload_details(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                401,
                json={
                    "id": "api.context.session_expired.app_error",
                    "message": "Invalid or expired session.",
                    "request_id": "req-123",
                    "status_code": 401,
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "bad-token",
            transport=transport,
        ) as client:
            with self.assertRaises(AuthError) as exc_info:
                await client.users.me()

        self.assertEqual(exc_info.exception.status_code, 401)
        self.assertEqual(exc_info.exception.error_id, "api.context.session_expired.app_error")
        self.assertEqual(exc_info.exception.request_id, "req-123")

    async def test_response_validation_error_includes_request_context(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api/v4/users/me")
            return httpx.Response(
                200,
                headers={"X-Request-Id": "req-456"},
                json={"id": "user-1"},
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            with self.assertRaises(ResponseValidationError) as exc_info:
                await client.users.me()

        self.assertEqual(exc_info.exception.method, "GET")
        self.assertEqual(exc_info.exception.path, "/api/v4/users/me")
        self.assertEqual(exc_info.exception.status_code, 200)
        self.assertEqual(exc_info.exception.request_id, "req-456")
        self.assertIn("user-1", exc_info.exception.raw_body or "")

    async def test_transport_errors_are_wrapped(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("boom", request=request)

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            with self.assertRaises(TransportError):
                await client.users.me()

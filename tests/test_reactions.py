from __future__ import annotations

import unittest

import httpx

from matteraio import MattermostClient


def _reaction_payload(emoji_name: str = "thumbsup") -> dict[str, object]:
    return {
        "user_id": "user-1",
        "post_id": "post-1",
        "emoji_name": emoji_name,
        "create_at": 123,
    }


class ReactionsResourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_add_reaction_sends_expected_payload(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/reactions")
            self.assertEqual(
                request.read(),
                b'{"user_id":"user-1","post_id":"post-1","emoji_name":"thumbsup"}',
            )
            return httpx.Response(201, json=_reaction_payload())

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            reaction = await client.reactions.add(
                user_id="user-1",
                post_id="post-1",
                emoji_name="thumbsup",
            )

        self.assertEqual(reaction.user_id, "user-1")
        self.assertEqual(reaction.post_id, "post-1")
        self.assertEqual(reaction.emoji_name, "thumbsup")
        self.assertEqual(reaction.create_at, 123)

    async def test_remove_reaction_returns_status_ok(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "DELETE")
            self.assertEqual(
                request.url.path,
                "/api/v4/users/user-1/posts/post-1/reactions/thumbsup",
            )
            return httpx.Response(200, json={"status": "OK"})

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            result = await client.reactions.remove("user-1", "post-1", "thumbsup")

        self.assertEqual(result.status, "OK")

    async def test_list_reactions_for_post_returns_typed_reactions(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/posts/post-1/reactions")
            return httpx.Response(
                200,
                json=[_reaction_payload("thumbsup"), _reaction_payload("eyes")],
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            reactions = await client.reactions.list("post-1")

        self.assertEqual([reaction.emoji_name for reaction in reactions], ["thumbsup", "eyes"])

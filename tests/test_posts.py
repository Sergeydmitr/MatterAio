from __future__ import annotations

import unittest

import httpx

from matteraio import MattermostClient


class PostsResourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_post_sends_expected_payload(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/posts")
            self.assertEqual(request.read(), b'{"channel_id":"channel-1","message":"hello"}')
            return httpx.Response(
                201,
                json={
                    "id": "post-1",
                    "channel_id": "channel-1",
                    "message": "hello",
                    "user_id": "user-1",
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            post = await client.posts.create(channel_id="channel-1", message="hello")

        self.assertEqual(post.id, "post-1")
        self.assertEqual(post.channel_id, "channel-1")
        self.assertEqual(post.message, "hello")

    async def test_create_post_accepts_file_ids(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/posts")
            self.assertEqual(
                request.read(),
                b'{"channel_id":"channel-1","message":"with file","file_ids":["file-1","file-2"]}',
            )
            return httpx.Response(
                201,
                json={
                    "id": "post-2",
                    "channel_id": "channel-1",
                    "message": "with file",
                    "user_id": "user-1",
                    "file_ids": ["file-1", "file-2"],
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            post = await client.posts.create(
                channel_id="channel-1",
                message="with file",
                file_ids=["file-1", "file-2"],
            )

        self.assertEqual(post.id, "post-2")
        self.assertEqual(post.file_ids, ["file-1", "file-2"])

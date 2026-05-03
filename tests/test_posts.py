from __future__ import annotations

import unittest

import httpx

from matteraio import MattermostClient


def _post_payload(post_id: str = "post-1", message: str = "hello") -> dict[str, object]:
    return {
        "id": post_id,
        "channel_id": "channel-1",
        "message": message,
        "user_id": "user-1",
    }


def _post_list_payload(post_id: str = "post-1", message: str = "hello") -> dict[str, object]:
    return {
        "order": [post_id],
        "posts": {post_id: _post_payload(post_id, message)},
    }


def _file_info_payload(file_id: str = "file-1") -> dict[str, object]:
    return {
        "id": file_id,
        "user_id": "user-1",
        "channel_id": "channel-1",
        "post_id": "post-1",
        "name": "note.txt",
        "extension": "txt",
        "size": 12,
        "mime_type": "text/plain",
    }


class PostsResourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_post_returns_typed_post(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/posts/post-1")
            self.assertEqual(request.url.params["include_deleted"], "true")
            return httpx.Response(
                200,
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
            post = await client.posts.get("post-1", include_deleted=True)

        self.assertEqual(post.id, "post-1")
        self.assertEqual(post.message, "hello")

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

    async def test_update_patch_and_delete_post(self) -> None:
        calls: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if len(calls) == 1:
                self.assertEqual(request.method, "PUT")
                self.assertEqual(request.url.path, "/api/v4/posts/post-1")
                self.assertEqual(
                    request.read(),
                    b'{"id":"post-1","message":"updated","is_pinned":true}',
                )
                return httpx.Response(
                    200, json=_post_payload(message="updated") | {"is_pinned": True}
                )

            if len(calls) == 2:
                self.assertEqual(request.method, "PUT")
                self.assertEqual(request.url.path, "/api/v4/posts/post-1/patch")
                self.assertEqual(
                    request.read(),
                    b'{"message":"patched","file_ids":["file-1"]}',
                )
                return httpx.Response(200, json=_post_payload(message="patched"))

            self.assertEqual(request.method, "DELETE")
            self.assertEqual(request.url.path, "/api/v4/posts/post-1")
            return httpx.Response(200, json={"status": "OK"})

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            updated = await client.posts.update("post-1", message="updated", is_pinned=True)
            patched = await client.posts.patch("post-1", message="patched", file_ids=["file-1"])
            deleted = await client.posts.delete("post-1")

        self.assertTrue(updated.is_pinned)
        self.assertEqual(patched.message, "patched")
        self.assertEqual(deleted.status, "OK")
        self.assertEqual(
            calls, ["/api/v4/posts/post-1", "/api/v4/posts/post-1/patch", "/api/v4/posts/post-1"]
        )

    async def test_get_thread_and_channel_history(self) -> None:
        calls: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if len(calls) == 1:
                self.assertEqual(request.method, "GET")
                self.assertEqual(request.url.path, "/api/v4/posts/post-1/thread")
                self.assertEqual(request.url.params["perPage"], "20")
                self.assertEqual(request.url.params["fromPost"], "post-0")
                self.assertEqual(request.url.params["direction"], "up")
                self.assertEqual(request.url.params["collapsedThreads"], "true")
                return httpx.Response(200, json=_post_list_payload())

            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/channels/channel-1/posts")
            self.assertEqual(request.url.params["page"], "2")
            self.assertEqual(request.url.params["per_page"], "10")
            self.assertEqual(request.url.params["before"], "post-3")
            self.assertEqual(request.url.params["include_deleted"], "true")
            self.assertEqual(request.url.params["type"], "files")
            return httpx.Response(200, json=_post_list_payload("post-2", "older"))

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            thread = await client.posts.thread(
                "post-1",
                per_page=20,
                from_post="post-0",
                direction="up",
                collapsed_threads=True,
            )
            history = await client.posts.list(
                "channel-1",
                page=2,
                per_page=10,
                before="post-3",
                include_deleted=True,
                type="files",
            )

        self.assertEqual(thread.order, ["post-1"])
        self.assertEqual(history.order, ["post-2"])

    async def test_search_posts_sends_expected_payload(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/teams/team-1/posts/search")
            self.assertEqual(
                request.read(),
                b'{"terms":"deploy","is_or_search":true,"time_zone_offset":180,"page":1,"per_page":20}',
            )
            return httpx.Response(
                200,
                json=_post_list_payload(message="deploy finished")
                | {"matches": {"post-1": ["deploy"]}},
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            result = await client.posts.search(
                "team-1",
                "deploy",
                is_or_search=True,
                time_zone_offset=180,
                page=1,
                per_page=20,
            )

        self.assertEqual(result.order, ["post-1"])
        self.assertEqual(result.matches, {"post-1": ["deploy"]})

    async def test_pin_unpin_and_get_by_ids(self) -> None:
        calls: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if len(calls) == 1:
                self.assertEqual(request.method, "POST")
                self.assertEqual(request.url.path, "/api/v4/posts/post-1/pin")
                return httpx.Response(200, json={"status": "OK"})

            if len(calls) == 2:
                self.assertEqual(request.method, "POST")
                self.assertEqual(request.url.path, "/api/v4/posts/post-1/unpin")
                return httpx.Response(200, json={"status": "OK"})

            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/posts/ids")
            self.assertEqual(request.read(), b'["post-1","post-2"]')
            return httpx.Response(
                200,
                json=[_post_payload("post-1"), _post_payload("post-2", "second")],
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            pinned = await client.posts.pin("post-1")
            unpinned = await client.posts.unpin("post-1")
            posts = await client.posts.get_by_ids(["post-1", "post-2"])

        self.assertEqual(pinned.status, "OK")
        self.assertEqual(unpinned.status, "OK")
        self.assertEqual([post.id for post in posts], ["post-1", "post-2"])

    async def test_get_post_file_info(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/posts/post-1/files/info")
            self.assertEqual(request.url.params["include_deleted"], "true")
            return httpx.Response(200, json=[_file_info_payload()])

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            files = await client.posts.files_info("post-1", include_deleted=True)

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].id, "file-1")

    async def test_channel_history_rejects_since_with_pagination(self) -> None:
        transport = httpx.MockTransport(lambda request: httpx.Response(500))

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            with self.assertRaises(ValueError):
                await client.posts.list("channel-1", since=1, page=1)

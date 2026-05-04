from __future__ import annotations

import unittest

import httpx

from matteraio import MattermostClient


class FilesResourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_file_info_returns_typed_file_info(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/files/file-1/info")
            return httpx.Response(
                200,
                json={
                    "id": "file-1",
                    "user_id": "user-1",
                    "channel_id": "channel-1",
                    "name": "note.txt",
                    "extension": "txt",
                    "size": 10,
                    "mime_type": "text/plain",
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            file_info = await client.files.info("file-1")

        self.assertEqual(file_info.id, "file-1")
        self.assertEqual(file_info.name, "note.txt")

    async def test_download_file_returns_response_content(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/files/file-1")
            return httpx.Response(200, content=b"hello file")

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            content = await client.files.download("file-1")

        self.assertEqual(content, b"hello file")

    async def test_file_paths_quote_segments(self) -> None:
        calls: list[bytes] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.raw_path)

            if len(calls) == 1:
                return httpx.Response(
                    200,
                    json={
                        "id": "file/1",
                        "user_id": "user-1",
                        "channel_id": "channel-1",
                        "name": "note.txt",
                    },
                )

            return httpx.Response(200, content=b"file")

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            file_info = await client.files.info("file/1")
            content = await client.files.download("file/1")

        self.assertEqual(file_info.id, "file/1")
        self.assertEqual(content, b"file")
        self.assertEqual(
            calls,
            [
                b"/api/v4/files/file%2F1/info",
                b"/api/v4/files/file%2F1",
            ],
        )

    async def test_upload_file_uses_multipart_form_data(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            body = request.read()

            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/files")
            self.assertTrue(request.headers["Content-Type"].startswith("multipart/form-data"))
            self.assertIn(b'name="channel_id"', body)
            self.assertIn(b"channel-1", body)
            self.assertIn(b'name="client_ids"', body)
            self.assertIn(b"client-1", body)
            self.assertIn(b'name="files"; filename="note.txt"', body)
            self.assertIn(b"hello file", body)

            return httpx.Response(
                201,
                json={
                    "file_infos": [
                        {
                            "id": "file-1",
                            "user_id": "user-1",
                            "channel_id": "channel-1",
                            "name": "note.txt",
                            "extension": "txt",
                            "size": 10,
                            "mime_type": "text/plain",
                            "has_preview_image": False,
                        }
                    ],
                    "client_ids": ["client-1"],
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            upload = await client.files.upload(
                channel_id="channel-1",
                filename="note.txt",
                content=b"hello file",
                content_type="text/plain",
                client_id="client-1",
            )

        self.assertEqual(upload.client_ids, ["client-1"])
        self.assertEqual(upload.file_infos[0].id, "file-1")
        self.assertEqual(upload.file_infos[0].name, "note.txt")

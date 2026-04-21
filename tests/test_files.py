from __future__ import annotations

import unittest

import httpx

from matteraio import MattermostClient


class FilesResourceTests(unittest.IsolatedAsyncioTestCase):
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

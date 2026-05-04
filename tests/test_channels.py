from __future__ import annotations

import unittest

import httpx

from matteraio import MattermostClient


def _channel_payload(
    channel_id: str = "channel-1",
    team_id: str = "team-1",
    name: str = "town-square",
    display_name: str = "Town Square",
    type: str = "O",
) -> dict[str, object]:
    return {
        "id": channel_id,
        "team_id": team_id,
        "name": name,
        "display_name": display_name,
        "type": type,
    }


def _channel_member_payload(
    channel_id: str = "channel-1",
    user_id: str = "user-1",
    roles: str = "channel_user",
) -> dict[str, object]:
    return {
        "channel_id": channel_id,
        "user_id": user_id,
        "roles": roles,
        "last_viewed_at": 1000,
        "msg_count": 5,
        "mention_count": 1,
    }


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

    async def test_update_channel_sends_full_payload(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "PUT")
            self.assertEqual(request.url.path, "/api/v4/channels/channel-1")
            self.assertEqual(
                request.read(),
                (
                    b'{"id":"channel-1","name":"engineering",'
                    b'"display_name":"Engineering","purpose":"Build",'
                    b'"header":"Deploy notes"}'
                ),
            )
            return httpx.Response(
                200,
                json={
                    **_channel_payload(name="engineering", display_name="Engineering"),
                    "purpose": "Build",
                    "header": "Deploy notes",
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            channel = await client.channels.update(
                "channel-1",
                name="engineering",
                display_name="Engineering",
                purpose="Build",
                header="Deploy notes",
            )

        self.assertEqual(channel.name, "engineering")
        self.assertEqual(channel.header, "Deploy notes")

    async def test_patch_channel_sends_partial_payload(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "PUT")
            self.assertEqual(request.url.path, "/api/v4/channels/channel-1/patch")
            self.assertEqual(
                request.read(),
                b'{"display_name":"Engineering","autotranslation":true}',
            )
            return httpx.Response(
                200,
                json={
                    **_channel_payload(display_name="Engineering"),
                    "autotranslation": True,
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            channel = await client.channels.patch(
                "channel-1",
                display_name="Engineering",
                autotranslation=True,
            )

        self.assertEqual(channel.display_name, "Engineering")

    async def test_delete_restore_and_archive_aliases(self) -> None:
        calls: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)

            if len(calls) == 1:
                self.assertEqual(request.method, "DELETE")
                self.assertEqual(request.url.path, "/api/v4/channels/channel-1")
                self.assertEqual(request.url.params["permanent"], "true")
                return httpx.Response(200, json={"status": "OK"})

            if len(calls) == 2:
                self.assertEqual(request.method, "POST")
                self.assertEqual(request.url.path, "/api/v4/channels/channel-1/restore")
                return httpx.Response(200, json=_channel_payload())

            if len(calls) == 3:
                self.assertEqual(request.method, "DELETE")
                self.assertEqual(request.url.path, "/api/v4/channels/channel-1")
                self.assertEqual(request.url.params["permanent"], "false")
                return httpx.Response(200, json={"status": "OK"})

            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/channels/channel-1/restore")
            return httpx.Response(200, json=_channel_payload())

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            deleted = await client.channels.delete("channel-1", permanent=True)
            restored = await client.channels.restore("channel-1")
            archived = await client.channels.archive("channel-1")
            unarchived = await client.channels.unarchive("channel-1")

        self.assertEqual(deleted.status, "OK")
        self.assertEqual(restored.id, "channel-1")
        self.assertEqual(archived.status, "OK")
        self.assertEqual(unarchived.id, "channel-1")
        self.assertEqual(
            calls,
            [
                "/api/v4/channels/channel-1",
                "/api/v4/channels/channel-1/restore",
                "/api/v4/channels/channel-1",
                "/api/v4/channels/channel-1/restore",
            ],
        )

    async def test_channel_member_endpoints_and_join_leave_aliases(self) -> None:
        calls: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)

            if len(calls) == 1:
                self.assertEqual(request.method, "GET")
                self.assertEqual(request.url.path, "/api/v4/channels/channel-1/members")
                self.assertEqual(request.url.params["page"], "1")
                self.assertEqual(request.url.params["per_page"], "5")
                return httpx.Response(200, json=[_channel_member_payload()])

            if len(calls) == 2:
                self.assertEqual(request.method, "POST")
                self.assertEqual(request.url.path, "/api/v4/channels/channel-1/members")
                self.assertEqual(request.read(), b'{"user_id":"user-1","post_root_id":"post-1"}')
                return httpx.Response(201, json=_channel_member_payload())

            if len(calls) == 3:
                self.assertEqual(request.method, "POST")
                self.assertEqual(request.url.path, "/api/v4/channels/channel-1/members")
                self.assertEqual(request.read(), b'{"user_id":"user-2"}')
                return httpx.Response(201, json=_channel_member_payload(user_id="user-2"))

            if len(calls) == 4:
                self.assertEqual(request.method, "DELETE")
                self.assertEqual(request.url.path, "/api/v4/channels/channel-1/members/user-1")
                return httpx.Response(200, json={"status": "OK"})

            self.assertEqual(request.method, "DELETE")
            self.assertEqual(request.url.path, "/api/v4/channels/channel-1/members/user-2")
            return httpx.Response(200, json={"status": "OK"})

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            members = await client.channels.list_members("channel-1", page=1, per_page=5)
            added = await client.channels.add_member(
                "channel-1",
                "user-1",
                post_root_id="post-1",
            )
            joined = await client.channels.join("channel-1", "user-2")
            removed = await client.channels.remove_member("channel-1", "user-1")
            left = await client.channels.leave("channel-1", "user-2")

        self.assertEqual(members[0].user_id, "user-1")
        self.assertEqual(added.user_id, "user-1")
        self.assertEqual(joined.user_id, "user-2")
        self.assertEqual(removed.status, "OK")
        self.assertEqual(left.status, "OK")

    async def test_create_direct_and_group_channels(self) -> None:
        calls: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)

            if len(calls) == 1:
                self.assertEqual(request.method, "POST")
                self.assertEqual(request.url.path, "/api/v4/channels/direct")
                self.assertEqual(request.read(), b'["user-1","user-2"]')
                return httpx.Response(
                    201,
                    json=_channel_payload(
                        channel_id="direct-1",
                        team_id="",
                        name="user-1__user-2",
                        display_name="",
                        type="D",
                    ),
                )

            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/channels/group")
            self.assertEqual(request.read(), b'["user-1","user-2","user-3"]')
            return httpx.Response(
                201,
                json=_channel_payload(
                    channel_id="group-1",
                    team_id="",
                    name="group",
                    display_name="Group",
                    type="G",
                ),
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            direct = await client.channels.create_direct("user-1", "user-2")
            group = await client.channels.create_group(["user-1", "user-2", "user-3"])

        self.assertEqual(direct.type, "D")
        self.assertEqual(group.type, "G")

    async def test_search_channel_endpoints(self) -> None:
        calls: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)

            if len(calls) == 1:
                self.assertEqual(request.method, "POST")
                self.assertEqual(request.url.path, "/api/v4/teams/team-1/channels/search")
                self.assertEqual(request.read(), b'{"term":"town"}')
                return httpx.Response(201, json=[_channel_payload()])

            if len(calls) == 2:
                self.assertEqual(request.method, "POST")
                self.assertEqual(request.url.path, "/api/v4/channels/search")
                self.assertEqual(request.url.params["system_console"], "false")
                self.assertEqual(
                    request.read(),
                    b'{"term":"eng","team_ids":["team-1"],"public":true,"page":1,"per_page":20}',
                )
                return httpx.Response(
                    200,
                    json={"channels": [_channel_payload(name="engineering")], "total_count": 1},
                )

            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/channels/group/search")
            self.assertEqual(request.read(), b'{"term":"sergey"}')
            return httpx.Response(
                200,
                json=[
                    _channel_payload(
                        channel_id="group-1",
                        team_id="",
                        name="group",
                        display_name="Group",
                        type="G",
                    ),
                ],
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            team_channels = await client.channels.search("team-1", "town")
            all_channels = await client.channels.search_all(
                "eng",
                system_console=False,
                team_ids=["team-1"],
                public=True,
                page=1,
                per_page=20,
            )
            group_channels = await client.channels.search_group("sergey")

        self.assertEqual(team_channels[0].id, "channel-1")
        self.assertEqual(all_channels[0].name, "engineering")
        self.assertEqual(group_channels[0].type, "G")

    async def test_stats_unread_and_pinned_posts(self) -> None:
        calls: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)

            if len(calls) == 1:
                self.assertEqual(request.method, "GET")
                self.assertEqual(request.url.path, "/api/v4/channels/channel-1/stats")
                return httpx.Response(
                    200,
                    json={"channel_id": "channel-1", "member_count": 12},
                )

            if len(calls) == 2:
                self.assertEqual(request.method, "GET")
                self.assertEqual(request.url.path, "/api/v4/users/user-1/channels/channel-1/unread")
                return httpx.Response(
                    200,
                    json={
                        "team_id": "team-1",
                        "channel_id": "channel-1",
                        "msg_count": 3,
                        "mention_count": 1,
                    },
                )

            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/channels/channel-1/pinned")
            return httpx.Response(
                200,
                json={
                    "order": ["post-1"],
                    "posts": {
                        "post-1": {
                            "id": "post-1",
                            "channel_id": "channel-1",
                            "message": "Pinned",
                        },
                    },
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            stats = await client.channels.stats("channel-1")
            unread = await client.channels.unread("user-1", "channel-1")
            pinned = await client.channels.pinned_posts("channel-1")

        self.assertEqual(stats.member_count, 12)
        self.assertEqual(unread.mention_count, 1)
        self.assertEqual(pinned.order, ["post-1"])
        self.assertEqual(pinned.posts["post-1"].message, "Pinned")

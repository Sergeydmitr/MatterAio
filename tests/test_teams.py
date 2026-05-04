from __future__ import annotations

import unittest

import httpx

from matteraio import MattermostClient


def _team_payload(
    team_id: str = "team-1",
    name: str = "engineering",
    display_name: str = "Engineering",
    type: str = "O",
) -> dict[str, object]:
    return {
        "id": team_id,
        "name": name,
        "display_name": display_name,
        "type": type,
    }


def _team_member_payload(
    team_id: str = "team-1",
    user_id: str = "user-1",
    roles: str = "team_user",
) -> dict[str, object]:
    return {
        "team_id": team_id,
        "user_id": user_id,
        "roles": roles,
        "scheme_user": True,
        "scheme_admin": "team_admin" in roles,
    }


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

    async def test_list_teams_uses_pagination(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/teams")
            self.assertEqual(request.url.params["page"], "2")
            self.assertEqual(request.url.params["per_page"], "10")
            self.assertEqual(request.url.params["exclude_policy_constrained"], "true")
            return httpx.Response(
                200,
                json=[
                    _team_payload(),
                    _team_payload("team-2", "support", "Support"),
                ],
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            teams = await client.teams.list(
                page=2,
                per_page=10,
                exclude_policy_constrained=True,
            )

        self.assertEqual(len(teams), 2)
        self.assertEqual(teams[1].name, "support")

    async def test_iter_all_teams_fetches_until_short_page(self) -> None:
        pages: list[int] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api/v4/teams")
            self.assertEqual(request.url.params["per_page"], "2")
            page = int(request.url.params["page"])
            pages.append(page)

            if page == 0:
                return httpx.Response(
                    200,
                    json=[
                        _team_payload(),
                        _team_payload("team-2", "support", "Support"),
                    ],
                )

            return httpx.Response(200, json=[_team_payload("team-3", "sales", "Sales")])

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            teams = [team async for team in client.teams.iter_all(per_page=2)]

        self.assertEqual([team.name for team in teams], ["engineering", "support", "sales"])
        self.assertEqual(pages, [0, 1])

    async def test_team_member_paths_quote_segments(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                request.url.raw_path,
                b"/api/v4/teams/team%2F1/members/user%2F1",
            )
            return httpx.Response(
                200,
                json=_team_member_payload(team_id="team/1", user_id="user/1"),
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            member = await client.teams.get_member("team/1", "user/1")

        self.assertEqual(member.team_id, "team/1")
        self.assertEqual(member.user_id, "user/1")

    async def test_search_teams_sends_expected_payload(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/teams/search")
            self.assertEqual(
                request.read(),
                b'{"term":"eng","page":1,"per_page":20,"allow_open_invite":true}',
            )
            return httpx.Response(
                200,
                json={
                    "teams": [_team_payload()],
                    "total_count": 1,
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            teams = await client.teams.search(
                "eng",
                page=1,
                per_page=20,
                allow_open_invite=True,
            )

        self.assertEqual(len(teams), 1)
        self.assertEqual(teams[0].id, "team-1")

    async def test_update_team_sends_full_payload(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "PUT")
            self.assertEqual(request.url.path, "/api/v4/teams/team-1")
            self.assertEqual(
                request.read(),
                (
                    b'{"id":"team-1","display_name":"Engineering",'
                    b'"description":"Core engineering","company_name":"Example",'
                    b'"allowed_domains":"example.com","invite_id":"invite-1",'
                    b'"allow_open_invite":true}'
                ),
            )
            return httpx.Response(
                200,
                json={
                    **_team_payload(),
                    "description": "Core engineering",
                    "company_name": "Example",
                    "allowed_domains": "example.com",
                    "invite_id": "invite-1",
                    "allow_open_invite": True,
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            team = await client.teams.update(
                "team-1",
                display_name="Engineering",
                description="Core engineering",
                company_name="Example",
                allowed_domains="example.com",
                invite_id="invite-1",
                allow_open_invite=True,
            )

        self.assertEqual(team.company_name, "Example")
        self.assertTrue(team.allow_open_invite)

    async def test_patch_team_sends_partial_payload(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "PUT")
            self.assertEqual(request.url.path, "/api/v4/teams/team-1/patch")
            self.assertEqual(
                request.read(),
                b'{"description":"Updated description","allow_open_invite":false}',
            )
            return httpx.Response(
                200,
                json={
                    **_team_payload(),
                    "description": "Updated description",
                    "allow_open_invite": False,
                },
            )

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            team = await client.teams.patch(
                "team-1",
                description="Updated description",
                allow_open_invite=False,
            )

        self.assertEqual(team.description, "Updated description")
        self.assertFalse(team.allow_open_invite)

    async def test_delete_and_restore_team(self) -> None:
        calls: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)

            if len(calls) == 1:
                self.assertEqual(request.method, "DELETE")
                self.assertEqual(request.url.path, "/api/v4/teams/team-1")
                self.assertEqual(request.url.params["permanent"], "true")
                return httpx.Response(200, json={"status": "OK"})

            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/v4/teams/team-1/restore")
            return httpx.Response(200, json=_team_payload())

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            deleted = await client.teams.delete("team-1", permanent=True)
            restored = await client.teams.restore("team-1")

        self.assertEqual(deleted.status, "OK")
        self.assertEqual(restored.id, "team-1")
        self.assertEqual(calls, ["/api/v4/teams/team-1", "/api/v4/teams/team-1/restore"])

    async def test_team_member_endpoints(self) -> None:
        calls: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)

            if len(calls) == 1:
                self.assertEqual(request.method, "GET")
                self.assertEqual(request.url.path, "/api/v4/teams/team-1/members")
                self.assertEqual(request.url.params["page"], "1")
                self.assertEqual(request.url.params["per_page"], "5")
                self.assertEqual(request.url.params["sort"], "Username")
                self.assertEqual(request.url.params["exclude_deleted_users"], "true")
                return httpx.Response(200, json=[_team_member_payload()])

            if len(calls) == 2:
                self.assertEqual(request.method, "POST")
                self.assertEqual(request.url.path, "/api/v4/teams/team-1/members")
                self.assertEqual(request.read(), b'{"team_id":"team-1","user_id":"user-1"}')
                return httpx.Response(201, json=_team_member_payload())

            if len(calls) == 3:
                self.assertEqual(request.method, "GET")
                self.assertEqual(request.url.path, "/api/v4/teams/team-1/members/user-1")
                return httpx.Response(
                    200,
                    json=_team_member_payload(roles="team_user team_admin"),
                )

            if len(calls) == 4:
                self.assertEqual(request.method, "DELETE")
                self.assertEqual(request.url.path, "/api/v4/teams/team-1/members/user-1")
                return httpx.Response(200, json={"status": "OK"})

            self.assertEqual(request.method, "PUT")
            self.assertEqual(request.url.path, "/api/v4/teams/team-1/members/user-1/roles")
            self.assertEqual(request.read(), b'{"roles":"team_user team_admin"}')
            return httpx.Response(200, json={"status": "OK"})

        transport = httpx.MockTransport(handler)

        async with MattermostClient(
            "https://mattermost.example.com",
            "token-123",
            transport=transport,
        ) as client:
            members = await client.teams.list_members(
                "team-1",
                page=1,
                per_page=5,
                sort="Username",
                exclude_deleted_users=True,
            )
            added = await client.teams.add_member("team-1", "user-1")
            member = await client.teams.get_member("team-1", "user-1")
            removed = await client.teams.remove_member("team-1", "user-1")
            roles_updated = await client.teams.update_member_roles(
                "team-1",
                "user-1",
                "team_user team_admin",
            )

        self.assertEqual(members[0].user_id, "user-1")
        self.assertEqual(added.team_id, "team-1")
        self.assertEqual(member.roles, "team_user team_admin")
        self.assertEqual(removed.status, "OK")
        self.assertEqual(roles_updated.status, "OK")

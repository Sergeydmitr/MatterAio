# Teams

[Endpoint reference](../endpoints.md)

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.teams.get(team_id)` | `GET /teams/{team_id}` | Get a team by ID. |
| `client.teams.get_by_name(name)` | `GET /teams/name/{name}` | Get a team by URL-safe name. |
| `client.teams.list(...)` | `GET /teams` | List teams visible to the current user. |
| `client.teams.search(term, ...)` | `POST /teams/search` | Search teams by name or display name. |
| `client.teams.create(...)` | `POST /teams` | Create a team. Use `type="O"` for open teams and `type="I"` for invite-only teams. |
| `client.teams.update(team_id, ...)` | `PUT /teams/{team_id}` | Replace the editable team profile. |
| `client.teams.patch(team_id, ...)` | `PUT /teams/{team_id}/patch` | Patch provided team fields. |
| `client.teams.delete(team_id, permanent=False)` | `DELETE /teams/{team_id}` | Soft-delete a team by default. |
| `client.teams.restore(team_id)` | `POST /teams/{team_id}/restore` | Restore a soft-deleted team. |
| `client.teams.list_members(team_id, ...)` | `GET /teams/{team_id}/members` | List team members. |
| `client.teams.add_member(team_id, user_id)` | `POST /teams/{team_id}/members` | Add a user to a team. |
| `client.teams.get_member(team_id, user_id)` | `GET /teams/{team_id}/members/{user_id}` | Get a team member and their roles. |
| `client.teams.remove_member(team_id, user_id)` | `DELETE /teams/{team_id}/members/{user_id}` | Remove a user from a team. |
| `client.teams.update_member_roles(team_id, user_id, roles)` | `PUT /teams/{team_id}/members/{user_id}/roles` | Overwrite team roles, for example `team_user team_admin`. |

## Returned Data

Team lookup, list, search, create, update, patch, and restore methods return `Team` or
`list[Team]`.

| Field | Type | Description |
| --- | --- | --- |
| `id` | `str` | Mattermost team ID. |
| `name` | `str` | URL-safe team name. |
| `display_name` | `str` | Human-readable team name. |
| `type` | `str` | Team visibility, usually `O` for open or `I` for invite-only. |
| `description` | `str or None` | Team description when present. |
| `company_name` | `str or None` | Company name when configured. |
| `allowed_domains` | `str or None` | Allowed signup domains. |
| `invite_id` | `str or None` | Invite identifier when present. |
| `allow_open_invite` | `bool or None` | Whether open invites are allowed. |

Membership methods return `TeamMember` or `list[TeamMember]`.

| Field | Type | Description |
| --- | --- | --- |
| `team_id` | `str` | Team ID. |
| `user_id` | `str` | User ID. |
| `roles` | `str` | Space-separated Mattermost team roles. |
| `delete_at` | `int or None` | Deletion timestamp in milliseconds, if removed. |
| `scheme_user` | `bool or None` | Whether the member gets user permissions from a scheme. |
| `scheme_admin` | `bool or None` | Whether the member gets admin permissions from a scheme. |
| `explicit_roles` | `str or None` | Explicit roles when Mattermost returns them. |

`delete(...)`, `remove_member(...)`, and `update_member_roles(...)` return `StatusOK` with a
`status` field.

## Examples

```python
from matteraio import MattermostClient


async def main() -> None:
    async with MattermostClient(
        base_url="https://mattermost.example.com",
        token="YOUR_BOT_TOKEN",
    ) as client:
        team = await client.teams.get_by_name("engineering")
        teams = await client.teams.list(page=0, per_page=20)

        created = await client.teams.create(
            name="platform",
            display_name="Platform",
            type="O",
        )
        patched = await client.teams.patch(created.id, description="Platform team")

        member = await client.teams.add_member(patched.id, "user-id")
        await client.teams.update_member_roles(patched.id, member.user_id, "team_user team_admin")

        print(team.display_name, len(teams), member.roles)
```

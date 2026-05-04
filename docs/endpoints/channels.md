# Channels

[Endpoint reference](../endpoints.md)

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.channels.get(channel_id)` | `GET /channels/{channel_id}` | Get a channel by ID. |
| `client.channels.get_by_name(team_id, channel_name)` | `GET /teams/{team_id}/channels/name/{channel_name}` | Get a channel by name inside a team. |
| `client.channels.create(...)` | `POST /channels` | Create a public or private channel. |
| `client.channels.list(team_id, ...)` | `GET /teams/{team_id}/channels` | List channels for a team. |
| `client.channels.iter_all(team_id, ...)` | `GET /teams/{team_id}/channels` | Iterate team channels across pages. |
| `client.channels.update(channel_id, ...)` | `PUT /channels/{channel_id}` | Replace the editable channel profile. |
| `client.channels.patch(channel_id, ...)` | `PUT /channels/{channel_id}/patch` | Patch provided channel fields. |
| `client.channels.delete(channel_id, permanent=False)` | `DELETE /channels/{channel_id}` | Archive a channel by default. |
| `client.channels.restore(channel_id)` | `POST /channels/{channel_id}/restore` | Restore an archived channel. |
| `client.channels.archive(channel_id, ...)` | `DELETE /channels/{channel_id}` | Alias for `delete(...)`. |
| `client.channels.unarchive(channel_id)` | `POST /channels/{channel_id}/restore` | Alias for `restore(...)`. |
| `client.channels.list_members(channel_id, ...)` | `GET /channels/{channel_id}/members` | List channel members. |
| `client.channels.iter_members(channel_id, ...)` | `GET /channels/{channel_id}/members` | Iterate channel members across pages. |
| `client.channels.add_member(channel_id, user_id, ...)` | `POST /channels/{channel_id}/members` | Add a user to a channel. |
| `client.channels.remove_member(channel_id, user_id)` | `DELETE /channels/{channel_id}/members/{user_id}` | Remove a user from a channel. |
| `client.channels.join(channel_id, user_id, ...)` | `POST /channels/{channel_id}/members` | Alias for `add_member(...)`. |
| `client.channels.leave(channel_id, user_id)` | `DELETE /channels/{channel_id}/members/{user_id}` | Alias for `remove_member(...)`. |
| `client.channels.create_direct(user_id, other_user_id)` | `POST /channels/direct` | Create or get a direct message channel. |
| `client.channels.create_group(user_ids)` | `POST /channels/group` | Create or get a group message channel for 3 to 8 users. |
| `client.channels.search(team_id, term)` | `POST /teams/{team_id}/channels/search` | Search public channels inside a team. |
| `client.channels.search_all(term, ...)` | `POST /channels/search` | Search open and private channels across teams. |
| `client.channels.search_group(term)` | `POST /channels/group/search` | Search group message channels by member username. |
| `client.channels.stats(channel_id)` | `GET /channels/{channel_id}/stats` | Get channel statistics. |
| `client.channels.unread(user_id, channel_id)` | `GET /users/{user_id}/channels/{channel_id}/unread` | Get unread message and mention counts. |
| `client.channels.pinned_posts(channel_id)` | `GET /channels/{channel_id}/pinned` | Get pinned posts for a channel. |

## Returned Data

Channel lookup, list, search, create, update, patch, restore, direct, and group methods return
`Channel` or `list[Channel]`.

| Field | Type | Description |
| --- | --- | --- |
| `id` | `str` | Mattermost channel ID. |
| `team_id` | `str or None` | Team ID for team channels. Direct and group channels may omit it. |
| `name` | `str` | URL-safe channel name. |
| `display_name` | `str` | Human-readable channel name. |
| `type` | `str` | Channel type, such as `O`, `P`, `D`, or `G`. |
| `purpose` | `str or None` | Channel purpose text. |
| `header` | `str or None` | Channel header text. |
| `total_msg_count` | `int or None` | Total message count when returned by Mattermost. |

Member methods return `ChannelMember` or `list[ChannelMember]`.

| Field | Type | Description |
| --- | --- | --- |
| `channel_id` | `str` | Channel ID. |
| `user_id` | `str` | User ID. |
| `roles` | `str` | Space-separated Mattermost channel roles. |
| `last_viewed_at` | `int or None` | Last viewed timestamp in milliseconds. |
| `msg_count` | `int or None` | Message count visible to the member. |
| `mention_count` | `int or None` | Mention count for the member. |
| `notify_props` | `dict[str, str] or None` | Member notification preferences. |
| `last_update_at` | `int or None` | Last membership update timestamp in milliseconds. |
| `scheme_guest` | `bool or None` | Whether guest permissions come from a scheme. |
| `scheme_user` | `bool or None` | Whether user permissions come from a scheme. |
| `scheme_admin` | `bool or None` | Whether admin permissions come from a scheme. |
| `explicit_roles` | `str or None` | Explicit roles when Mattermost returns them. |

Additional return types:

| SDK method | Return type | Notes |
| --- | --- | --- |
| `delete(...)`, `archive(...)`, `remove_member(...)`, `leave(...)` | `StatusOK` | Contains a `status` field. |
| `stats(channel_id)` | `ChannelStats` | Fields: `channel_id`, `member_count`. |
| `unread(user_id, channel_id)` | `ChannelUnread` | Fields: `team_id`, `channel_id`, `msg_count`, `mention_count`, `last_viewed_at`. |
| `pinned_posts(channel_id)` | `PostList` | Uses `order` plus `posts` keyed by post ID. |

## Examples

```python
from matteraio import MattermostClient


async def main() -> None:
    async with MattermostClient(
        base_url="https://mattermost.example.com",
        token="YOUR_BOT_TOKEN",
    ) as client:
        team = await client.teams.get_by_name("engineering")

        channel = await client.channels.create(
            team_id=team.id,
            name="deployments",
            display_name="Deployments",
            type="O",
            purpose="Release and deploy coordination",
        )
        same_channel = await client.channels.get_by_name(team.id, "deployments")
        channels = await client.channels.list(team.id, page=0, per_page=20)
        channel_names = [
            channel.name async for channel in client.channels.iter_all(team.id, per_page=100)
        ]

        member = await client.channels.add_member(channel.id, "user-id")
        stats = await client.channels.stats(channel.id)
        unread = await client.channels.unread(member.user_id, channel.id)
        pinned = await client.channels.pinned_posts(same_channel.id)

        print(len(channels), channel_names, stats.member_count, unread.mention_count, pinned.order)
```

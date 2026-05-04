# Posts

[Endpoint reference](../endpoints.md)

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.posts.get(post_id, ...)` | `GET /posts/{post_id}` | Get a post by ID. |
| `client.posts.create(...)` | `POST /posts` | Create a post in a channel. Use `root_id` for thread replies and `file_ids` for uploaded files. |
| `client.posts.update(post_id, ...)` | `PUT /posts/{post_id}` | Replace the editable post body. |
| `client.posts.patch(post_id, ...)` | `PUT /posts/{post_id}/patch` | Patch provided post fields. |
| `client.posts.delete(post_id)` | `DELETE /posts/{post_id}` | Soft-delete a post. |
| `client.posts.thread(post_id, ...)` | `GET /posts/{post_id}/thread` | Get a post thread. |
| `client.posts.list(channel_id, ...)` | `GET /channels/{channel_id}/posts` | Get channel post history. |
| `client.posts.iter_channel(channel_id, ...)` | `GET /channels/{channel_id}/posts` | Iterate channel posts across pages. |
| `client.posts.search(team_id, terms, ...)` | `POST /teams/{team_id}/posts/search` | Search team posts using Mattermost search syntax. |
| `client.posts.pin(post_id)` | `POST /posts/{post_id}/pin` | Pin a post to its channel. |
| `client.posts.unpin(post_id)` | `POST /posts/{post_id}/unpin` | Unpin a post from its channel. |
| `client.posts.get_by_ids(post_ids)` | `POST /posts/ids` | Fetch posts by a batch of post IDs. |
| `client.posts.files_info(post_id, ...)` | `GET /posts/{post_id}/files/info` | Get file metadata attached to a post. |

## Returned Data

Post lookup, create, update, patch, and batch lookup methods return `Post` or `list[Post]`.

| Field | Type | Description |
| --- | --- | --- |
| `id` | `str` | Mattermost post ID. |
| `channel_id` | `str` | Channel containing the post. |
| `message` | `str` | Markdown message body. |
| `user_id` | `str or None` | Author user ID when returned by Mattermost. |
| `root_id` | `str or None` | Root post ID for thread replies. |
| `file_ids` | `list[str]` | Attached file IDs. |
| `create_at` | `int or None` | Creation timestamp in milliseconds. |
| `update_at` | `int or None` | Last update timestamp in milliseconds. |
| `delete_at` | `int or None` | Deletion timestamp in milliseconds. |
| `is_pinned` | `bool or None` | Whether the post is pinned. |
| `has_reactions` | `bool or None` | Whether the post has reactions. |

`thread(...)`, `list(...)`, and channel pinned posts return `PostList`.

| Field | Type | Description |
| --- | --- | --- |
| `order` | `list[str]` | Post IDs in display order. |
| `posts` | `dict[str, Post]` | Posts keyed by post ID. |
| `next_post_id` | `str or None` | Pagination pointer to the next post. |
| `prev_post_id` | `str or None` | Pagination pointer to the previous post. |
| `has_next` | `bool or None` | Whether more posts are available. |

`search(...)` returns `PostSearchResponse`, which has all `PostList` fields plus a `matches`
field of type `dict[str, list[str]]`. `files_info(...)` returns `list[FileInfo]`.
`delete(...)`, `pin(...)`, and `unpin(...)` return `StatusOK` with a `status` field.

## Examples

```python
from matteraio import MattermostClient


async def main() -> None:
    async with MattermostClient(
        base_url="https://mattermost.example.com",
        token="YOUR_BOT_TOKEN",
    ) as client:
        team = await client.teams.get_by_name("engineering")
        channel = await client.channels.get_by_name(team.id, "town-square")

        post = await client.posts.create(
            channel_id=channel.id,
            message="Deploy finished.",
        )
        reply = await client.posts.create(
            channel_id=channel.id,
            root_id=post.id,
            message="Smoke tests passed.",
        )

        history = await client.posts.list(channel.id, page=0, per_page=20)
        messages = [post.message async for post in client.posts.iter_channel(channel.id)]
        thread = await client.posts.thread(post.id, per_page=20)
        search = await client.posts.search(team.id, "deploy", per_page=10)
        fetched = await client.posts.get_by_ids([post.id, reply.id])

        await client.posts.pin(post.id)

        print(history.order, messages, thread.posts[post.id].message, search.matches, len(fetched))
```

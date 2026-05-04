# Reactions

[Endpoint reference](../endpoints.md)

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.reactions.add(...)` | `POST /reactions` | Add a reaction to a post. |
| `client.reactions.remove(user_id, post_id, emoji_name)` | `DELETE /users/{user_id}/posts/{post_id}/reactions/{emoji_name}` | Remove one user's reaction. |
| `client.reactions.list(post_id)` | `GET /posts/{post_id}/reactions` | List reactions for a post. |

## Returned Data

`add(...)` returns `Reaction`; `list(post_id)` returns `list[Reaction]`.

| Field | Type | Description |
| --- | --- | --- |
| `user_id` | `str` | User who reacted. |
| `post_id` | `str` | Reacted post. |
| `emoji_name` | `str` | Mattermost emoji name without surrounding colons. |
| `create_at` | `int or None` | Creation timestamp in milliseconds. |

`remove(...)` returns `StatusOK` with a `status` field.

## Examples

```python
from matteraio import MattermostClient


async def main() -> None:
    async with MattermostClient(
        base_url="https://mattermost.example.com",
        token="YOUR_BOT_TOKEN",
    ) as client:
        me = await client.users.me()
        reaction = await client.reactions.add(
            user_id=me.id,
            post_id="post-id",
            emoji_name="white_check_mark",
        )
        reactions = await client.reactions.list(reaction.post_id)
        await client.reactions.remove(me.id, reaction.post_id, reaction.emoji_name)

        print([item.emoji_name for item in reactions])
```

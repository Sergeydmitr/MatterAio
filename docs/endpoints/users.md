# Users and Auth

[Endpoint reference](../endpoints.md)

| SDK method | Mattermost endpoint | Description |
| --- | --- | --- |
| `client.users.login(...)` | `POST /users/login` | Log in with email, username, or LDAP ID. Stores the returned session token when the client was created without a token. |
| `client.users.me()` | `GET /users/me` | Get the authenticated user. |
| `client.users.get(user_id)` | `GET /users/{user_id}` | Get a user by ID. Mattermost also accepts `me`. |
| `client.users.get_by_username(username)` | `GET /users/username/{username}` | Get a user by username. |
| `client.users.get_by_email(email)` | `GET /users/email/{email}` | Get a user by email address. |
| `client.users.search(term, ...)` | `POST /users/search` | Search users by name, username, nickname, or email with optional team/channel filters. |

## Returned Data

`client.users.login(...)` returns `LoginResponse`:

| Field | Type | Description |
| --- | --- | --- |
| `user` | `User` | Authenticated user returned by Mattermost. |
| `token` | `str` | Session token from the Mattermost `Token` response header. The client stores it for later requests. |

User lookup methods return `User`; `client.users.search(...)` returns `list[User]`.

| Field | Type | Description |
| --- | --- | --- |
| `id` | `str` | Mattermost user ID. |
| `username` | `str` | Mattermost username. |
| `email` | `str or None` | Email address when the server includes it. |

## Examples

```python
from matteraio import MattermostClient


async def main() -> None:
    async with MattermostClient(base_url="https://mattermost.example.com") as client:
        login = await client.users.login(
            login_id="bot@example.com",
            password="correct-horse-battery-staple",
        )
        print(login.user.id, login.token)

        me = await client.users.me()
        user = await client.users.get_by_username("alice")
        matches = await client.users.search("ali", team_id="team-id", limit=10)

        print(me.username, user.email, [item.username for item in matches])
```

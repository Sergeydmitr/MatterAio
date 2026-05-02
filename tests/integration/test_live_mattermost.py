from __future__ import annotations

from collections.abc import Callable
from time import monotonic

import pytest

from matteraio import (
    MattermostClient,
    MattermostWebSocketClient,
    PostedEvent,
    TypedWebSocketEvent,
    WebSocketMessage,
)

pytestmark = pytest.mark.integration


async def receive_until(
    client: MattermostWebSocketClient,
    predicate: Callable[[TypedWebSocketEvent | WebSocketMessage], bool],
    *,
    timeout: float = 30.0,
) -> TypedWebSocketEvent | WebSocketMessage:
    deadline = monotonic() + timeout

    while True:
        remaining = deadline - monotonic()
        if remaining <= 0:
            pytest.fail("Timed out waiting for a matching Mattermost WebSocket message.")

        message = await client.receive_event(timeout=min(5.0, remaining))
        if predicate(message):
            return message


async def test_rest_resources_work_against_live_server(
    integration_workspace: dict[str, str],
) -> None:
    async with MattermostClient(
        base_url=integration_workspace["base_url"],
        token=integration_workspace["token"],
    ) as client:
        team = await client.teams.get(integration_workspace["team_id"])
        assert team.name == integration_workspace["team_name"]

        named_team = await client.teams.get_by_name(integration_workspace["team_name"])
        assert named_team.id == integration_workspace["team_id"]

        me = await client.users.me()
        assert me.username == integration_workspace["username"]

        channel = await client.channels.get(integration_workspace["channel_id"])
        assert channel.id == integration_workspace["channel_id"]

        named_channel = await client.channels.get_by_name(
            integration_workspace["team_id"],
            integration_workspace["channel_name"],
        )
        assert named_channel.id == integration_workspace["channel_id"]

        channels = await client.channels.list(integration_workspace["team_id"])
        assert any(item.id == integration_workspace["channel_id"] for item in channels)

        created_channel = await client.channels.create(
            team_id=integration_workspace["team_id"],
            name=f"{integration_workspace['channel_name']}-extra",
            display_name="MatterAio Extra",
        )
        assert created_channel.team_id == integration_workspace["team_id"]

        upload = await client.files.upload(
            channel_id=integration_workspace["channel_id"],
            filename="integration.txt",
            content=b"live integration payload",
            content_type="text/plain",
        )
        assert len(upload.file_infos) == 1

        file_info = upload.file_infos[0]
        assert file_info.name == "integration.txt"

        fetched_file_info = await client.files.info(file_info.id)
        assert fetched_file_info.name == "integration.txt"

        file_content = await client.files.download(file_info.id)
        assert file_content == b"live integration payload"

        post = await client.posts.create(
            channel_id=integration_workspace["channel_id"],
            message="MatterAio live integration post",
            file_ids=[file_info.id],
        )
        assert post.channel_id == integration_workspace["channel_id"]
        assert post.message == "MatterAio live integration post"
        assert post.file_ids == [file_info.id]

        fetched_post = await client.posts.get(post.id)
        assert fetched_post.id == post.id
        assert fetched_post.message == post.message


async def test_websocket_receives_posted_event_from_live_server(
    integration_workspace: dict[str, str],
) -> None:
    async with MattermostClient(
        base_url=integration_workspace["base_url"],
        token=integration_workspace["token"],
    ) as rest_client:
        websocket = MattermostWebSocketClient(
            base_url=integration_workspace["base_url"],
            token=integration_workspace["token"],
        )
        await websocket.connect()

        try:
            seq = await websocket.authenticate()
            reply = await receive_until(
                websocket,
                lambda message: (
                    isinstance(message, WebSocketMessage)
                    and message.is_reply
                    and message.seq_reply == seq
                ),
            )
            assert isinstance(reply, WebSocketMessage)
            assert reply.status == "OK"

            post = await rest_client.posts.create(
                channel_id=integration_workspace["channel_id"],
                message="MatterAio websocket integration post",
            )

            posted = await receive_until(
                websocket,
                lambda message: (
                    isinstance(message, PostedEvent) and message.data.post.id == post.id
                ),
            )
            assert isinstance(posted, PostedEvent)
            assert posted.data.post.message == post.message
            assert posted.broadcast is not None
            assert posted.broadcast.channel_id == integration_workspace["channel_id"]
        finally:
            await websocket.aclose()

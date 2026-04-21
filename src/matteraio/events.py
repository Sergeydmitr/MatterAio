from __future__ import annotations

from typing import Any

from pydantic import Field

from .models import MattermostModel


class WebSocketBroadcast(MattermostModel):
    omit_users: Any | None = None
    user_id: str | None = None
    channel_id: str | None = None
    team_id: str | None = None
    connection_id: str | None = None
    omit_connection_id: str | None = None


class WebSocketCommand(MattermostModel):
    seq: int
    action: str
    data: dict[str, Any] = Field(default_factory=dict)


class WebSocketMessage(MattermostModel):
    event: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    broadcast: WebSocketBroadcast | None = None
    seq: int | None = None
    status: str | None = None
    seq_reply: int | None = None

    @property
    def is_event(self) -> bool:
        return self.event is not None

    @property
    def is_reply(self) -> bool:
        return self.status is not None

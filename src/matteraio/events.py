from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import Field, field_validator

from .models import MattermostModel, Post


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

    def parse_event(self) -> TypedWebSocketEvent | WebSocketMessage:
        return parse_websocket_event(self)


class WebSocketEventBase(MattermostModel):
    event: str
    data: MattermostModel
    broadcast: WebSocketBroadcast | None = None
    seq: int | None = None


class HelloEventData(MattermostModel):
    connection_id: str
    server_version: str


class HelloEvent(WebSocketEventBase):
    event: Literal["hello"]
    data: HelloEventData


class StatusChangeEventData(MattermostModel):
    status: str
    user_id: str


class StatusChangeEvent(WebSocketEventBase):
    event: Literal["status_change"]
    data: StatusChangeEventData


class PostedEventData(MattermostModel):
    channel_display_name: str | None = None
    channel_name: str | None = None
    channel_type: str | None = None
    mentions: list[str] = Field(default_factory=list)
    post: Post
    sender_name: str | None = None
    set_online: bool | None = None
    team_id: str | None = None

    @field_validator("mentions", mode="before")
    @classmethod
    def _parse_mentions(cls, value: Any) -> Any:
        if isinstance(value, str):
            return json.loads(value)
        return value

    @field_validator("post", mode="before")
    @classmethod
    def _parse_post(cls, value: Any) -> Any:
        if isinstance(value, str):
            return json.loads(value)
        return value


class PostedEvent(WebSocketEventBase):
    event: Literal["posted"]
    data: PostedEventData


type TypedWebSocketEvent = HelloEvent | PostedEvent | StatusChangeEvent


def parse_websocket_event(message: WebSocketMessage) -> TypedWebSocketEvent | WebSocketMessage:
    if not message.is_event or message.event is None:
        return message

    parser = _EVENT_PARSERS.get(message.event)
    if parser is None:
        return message

    return parser.model_validate(message.model_dump())


_EVENT_PARSERS: dict[str, type[TypedWebSocketEvent]] = {
    "hello": HelloEvent,
    "posted": PostedEvent,
    "status_change": StatusChangeEvent,
}

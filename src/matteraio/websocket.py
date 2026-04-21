from __future__ import annotations

import json
from json import JSONDecodeError
from types import TracebackType
from typing import Any

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import InvalidURI, WebSocketException

from .config import MattermostConfig
from .events import WebSocketCommand, WebSocketMessage
from .exceptions import (
    WebSocketConnectionError,
    WebSocketNotConnectedError,
    WebSocketProtocolError,
)


class MattermostWebSocketClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        open_timeout: float = 10.0,
        ping_interval: float | None = 20.0,
        ping_timeout: float | None = 20.0,
        close_timeout: float = 10.0,
        max_size: int | None = 1_048_576,
        additional_headers: dict[str, str] | None = None,
    ) -> None:
        self.config = MattermostConfig(base_url=base_url, token=token)
        self._open_timeout = open_timeout
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._close_timeout = close_timeout
        self._max_size = max_size
        self._additional_headers = additional_headers
        self._websocket: ClientConnection | None = None
        self._seq = 0

    async def __aenter__(self) -> MattermostWebSocketClient:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    @property
    def is_connected(self) -> bool:
        return self._websocket is not None

    async def connect(self) -> None:
        if self._websocket is not None:
            raise WebSocketProtocolError("WebSocket connection is already open.")

        try:
            self._websocket = await connect(
                self.config.websocket_url,
                additional_headers=self._additional_headers,
                open_timeout=self._open_timeout,
                ping_interval=self._ping_interval,
                ping_timeout=self._ping_timeout,
                close_timeout=self._close_timeout,
                max_size=self._max_size,
            )
        except (OSError, InvalidURI, WebSocketException) as exc:
            raise WebSocketConnectionError(
                "Failed to open Mattermost WebSocket connection."
            ) from exc

    async def aclose(self) -> None:
        if self._websocket is None:
            return

        websocket = self._websocket
        self._websocket = None
        await websocket.close()

    async def authenticate(self) -> int:
        return await self.send_command(
            "authentication_challenge",
            {"token": self.config.token},
        )

    async def send_command(self, action: str, data: dict[str, Any] | None = None) -> int:
        websocket = self._require_connection()
        seq = self._next_seq()
        command = WebSocketCommand(
            seq=seq,
            action=action,
            data={} if data is None else data,
        )

        try:
            await websocket.send(command.model_dump_json())
        except WebSocketException as exc:
            raise WebSocketConnectionError("Failed to send Mattermost WebSocket command.") from exc

        return seq

    async def receive_json(self) -> dict[str, Any]:
        websocket = self._require_connection()

        try:
            payload = await websocket.recv()
        except WebSocketException as exc:
            raise WebSocketConnectionError(
                "Failed to receive Mattermost WebSocket message."
            ) from exc

        if not isinstance(payload, str):
            raise WebSocketProtocolError("Mattermost WebSocket returned a binary frame.")

        try:
            decoded = json.loads(payload)
        except JSONDecodeError as exc:
            raise WebSocketProtocolError("Mattermost WebSocket returned invalid JSON.") from exc

        if not isinstance(decoded, dict):
            raise WebSocketProtocolError("Mattermost WebSocket returned a non-object payload.")

        return decoded

    async def receive_message(self) -> WebSocketMessage:
        return WebSocketMessage.model_validate(await self.receive_json())

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _require_connection(self) -> ClientConnection:
        if self._websocket is None:
            raise WebSocketNotConnectedError("WebSocket connection is not open.")
        return self._websocket

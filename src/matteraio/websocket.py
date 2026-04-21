from __future__ import annotations

import asyncio
import json
from json import JSONDecodeError
from types import TracebackType
from typing import Any, NoReturn

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed, InvalidURI, WebSocketException

from .config import MattermostConfig
from .events import WebSocketCommand, WebSocketMessage
from .exceptions import (
    WebSocketConnectionError,
    WebSocketDisconnectedError,
    WebSocketNotConnectedError,
    WebSocketProtocolError,
    WebSocketTimeoutError,
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
        reconnect_initial_delay: float = 1.0,
        reconnect_max_delay: float = 16.0,
        reconnect_max_attempts: int | None = None,
        additional_headers: dict[str, str] | None = None,
    ) -> None:
        self.config = MattermostConfig(base_url=base_url, token=token)
        self._open_timeout = open_timeout
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._close_timeout = close_timeout
        self._max_size = max_size
        self._reconnect_initial_delay = reconnect_initial_delay
        self._reconnect_max_delay = reconnect_max_delay
        self._reconnect_max_attempts = reconnect_max_attempts
        self._additional_headers = additional_headers
        self._websocket: ClientConnection | None = None
        self._seq = 0
        self._restore_authentication = False
        self._last_close_code: int | None = None
        self._last_close_reason: str | None = None

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
        return self._websocket is not None and self._websocket.close_code is None

    @property
    def close_code(self) -> int | None:
        if self._websocket is not None and self._websocket.close_code is not None:
            return self._websocket.close_code
        return self._last_close_code

    @property
    def close_reason(self) -> str | None:
        if self._websocket is not None and self._websocket.close_reason is not None:
            return self._websocket.close_reason
        return self._last_close_reason

    async def connect(self) -> None:
        if self.is_connected:
            raise WebSocketProtocolError("WebSocket connection is already open.")

        self._websocket = None
        await self._connect_once()

    async def reconnect(self) -> None:
        await self.aclose()

        attempt = 0
        delay = self._reconnect_initial_delay
        while True:
            attempt += 1
            try:
                await self._connect_once()
                break
            except WebSocketConnectionError:
                if (
                    self._reconnect_max_attempts is not None
                    and attempt >= self._reconnect_max_attempts
                ):
                    raise
                await asyncio.sleep(delay)
                delay = min(self._reconnect_max_delay, delay * 2)

        if self._restore_authentication:
            await self.authenticate()

    async def aclose(self, code: int = 1000, reason: str = "") -> None:
        if self._websocket is None:
            return

        websocket = self._websocket
        self._websocket = None
        await websocket.close(code=code, reason=reason)
        self._store_close_details(
            websocket.close_code if websocket.close_code is not None else code,
            websocket.close_reason or reason or None,
        )

    async def authenticate(self) -> int:
        seq = await self.send_command(
            "authentication_challenge",
            {"token": self.config.token},
        )
        self._restore_authentication = True
        return seq

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
        except ConnectionClosed as exc:
            self._raise_disconnected("send Mattermost WebSocket command", exc)
        except WebSocketException as exc:
            raise WebSocketConnectionError("Failed to send Mattermost WebSocket command.") from exc

        return seq

    async def ping(self, data: str | bytes | bytearray | memoryview | None = None) -> float:
        websocket = self._require_connection()

        try:
            pong_waiter = await websocket.ping(data)
            return await pong_waiter
        except ConnectionClosed as exc:
            self._raise_disconnected("ping Mattermost WebSocket", exc)
        except WebSocketException as exc:
            raise WebSocketConnectionError("Failed to ping Mattermost WebSocket.") from exc

    async def receive_json(self, *, timeout: float | None = None) -> dict[str, Any]:
        websocket = self._require_connection()

        try:
            if timeout is None:
                payload = await websocket.recv()
            else:
                async with asyncio.timeout(timeout):
                    payload = await websocket.recv()
        except TimeoutError as exc:
            raise WebSocketTimeoutError(
                "Timed out waiting for a Mattermost WebSocket message."
            ) from exc
        except ConnectionClosed as exc:
            self._raise_disconnected("receive Mattermost WebSocket message", exc)
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

    async def receive_message(self, *, timeout: float | None = None) -> WebSocketMessage:
        return WebSocketMessage.model_validate(await self.receive_json(timeout=timeout))

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _require_connection(self) -> ClientConnection:
        if self._websocket is None:
            raise WebSocketNotConnectedError("WebSocket connection is not open.")

        if self._websocket.close_code is not None:
            close_code = self._websocket.close_code
            close_reason = self._websocket.close_reason
            self._websocket = None
            self._store_close_details(close_code, close_reason)
            raise WebSocketDisconnectedError(
                "Mattermost WebSocket connection is closed.",
                close_code=close_code,
                close_reason=close_reason,
            )

        return self._websocket

    async def _connect_once(self) -> None:
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

        self._store_close_details(None, None)

    def _raise_disconnected(self, action: str, exc: ConnectionClosed) -> NoReturn:
        close_frame = exc.rcvd or exc.sent
        close_code = close_frame.code if close_frame is not None else None
        close_reason = close_frame.reason if close_frame is not None else None
        self._websocket = None
        self._store_close_details(close_code, close_reason)
        raise WebSocketDisconnectedError(
            f"Mattermost WebSocket closed while attempting to {action}.",
            close_code=close_code,
            close_reason=close_reason,
        ) from exc

    def _store_close_details(self, close_code: int | None, close_reason: str | None) -> None:
        self._last_close_code = close_code
        self._last_close_reason = close_reason

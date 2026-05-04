from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from inspect import isawaitable
from typing import TYPE_CHECKING, TypeAlias, TypeVar, cast

from .events import TypedWebSocketEvent, WebSocketEventBase, WebSocketMessage

if TYPE_CHECKING:
    from .websocket import MattermostWebSocketClient


WebSocketHandlerEvent: TypeAlias = TypedWebSocketEvent | WebSocketMessage
EventSelector: TypeAlias = str | type[WebSocketEventBase] | type[WebSocketMessage] | None
EventFilter: TypeAlias = Callable[[WebSocketHandlerEvent], bool | Awaitable[bool]]
EventCallback: TypeAlias = Callable[[WebSocketHandlerEvent], Awaitable[None]]
HandlerFuncT = TypeVar("HandlerFuncT", bound=Callable[..., Awaitable[None]])


@dataclass(frozen=True)
class EventHandler:
    selector: EventSelector
    callback: EventCallback
    filters: tuple[EventFilter, ...] = ()

    async def matches(self, event: WebSocketHandlerEvent) -> bool:
        if not self._selector_matches(event):
            return False

        for event_filter in self.filters:
            matched = event_filter(event)
            if isawaitable(matched):
                matched = await matched
            if not matched:
                return False

        return True

    async def call(self, event: WebSocketHandlerEvent) -> None:
        result = self.callback(event)
        if not isawaitable(result):
            raise TypeError("Mattermost event handlers must be async callables.")
        await result

    def _selector_matches(self, event: WebSocketHandlerEvent) -> bool:
        if self.selector is None:
            return True
        if isinstance(self.selector, str):
            return event.event == self.selector
        return isinstance(event, self.selector)


class MattermostEventRouter:
    def __init__(self, *, name: str | None = None) -> None:
        self.name = name
        self._handlers: list[EventHandler] = []
        self._routers: list[MattermostEventRouter] = []

    @property
    def handlers(self) -> tuple[EventHandler, ...]:
        return tuple(self._handlers)

    @property
    def routers(self) -> tuple[MattermostEventRouter, ...]:
        return tuple(self._routers)

    def on(
        self,
        selector: EventSelector = None,
        *filters: EventFilter,
    ) -> Callable[[HandlerFuncT], HandlerFuncT]:
        def decorator(callback: HandlerFuncT) -> HandlerFuncT:
            self.register(callback, selector=selector, filters=filters)
            return callback

        return decorator

    def event(
        self,
        selector: EventSelector = None,
        *filters: EventFilter,
    ) -> Callable[[HandlerFuncT], HandlerFuncT]:
        return self.on(selector, *filters)

    def register(
        self,
        callback: HandlerFuncT,
        *,
        selector: EventSelector = None,
        filters: Iterable[EventFilter] = (),
    ) -> HandlerFuncT:
        self._handlers.append(
            EventHandler(
                selector=selector,
                callback=cast(EventCallback, callback),
                filters=tuple(filters),
            )
        )
        return callback

    def include_router(self, router: MattermostEventRouter) -> MattermostEventRouter:
        if router is self:
            raise ValueError("A Mattermost event router cannot include itself.")
        self._routers.append(router)
        return router

    def include_routers(self, *routers: MattermostEventRouter) -> None:
        for router in routers:
            self.include_router(router)

    async def dispatch(self, event: WebSocketHandlerEvent) -> int:
        handled = 0

        for handler in self._handlers:
            if await handler.matches(event):
                await handler.call(event)
                handled += 1

        for router in self._routers:
            handled += await router.dispatch(event)

        return handled


class MattermostEventDispatcher(MattermostEventRouter):
    async def feed_event(self, event: WebSocketHandlerEvent) -> int:
        return await self.dispatch(event)

    async def dispatch_next(
        self,
        client: MattermostWebSocketClient,
        *,
        timeout: float | None = None,
    ) -> int:
        event = await client.receive_event(timeout=timeout)
        return await self.dispatch(event)

    async def start(
        self,
        client: MattermostWebSocketClient,
        *,
        authenticate: bool = True,
        timeout: float | None = None,
    ) -> None:
        if not client.is_connected:
            await client.connect()
        if authenticate:
            await client.authenticate()

        while True:
            await self.dispatch_next(client, timeout=timeout)

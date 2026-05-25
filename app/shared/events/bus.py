from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, Type, TypeVar

from app.shared.events.base import DomainEvent

logger = logging.getLogger(__name__)

E = TypeVar("E", bound=DomainEvent)

EventHandler = Callable[[E], Awaitable[None]]
"""Generic handler alias. `EventHandler[UserRegistered]` is the type a
handler subscribed to `UserRegistered` must satisfy."""


class EventBus(Protocol):
    """Port for in-process dispatch from event-type to subscribed handlers.

    `subscribe` is generic in the event type so callers get a type error if
    they wire a handler that doesn't accept the event class they passed.
    """

    def subscribe(self, event_cls: Type[E], handler: EventHandler[E]) -> None: ...

    async def dispatch(self, event: DomainEvent) -> "DispatchResult": ...


class DispatchResult:
    __slots__ = ("succeeded", "errors")

    def __init__(self, succeeded: int, errors: list[BaseException]) -> None:
        self.succeeded = succeeded
        self.errors = errors

    @property
    def ok(self) -> bool:
        return not self.errors


class InProcessEventBus:
    """Synchronous-style dispatch across the current process.

    Handlers run sequentially. Each handler is awaited inside its own
    try/except so one failure doesn't poison the others; the failures are
    surfaced via DispatchResult so the relay can retry the outbox record.
    """

    def __init__(self) -> None:
        # Storage erases the per-event type parameter — the public `subscribe`
        # signature enforces the invariant; this dict is intentionally `Any`.
        self._handlers: dict[Type[DomainEvent], list[EventHandler[Any]]] = {}

    def subscribe(self, event_cls: Type[E], handler: EventHandler[E]) -> None:
        self._handlers.setdefault(event_cls, []).append(handler)

    async def dispatch(self, event: DomainEvent) -> DispatchResult:
        handlers = self._handlers.get(type(event), [])
        succeeded = 0
        errors: list[BaseException] = []
        for handler in handlers:
            try:
                await handler(event)
                succeeded += 1
            except BaseException as exc:
                logger.exception(
                    "event handler failed",
                    extra={
                        "event_type": type(event).__name__,
                        "handler": getattr(handler, "__qualname__", repr(handler)),
                    },
                )
                errors.append(exc)
        return DispatchResult(succeeded=succeeded, errors=errors)

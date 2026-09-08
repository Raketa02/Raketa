from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Type, TypeVar

from app.application.events.envelope import DeliveryContext
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)

E = TypeVar("E", bound=DomainEvent)
EventHandler = Callable[[E, DeliveryContext], Awaitable[None]]


class MissingEventHandlerError(RuntimeError):
    pass


@dataclass(frozen=True)
class DispatchResult:
    succeeded: int
    errors: tuple[Exception, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def missing_handlers(self) -> bool:
        return any(isinstance(error, MissingEventHandlerError) for error in self.errors)


class EventDispatcher:
    """Dispatches a delivered domain event to its registered application handlers."""

    def __init__(self) -> None:
        self._handlers: dict[Type[DomainEvent], list[EventHandler[Any]]] = {}

    def subscribe(self, event_cls: Type[E], handler: EventHandler[E]) -> None:
        self._handlers.setdefault(event_cls, []).append(handler)

    def copy(self) -> "EventDispatcher":
        """These subscriptions, in a dispatcher further ones do not reach back into.

        **For the handlers that cannot be registered once for the process.**
        Every subscriber was a logger until the Conversation context arrived
        (``docs/adr/0146`` §5), and a logger needs nothing per delivery; a
        subscriber that *writes* needs the session the batch will mark the outbox
        row published in, and that session exists for one tick. So the process's
        dispatcher is copied per batch and the session-bound handlers are added
        to the copy — which is what stops one tick's handlers accumulating on the
        next tick's.
        """

        twin = EventDispatcher()
        twin._handlers = {
            event_cls: list(handlers)
            for event_cls, handlers in self._handlers.items()
        }
        return twin

    async def dispatch(
        self, event: DomainEvent, context: DeliveryContext
    ) -> DispatchResult:
        handlers = self._handlers.get(type(event), [])
        if not handlers:
            return DispatchResult(
                succeeded=0,
                errors=(
                    MissingEventHandlerError(
                        f"No application handler registered for {type(event).__name__}"
                    ),
                ),
            )

        succeeded = 0
        errors: list[Exception] = []
        for handler in handlers:
            try:
                await handler(event, context)
                succeeded += 1
            except Exception as exc:
                logger.exception(
                    "event handler failed",
                    extra={
                        "event_id": str(context.event_id),
                        "event_type": type(event).__name__,
                        "handler": getattr(handler, "__qualname__", repr(handler)),
                    },
                )
                errors.append(exc)
        return DispatchResult(succeeded=succeeded, errors=tuple(errors))

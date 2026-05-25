"""Composition root for the events subsystem.

This module is the single place that knows about every domain event class
and every handler subscription. Importing it here keeps the wiring out of
the request hot-path (it runs once at startup) and gives any reviewer a
single file to read to understand what fires when.

Adding a new event:
    1. Define the dataclass in `<module>/domain/events.py`.
    2. Add it to `_EVENTS` below so the registry knows its name.

Adding a new subscriber:
    1. Write a handler class with `async __call__(event)`.
    2. Add a `bus.subscribe(EventClass, handler)` line below.
"""
from __future__ import annotations

from app.modules.auth.application.handlers import (
    LogRefreshTokenIssued,
    LogRefreshTokenRevoked,
    LogRefreshTokenRotated,
)
from app.modules.auth.domain.events import (
    RefreshTokenIssued,
    RefreshTokenRevoked,
    RefreshTokenRotated,
)
from app.modules.users.application.handlers import LogUserRegistered
from app.modules.users.domain.events import UserRegistered
from app.shared.events import EventBus, EventRegistry

_EVENTS = (
    UserRegistered,
    RefreshTokenIssued,
    RefreshTokenRevoked,
    RefreshTokenRotated,
)


def build_event_registry() -> EventRegistry:
    registry = EventRegistry()
    for event_cls in _EVENTS:
        registry.register(event_cls)
    return registry


def register_handlers(bus: EventBus) -> None:
    bus.subscribe(UserRegistered, LogUserRegistered())
    bus.subscribe(RefreshTokenIssued, LogRefreshTokenIssued())
    bus.subscribe(RefreshTokenRevoked, LogRefreshTokenRevoked())
    bus.subscribe(RefreshTokenRotated, LogRefreshTokenRotated())

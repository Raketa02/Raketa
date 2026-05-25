from __future__ import annotations

import json
import typing
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Type
from uuid import UUID

from app.shared.events.base import DomainEvent


class EventRegistry:
    """Maps an event class to a stable string name and back.

    Why a registry instead of `type(event).__name__`: events get persisted to
    the outbox table and possibly to message brokers. Names must stay stable
    even if a class is moved or renamed, so we register an explicit mapping.
    """

    def __init__(self) -> None:
        self._name_to_cls: dict[str, Type[DomainEvent]] = {}
        self._cls_to_name: dict[Type[DomainEvent], str] = {}

    def register(
        self, event_cls: Type[DomainEvent], *, name: str | None = None
    ) -> None:
        canonical = name or event_cls.__name__
        if (
            canonical in self._name_to_cls
            and self._name_to_cls[canonical] is not event_cls
        ):
            raise ValueError(f"Event name '{canonical}' is already registered")
        self._name_to_cls[canonical] = event_cls
        self._cls_to_name[event_cls] = canonical

    def name_for(self, event_cls: Type[DomainEvent]) -> str:
        try:
            return self._cls_to_name[event_cls]
        except KeyError as exc:
            raise LookupError(
                f"Event class {event_cls!r} is not registered. Register it at startup."
            ) from exc

    def class_for(self, name: str) -> Type[DomainEvent]:
        try:
            return self._name_to_cls[name]
        except KeyError as exc:
            raise LookupError(
                f"No event class registered under name '{name}'."
            ) from exc

    def serialize(self, event: DomainEvent) -> dict[str, Any]:
        if not is_dataclass(event):
            raise TypeError(
                f"Only dataclass-based events are supported, got {type(event).__name__}"
            )
        # `asdict` keeps UUID/datetime as Python objects, but the JSON column
        # needs primitives. Round-trip through our encoder so the payload is
        # storage-ready (string UUIDs, ISO datetimes) regardless of dialect.
        return json.loads(dumps(asdict(event)))

    def deserialize(self, name: str, payload: dict[str, Any]) -> DomainEvent:
        event_cls = self.class_for(name)
        return event_cls(**_coerce_payload(event_cls, payload))


def dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, cls=_DomainEventJSONEncoder, separators=(",", ":"))


def loads(raw: str) -> dict[str, Any]:
    return json.loads(raw)


class _DomainEventJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            if obj.tzinfo is None:
                obj = obj.replace(tzinfo=timezone.utc)
            return obj.isoformat()
        return super().default(obj)


@lru_cache(maxsize=None)
def _resolve_hints(event_cls: Type[DomainEvent]) -> dict[str, Any]:
    """Resolve type hints once per event class. Required because callers may
    use `from __future__ import annotations`, which turns `__annotations__`
    into strings; `get_type_hints` resolves them to real types."""
    try:
        return typing.get_type_hints(event_cls)
    except Exception:
        return getattr(event_cls, "__annotations__", {})


def _coerce_payload(
    event_cls: Type[DomainEvent], payload: dict[str, Any]
) -> dict[str, Any]:
    """Re-hydrate UUID and datetime fields from their JSON-safe representations."""
    hints = _resolve_hints(event_cls)
    coerced: dict[str, Any] = {}
    for key, value in payload.items():
        hint = hints.get(key)
        coerced[key] = _coerce_value(hint, value)
    return coerced


def _coerce_value(hint: Any, value: Any) -> Any:
    if value is None:
        return None
    if hint is UUID and isinstance(value, str):
        return UUID(value)
    if hint is datetime and isinstance(value, str):
        return datetime.fromisoformat(value)
    return value

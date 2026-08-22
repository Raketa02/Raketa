from __future__ import annotations

import json
import types
import typing
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Type
from uuid import UUID

from app.application.events.catalog import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.application.ports.events import EncodedEvent, EventDecodingError
from app.shared.domain import DomainEvent


class JsonEventCodec:
    """JSON persistence adapter for registered, versioned domain-event contracts."""

    def __init__(self, catalog: EventCatalog) -> None:
        self._catalog = catalog

    def encode(self, event: DomainEvent) -> EncodedEvent:
        if not is_dataclass(event):
            raise TypeError(
                f"Only dataclass-based events are supported, got {type(event).__name__}"
            )
        contract = self._catalog.contract_for(type(event))
        return EncodedEvent(
            event_type=contract.name,
            schema_version=contract.version,
            payload=json.loads(_dumps(asdict(event))),
        )

    def decode(self, envelope: SerializedEventEnvelope) -> DomainEvent:
        try:
            event_cls = self._catalog.class_for(
                envelope.event_type, envelope.schema_version
            )
            return event_cls(**_coerce_payload(event_cls, envelope.payload))
        except Exception as exc:
            raise EventDecodingError(str(exc)) from exc


def _dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, cls=_DomainEventJSONEncoder, separators=(",", ":"))


class _DomainEventJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            if obj.tzinfo is None:
                obj = obj.replace(tzinfo=timezone.utc)
            return obj.isoformat()
        return super().default(obj)


def _target_type(hint: Any) -> Any:
    """The concrete type a field coerces to, looking through ``X | None``.

    Without this, an **optional** UUID decodes as the string it was stored as —
    `hint is UUID` is false for `UUID | None`, so the coercion below simply does
    not fire. Nothing raises: the event reconstructs, and the field compares
    unequal to the value it was written from, so a replayed aggregate quietly
    disagrees with the one that wrote it. Money's movements are the first events
    in the tree with an optional id on them, and they found it (#69).

    Only a union of exactly one type with ``None`` resolves. A genuine union of
    two concrete types has no single answer, and guessing one would be a worse
    failure than not coercing.
    """

    origin = typing.get_origin(hint)
    if origin is typing.Union or origin is types.UnionType:
        concrete = [arg for arg in typing.get_args(hint) if arg is not type(None)]
        return concrete[0] if len(concrete) == 1 else None
    return hint


@lru_cache(maxsize=None)
def _resolve_hints(event_cls: Type[DomainEvent]) -> dict[str, Any]:
    try:
        return typing.get_type_hints(event_cls)
    except Exception:
        return getattr(event_cls, "__annotations__", {})


def _coerce_payload(
    event_cls: Type[DomainEvent], payload: dict[str, Any]
) -> dict[str, Any]:
    hints = _resolve_hints(event_cls)
    coerced: dict[str, Any] = {}
    for key, value in payload.items():
        hint = _target_type(hints.get(key))
        if value is not None and hint is UUID and isinstance(value, str):
            value = UUID(value)
        elif value is not None and hint is datetime and isinstance(value, str):
            value = datetime.fromisoformat(value)
        coerced[key] = value
    return coerced

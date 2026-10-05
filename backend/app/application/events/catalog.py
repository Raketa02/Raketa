from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from app.shared.domain import DomainEvent


@dataclass(frozen=True)
class EventContract:
    name: str
    version: int
    event_cls: Type[DomainEvent]


class EventCatalog:
    """Durable event-contract mapping independent of Python class names."""

    def __init__(self) -> None:
        self._by_name_version: dict[tuple[str, int], EventContract] = {}
        self._by_class: dict[Type[DomainEvent], EventContract] = {}

    def register(
        self,
        event_cls: Type[DomainEvent],
        *,
        name: str,
        version: int = 1,
    ) -> None:
        if not name:
            raise ValueError("Event contract name must not be empty")
        if version < 1:
            raise ValueError("Event contract version must be positive")

        contract = EventContract(name=name, version=version, event_cls=event_cls)
        key = (name, version)
        existing_for_name = self._by_name_version.get(key)
        if (
            existing_for_name is not None
            and existing_for_name.event_cls is not event_cls
        ):
            raise ValueError(f"Event contract '{name}' version {version} is registered")
        existing_for_class = self._by_class.get(event_cls)
        if existing_for_class is not None and existing_for_class != contract:
            raise ValueError(
                f"Event class {event_cls!r} already has a durable contract"
            )
        self._by_name_version[key] = contract
        self._by_class[event_cls] = contract

    def contract_for(self, event_cls: Type[DomainEvent]) -> EventContract:
        try:
            return self._by_class[event_cls]
        except KeyError as exc:
            raise LookupError(f"Event class {event_cls!r} is not registered") from exc

    def registered_classes(self) -> tuple[Type[DomainEvent], ...]:
        """Every event class with a durable contract, in registration order."""

        return tuple(self._by_class)

    def class_for(self, name: str, version: int) -> Type[DomainEvent]:
        try:
            return self._by_name_version[(name, version)].event_cls
        except KeyError as exc:
            raise LookupError(
                f"No event contract registered for '{name}' version {version}"
            ) from exc

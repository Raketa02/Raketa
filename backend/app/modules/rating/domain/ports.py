"""The rating context's ports.

An **aggregate repository** is how a use case reaches an event-sourced aggregate
without knowing that it is event-sourced. It owns the aggregate-type name, the
replay, the ownership scoping and the optimistic-concurrency bookkeeping, so a
use case reads as domain steps — load, decide, save — and can be unit-tested
against a fake event store rather than a running database.

This is not the *read-model* kind of repository. See ``backend/CONTEXT.md`` for
the distinction, and ADR-0017 for why this context is event-sourced.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Sport
from app.modules.rating.domain.assessment import Assessment


@runtime_checkable
class AssessmentRepository(Protocol):
    """Loads and saves Assessment aggregates.

    ``save`` appends and publishes; it does **not** commit. The transaction stays
    a use-case dependency because completing an assessment writes two streams in
    one transaction, and ADR-0017 states that as a domain rule rather than a
    persistence detail.
    """

    async def load(self, assessment_id: UUID, *, for_player: UUID) -> Assessment:
        """The player's assessment, replayed from its stream.

        ``for_player`` is required so that forgetting the ownership check is a
        type error rather than one player reading another's transcript. An
        assessment that does not exist and one belonging to another player raise
        the same error, so the API cannot be used to discover which ids exist.
        """
        ...

    async def save(self, assessment: Assessment) -> None:
        """Append the aggregate's pending events and publish them.

        A no-op when nothing is pending, which is what keeps abandoning an
        already-abandoned run idempotent without the caller checking first.
        """
        ...

    async def find_open(
        self, *, player_id: UUID, sport: Sport
    ) -> Assessment | None: ...

    async def find_all_open(self, *, player_id: UUID) -> list[Assessment]: ...

"""The Clubs context's port.

One repository, and it is the **record** kind rather than the aggregate-over-an-
event-store kind the rating context has: a club is loaded as rows and saved as
rows, and the optimistic-concurrency guard is a version column rather than a
stream version. ``backend/CONTEXT.md`` draws that distinction; ADR-0077 is why
this side of it.

``save`` does not commit. The transaction boundary stays a use-case dependency
for the same reason it does everywhere else here — and it matters more in this
context than in most, because *close the open row and open the new one* is two
statements, and a partial failure between them leaves a series with no row in
force at all. The partial unique index catches the opposite mistake and does
nothing about that one.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.value_objects import ClubName


@runtime_checkable
class ClubRepository(Protocol):
    async def get(self, club_id: UUID) -> Club | None:
        """The club and all three of its series, or nothing.

        The whole record: nine clubs with a handful of courts each, and every
        caller that wants a policy also wants the club it belongs to. A narrower
        read is an optimisation nothing has asked for yet, and it would be a
        second way to answer *what is this club's policy*.
        """
        ...

    async def get_by_name(self, name: ClubName) -> Club | None:
        """The natural key ops enters a club under — the seed's stable handle."""
        ...

    async def find_all(self) -> list[Club]:
        """Every club, by name.

        By name rather than by creation time because `created_at` is a server
        default and every club written in one transaction shares it — a tie
        breaking on a random uuid is an order that changes between runs, which
        is exactly what a seed report must not have.
        """
        ...

    async def add(self, club: Club) -> Club:
        """Insert a club that does not exist yet, with its two open rows."""
        ...

    async def save(self, club: Club) -> Club:
        """Persist the delta, refusing on a stale version.

        Raises ``ConcurrentClubModification`` when the stored version has moved
        since the club was loaded — never a silent merge, because two writers
        interleaving on a policy row would produce a version nobody authored.
        """
        ...

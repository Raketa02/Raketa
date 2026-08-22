"""The three writes that change who is on a court, and one that moves the hour.

Four small use cases in one module because they are one shape — load, ask the
aggregate, save, commit — and splitting them into four files would say they were
four different things. Each one's *rule* lives on the aggregate, where the
kernel is; what is here is the transaction.

**None of them commits anything the caller cannot join.** ``save`` publishes the
announcements into the same transaction and does not commit, so
``Raketa02/Raketa#70`` — a seat payment, the court it earns, and both outbox
rows in one write — composes over these rather than around them.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.matches.application.commands import (
    MoveMatchStartCommand,
    PaySeatCommand,
    TakeSeatCommand,
    VacateSeatCommand,
)
from app.modules.matches.domain.errors import MatchNotFound
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import MatchRepository


class _MatchWrite:
    """Load, mutate, save, commit — the shape all four share."""

    def __init__(
        self, matches: MatchRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._matches = matches
        self._uow = uow
        self._clock = clock

    async def _load(self, match_id: UUID) -> Match:
        match = await self._matches.get(match_id)
        if match is None:
            raise MatchNotFound()
        return match


class MoveMatchStart(_MatchWrite):
    """Move a match. ADR-0032: *"a moved match is the same match."*"""

    async def execute(self, command: MoveMatchStartCommand) -> Match:
        match = await self._load(command.match_id)
        match.move_start(command.start, at=instant(self._clock.now()))
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored


class TakeSeat(_MatchWrite):
    """A player takes a seat: held, and owing for it."""

    async def execute(self, command: TakeSeatCommand) -> Match:
        match = await self._load(command.match_id)
        match.take_seat(command.player_id, at=instant(self._clock.now()))
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored


class PaySeat(_MatchWrite):
    """The money landed — and the match commits if that filled it past its deadline.

    Both changes are announced, and both are in one transaction: a match bound
    to four people whose commitment nobody recorded is the reassuring-direction
    failure ADR-0034's five kinds exist to remove.
    """

    async def execute(self, command: PaySeatCommand) -> Match:
        match = await self._load(command.match_id)
        match.pay_seat(command.player_id, at=instant(self._clock.now()))
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored


class VacateSeat(_MatchWrite):
    """A player leaves, and the match carries the hole.

    What she recovers is her **departure's** answer, on an axis of its own
    (ADR-0033) — ``Raketa02/Raketa#67`` writes that record beside this one, and
    it is deliberately not written here.
    """

    async def execute(self, command: VacateSeatCommand) -> Match:
        match = await self._load(command.match_id)
        match.vacate_seat(command.player_id, at=instant(self._clock.now()))
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored

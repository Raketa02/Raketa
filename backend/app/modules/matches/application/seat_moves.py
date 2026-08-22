"""The three writes that change who is on a court, and one that moves the hour.

Four small use cases in one module because they are one shape — load, ask the
aggregate, save, commit — and splitting them into four files would say they were
four different things. Each one's *rule* lives on the aggregate, where the
kernel is; what is here is the transaction.

**None of them commits anything the caller cannot join.** ``save`` publishes the
announcements into the same transaction and does not commit, so
``Raketa02/Raketa#70`` — a seat payment, the court it earns, and both outbox
rows in one write — composes over these rather than around them.

**Every one of them ends in the hold ladder, before the save and inside the same
transaction.** Three of the four move what the ladder says — a payment enters a
tier, a departure leaves one, and moving the hour moves the instant a tier lapses
— and the ladder is the only thing allowed to move ``held_since`` to match. Run
afterwards instead, or on the outbox, there is a window in which the stored
record is in the one combination the kernel refuses to read
(``resolve_court_hold.py``). ``TakeSeat`` runs it too and will almost always be
told *stand*: taking a seat is not paying for one, so it changes no count the
ladder reads — but *almost always* is not a reason for a write path to be the one
that does not ask.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.matches.application.commands import (
    DepartCommand,
    MoveMatchStartCommand,
    PaySeatCommand,
    TakeSeatCommand,
)
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.domain.errors import MatchNotFound
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import MatchRepository


class _MatchWrite:
    """Load, mutate, resolve the hold, save, commit — the shape all four share."""

    def __init__(
        self,
        matches: MatchRepository,
        holds: ResolveCourtHold,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._matches = matches
        self._holds = holds
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
        at = instant(self._clock.now())
        match.move_start(command.start, at=at)
        await self._holds.apply(match, at=at)
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored


class TakeSeat(_MatchWrite):
    """A player takes a seat: held, and owing for it."""

    async def execute(self, command: TakeSeatCommand) -> Match:
        match = await self._load(command.match_id)
        at = instant(self._clock.now())
        match.take_seat(command.player_id, at=at)
        await self._holds.apply(match, at=at)
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
        at = instant(self._clock.now())
        match.pay_seat(command.player_id, at=at)
        await self._holds.apply(match, at=at)
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored


class Depart(_MatchWrite):
    """A player leaves: one hole in the match, one departure of her own.

    Both records are written in the transaction the seat is emptied in, which is
    what stops a hole existing with nobody's money attached to it. The quote is
    checked by the aggregate, against the outcome recomputed on the record this
    load returned — so the refusal is taken on the same facts the write would
    have used, and not on a read that has since gone stale.
    """

    async def execute(self, command: DepartCommand) -> Match:
        match = await self._load(command.match_id)
        at = instant(self._clock.now())
        match.depart(command.player_id, quote=command.quote, at=at)
        await self._holds.apply(match, at=at)
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored

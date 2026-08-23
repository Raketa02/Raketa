"""The writes that change who is on a court, and one that moves the hour.

Six small use cases in one module because they are one shape — load, ask the
aggregate, save, commit — and splitting them into six files would say they were
six different things. Each one's *rule* lives on the aggregate, where the
kernel is; what is here is the transaction.

**A seat claim is one of them and not a context of its own.** It changes who may
take a seat, which is what this module is about, and it is written to the match's
own tables in the match's own transaction — ADR-0081 puts its expiry under the
match's `next_wake_at` for exactly that reason.

**None of them commits anything the caller cannot join.** ``save`` publishes the
announcements into the same transaction and does not commit, which is what lets
``money.PayForASeat`` compose over these rather than around them — a seat
payment, the court it earns and both outbox rows in one write
(``Raketa02/Raketa#70``). It reaches them through a port of Money's own rather
than by importing this module, because the fence points the other way.

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
    ClaimSeatCommand,
    DepartCommand,
    MoveMatchStartCommand,
    PaySeatCommand,
    RedeemSeatClaimCommand,
    TakeSeatCommand,
)
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.domain.errors import MatchNotFound, PlayerAlreadyClaiming
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import MatchRepository, SeatClaims


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


class ClaimSeat(_MatchWrite):
    """A player takes the five minutes in front of a seat (ADR-0081).

    **Two rules and two places they can live.** Everything about *this* match —
    the join cutoff, whether a seat is free, whether one is spoken for, whether
    thirty seconds have passed — is the aggregate's, because it is a function of
    the record. *Is she already buying a seat somewhere else* is not: no
    aggregate can see another one, so it is a narrow read through a port of its
    own, taken here, before the match is touched.

    Asked in that order deliberately. The cross-match question is one indexed
    query and the aggregate's are free, but a player who is mid-payment
    elsewhere should be told *that* rather than told this match is full — the
    first refusal she gets should be the one that explains what to do.
    """

    def __init__(
        self,
        matches: MatchRepository,
        holds: ResolveCourtHold,
        uow: UnitOfWork,
        clock: Clock,
        claims: SeatClaims,
    ) -> None:
        super().__init__(matches, holds, uow, clock)
        self._claims = claims

    async def execute(self, command: ClaimSeatCommand) -> Match:
        match = await self._load(command.match_id)
        at = instant(self._clock.now())
        if await self._claims.live_for(command.player_id, at=at) is not None:
            raise PlayerAlreadyClaiming()
        match.open_claim(command.player_id, at=at)
        await self._holds.apply(match, at=at)
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored


class RedeemSeatClaim(_MatchWrite):
    """The money landed inside the five minutes: the seat is taken **and** paid.

    One write, because a redeemed claim that left a held-and-unpaid seat behind
    would open the very window ADR-0081 exists to close. The commitment check
    rides along inside ``pay_seat``, so a match this payment fills past its own
    deadline commits in the same transaction.

    **This is the seam ``money.PayForASeat`` composes over**, not replaces: the
    court the payment earns joins *this* transaction, and the movement follows in
    one of its own — ADR-0055 refuses a movement inside a match transaction, and
    ``Raketa02/Raketa#70`` is where the two are ordered.
    """

    async def execute(self, command: RedeemSeatClaimCommand) -> Match:
        match = await self._load(command.match_id)
        at = instant(self._clock.now())
        match.redeem_claim(command.player_id, at=at)
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

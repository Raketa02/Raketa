"""``Seats`` over the Matches aggregate and the hold ladder.

The one file in Money that knows a seat is a position on a ``Match``, that a
five-minute claim is what stands in front of one, that paying may push the match
into a hold tier and earn it a court, and that the court is a ``Reservation``
Courts owns. Everything above it asks in Money's words and is told *hers* or
*gone*.

**It composes the existing writes rather than reassembling them.** ``Match``
already refuses everything that has to be refused, ``ResolveCourtHold`` is
already the only thing allowed to move ``held_since``, and ``ClaimCourt`` is
already ADR-0035's whole re-ask loop. A second implementation of any of them
here would be a second answer to a question that already has one.

**Three doors, and which one to take is a fact about the record.**

* She is **already on a paid seat** — nothing to write. That is not a defensive
  branch: it is the state a process that died between this transaction and the
  movement's leaves behind, and the state a replayed report finds. Without it a
  retry would find no live claim, read as *gone*, and refund a seat she is
  sitting on.
* She **holds a seat and has not paid** — an invited player, and the door cash
  across a counter comes through (ADR-0059). ``pay_seat``.
* She holds **neither**, so she is buying one — ``redeem_claim``, which takes
  and pays in one move and refuses by name when her five minutes are up.

**It does not commit**, and the whole ticket rests on that: ADR-0035's *"a seat
payment that earns a court, and the court it earns, are one event or they are a
bug"* is only true if the seat, the reservation and both outbox rows close
together, which is the use case's transaction to close.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Instant, MatchKind

from app.modules.courts.domain.ports import ReservationRepository
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.domain.errors import MatchNotFound, NoLiveSeatClaim
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import MatchRepository
from app.modules.money.domain.errors import PaymentNamesNoSeat
from app.modules.money.domain.funding import (
    Custody,
    SeatFunding,
    SeatIsGone,
    SeatIsHers,
)
from app.modules.money.domain.movement import SeatRef


class SeatsThroughMatches:
    """A seat bought, kept aside as a reservation, and named back to Money."""

    def __init__(
        self,
        *,
        matches: MatchRepository,
        holds: ResolveCourtHold,
        reservations: ReservationRepository,
    ) -> None:
        self._matches = matches
        self._holds = holds
        self._reservations = reservations

    async def pay_for(
        self, *, match_id: UUID, player_id: UUID, at: Instant
    ) -> SeatFunding:
        match = await self._matches.get(match_id)
        if match is None:
            raise MatchNotFound()

        seat = match.seat_of(player_id)
        if seat is not None and seat.paid:
            # Written already. See the module docstring: this is a recovery
            # path, not a guard.
            return await self._hers(match, seat.index)

        if seat is not None:
            match.pay_seat(player_id, at=at)
            index = seat.index
        else:
            try:
                index = match.redeem_claim(player_id, at=at).index
            except NoLiveSeatClaim:
                # The late bank confirmation. Nothing has been mutated: the
                # aggregate refuses before it touches the claim.
                return SeatIsGone(seat=self._seat_she_was_buying(match, player_id))

        # Before the save and in the same transaction, like every other Matches
        # write — a payment enters a tier, so this is the ask that earns the
        # court, or records that there was none to earn.
        await self._holds.apply(match, at=at)
        await self._matches.save(match)
        return await self._hers(match, index)

    async def _hers(self, match: Match, index: int) -> SeatIsHers:
        """The seat, and the two facts Money cannot derive for itself.

        **Custody comes off the match's kind and nothing else** (ADR-0056): an
        open match has bought nothing, so the money is Raketa's to hold until it
        commits; a private court is already bought, so the share passes through
        on arrival. ``PayModel`` is not read — a solo private court sells no
        seats, so there is no share for this path to be about.

        The reservation is a **query** and never a column: the match stores no
        ``reservation_id`` because the reservation already says
        ``MatchHeld(match_id)``.
        """

        reservation = await self._reservations.for_match(match.id)
        return SeatIsHers(
            seat=SeatRef(match_id=match.id, index=index),
            club_id=match.club_id,
            custody=(
                Custody.PASSED_THROUGH
                if match.kind is MatchKind.PRIVATE
                else Custody.HELD
            ),
            reservation=None if reservation is None else reservation.id,
        )

    @staticmethod
    def _seat_she_was_buying(match: Match, player_id: UUID) -> SeatRef:
        """Which seat a refund is about, once the claim on it is over.

        Her **most recently opened** claim on this match. Claims are ended and
        never removed — the cooldown is measured from the instant one closed —
        so the row is still there to read, and the newest is the one the money
        that is now landing was for.

        A payment naming a player who has never claimed or held a seat here can
        name no seat at all, and ``shareOnline`` requires one, so it is refused
        rather than filed against a guess.
        """

        hers = [claim for claim in match.claims if claim.player_id == player_id]
        if not hers:
            raise PaymentNamesNoSeat()
        newest = max(hers, key=lambda claim: (claim.claimed_at, claim.id))
        return SeatRef(match_id=match.id, index=newest.seat_index)

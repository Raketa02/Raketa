"""**The club runs its Raketa bookings** (#547; the mechanics §16.7, §16.9,
§16.14, §16.16; the screens B4, B6).

Two acts and three reads on the club surface, each for the desk's own club:

- **the day** — every booking whose game starts on a calendar day at the club,
  filtered, each with its status, its players (name, *paid*, *held*), its money
  (the court's price, what was collected, what was refunded) and the group it
  came from;
- **the free courts** — where a game may be moved: every other court of its sport
  the club still has for Raketa at its hour;
- **Move** — onto one of them; the players read the new number;
- **Cancel**, with the club's reason — **first a move by cancel** (#672; the
  mechanics §16.9, Q122): when a free court of the club's absorbs it — the
  same hour and share, the same kind or indoor for an outdoor game, indoor for
  *weather* — the game moves there and nothing else happens: every hold or
  taken share stays as it is, nobody is refunded, let go or owed a card, and
  the players are told *Game moved*. Otherwise, or *anyway*: everybody still
  in refunded **in full**, and a leaver whose open seat was still paid for;
  nothing on anybody's record; the game, its room and its court hour off; and
  **the people still in dealt the owed card first**, closest to this game
  (#673), by the proposer, which the cancel makes due (``propose_games.py``).
  **Either way the court the game was on is closed for the hour** (#673): it
  can't be played then, so it is never sold for that hour again until the
  club removes the exception;
- **the cancel's preview** — what a cancel with a reason would do now: move
  the game to a named court of a named kind, or call it off. The cancel
  decides afresh when the club confirms.

Desk check-in is removed (#651).

Move and Cancel are the club's **until the game starts**, and never on a game
called off. **Every act locks the game
first** — its proposal's row, the booking's own id — as every act on a game
does, so a club's cancel, a player's leaving and a rescue arriving together are
one after another; and each is one transaction, the money following the commit.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant, invariant
from app.modules.clubs.domain.court_hours import (
    DAY_CLOSES,
    DAY_OPENS,
    hour_start,
    local_day,
)
from app.modules.proposals.domain.club_bookings import (
    NOTHING_TAKEN,
    BookedFrom,
    CancelOutcome,
    ClubFilter,
    ClubStatus,
    CourtToMoveTo,
    Takings,
    club_status,
    shown_under,
    still_to_be_played,
)
from app.modules.proposals.domain.errors import (
    BookingIsCalledOff,
    BookingNotFound,
    CourtNotFree,
    GameHasStarted,
)
from app.modules.proposals.domain.home import (
    BookedGame,
    ClubCancelReason,
)
from app.modules.proposals.domain.ports import (
    BookingTakings,
    ClubBookings,
    PlayerBookings,
    PlayerNames,
    PoolOrigins,
    ProposalRepository,
    RefundReason,
    SeatRefunds,
    UndecidedCharges,
)


# --------------------------------------------------------------------------- #
# The day
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class ClubBookingRow:
    game: BookedGame
    status: ClubStatus
    takings: Takings
    #: The group it came from — ``None`` for a pool that is no group any more.
    booked_from: BookedFrom | None
    #: Move and Cancel are still the club's.
    still_to_be_played: bool


@final
@dataclass(frozen=True, slots=True)
class ClubDay:
    day: date
    read_at: Instant
    chosen: ClubFilter
    rows: tuple[ClubBookingRow, ...]
    #: How many of the day's bookings each filter shows — the chips' counts.
    counts: Mapping[ClubFilter, int]
    #: Each player's Name; an account that can no longer be named is absent.
    names: Mapping[UUID, str]


@final
class ReadClubBookings:
    def __init__(
        self,
        *,
        bookings: ClubBookings,
        takings: BookingTakings,
        origins: PoolOrigins,
        names: PlayerNames,
        clock: Clock,
    ) -> None:
        self._bookings = bookings
        self._takings = takings
        self._origins = origins
        self._names = names
        self._clock = clock

    async def execute(
        self, club_id: UUID, *, day: date | None, chosen: ClubFilter
    ) -> ClubDay:
        now = instant(self._clock.now())
        on = day if day is not None else local_day(now)
        games = await self._bookings.on_day(
            club_id,
            start=hour_start(on, DAY_OPENS),
            end=hour_start(on, DAY_CLOSES),
        )
        statuses = {game.booking_id: club_status(game, now=now) for game in games}
        shown = [
            game for game in games if shown_under(statuses[game.booking_id], chosen)
        ]
        takings = await self._takings.of([game.booking_id for game in shown])
        origins = await self._origins.of({game.pool_id for game in shown})
        names = await self._names.names_of(
            {player for game in shown for player in game.players}
        )
        return ClubDay(
            day=on,
            read_at=now,
            chosen=chosen,
            rows=tuple(
                ClubBookingRow(
                    game=game,
                    status=statuses[game.booking_id],
                    takings=takings.get(game.booking_id, NOTHING_TAKEN),
                    booked_from=origins.get(game.pool_id),
                    still_to_be_played=still_to_be_played(game, now=now),
                )
                for game in shown
            ),
            counts={
                one: sum(1 for status in statuses.values() if shown_under(status, one))
                for one in ClubFilter
            },
            names=names,
        )


# --------------------------------------------------------------------------- #
# Move and Cancel
# --------------------------------------------------------------------------- #


@final
class ReadFreeCourts:
    """Where the club may move a game — the Move dialog."""

    def __init__(
        self, *, bookings: PlayerBookings, club: ClubBookings, clock: Clock
    ) -> None:
        self._bookings = bookings
        self._club = club
        self._clock = clock

    async def execute(
        self, *, club_id: UUID, booking_id: UUID
    ) -> tuple[CourtToMoveTo, ...]:
        now = instant(self._clock.now())
        await _still_the_clubs_to_play(self._bookings, club_id, booking_id, now=now)
        return tuple(await self._club.free_courts(booking_id))


@final
class MoveTheGame:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        bookings: PlayerBookings,
        club: ClubBookings,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._bookings = bookings
        self._club = club
        self._uow = uow
        self._clock = clock

    async def execute(
        self, *, club_id: UUID, booking_id: UUID, court_id: UUID
    ) -> CourtToMoveTo:
        """The court the game is on now."""

        now = instant(self._clock.now())
        await self._proposals.load_for_update(booking_id)
        await _still_the_clubs_to_play(self._bookings, club_id, booking_id, now=now)
        moved = await self._club.move(booking_id, court_id, at=now)
        if moved is None:
            raise CourtNotFree()
        await self._uow.commit()
        return moved


@final
class PreviewTheCancel:
    """What a cancel with a reason would do now — the Cancel dialog (#672)."""

    def __init__(
        self, *, bookings: PlayerBookings, club: ClubBookings, clock: Clock
    ) -> None:
        self._bookings = bookings
        self._club = club
        self._clock = clock

    async def execute(
        self, *, club_id: UUID, booking_id: UUID, because: ClubCancelReason
    ) -> CancelOutcome:
        now = instant(self._clock.now())
        await _still_the_clubs_to_play(self._bookings, club_id, booking_id, now=now)
        return CancelOutcome(
            moved_to=await self._club.absorbing_court(booking_id, because=because)
        )


@final
class CancelTheGame:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        bookings: PlayerBookings,
        club: ClubBookings,
        refunds: SeatRefunds,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._bookings = bookings
        self._club = club
        self._refunds = refunds
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(
        self,
        *,
        club_id: UUID,
        booking_id: UUID,
        because: ClubCancelReason,
        anyway: bool,
    ) -> CancelOutcome:
        """A move by cancel when a free court absorbs it now, or — with none,
        or ``anyway`` — the game called off; the answer says which."""

        now = instant(self._clock.now())
        proposal = await self._proposals.load_for_update(booking_id)
        await _still_the_clubs_to_play(self._bookings, club_id, booking_id, now=now)
        proposal = invariant(proposal, f"a booking {booking_id} with no proposal")
        came_to = await self._club.cancel(
            booking_id, because=because, anyway=anyway, at=now
        )
        if isinstance(came_to, CourtToMoveTo):
            # Moved, never called off: every hold or taken share stays as it
            # is, and nobody is refunded, let go or owed a card.
            await self._uow.commit()
            return CancelOutcome(moved_to=came_to)
        cancelled = came_to
        await self._refunds.refund(
            booking_id,
            cancelled.still_in,
            reason=RefundReason.CANCELLED_BY_THE_CLUB,
            because=because,
            at=now,
        )
        # A leaver whose seat was still open and paid is refunded too — in a
        # leaver's words, and owed no new game (Q108).
        leavers = [p for p in cancelled.refunded if p not in cancelled.still_in]
        if leavers:
            await self._refunds.refund(
                booking_id,
                leavers,
                reason=RefundReason.CANCELLED_AFTER_YOU_LEFT,
                because=because,
                at=now,
            )
        # A rescue's payment somebody confirmed for a seat here and never took
        # is let go with the game: nobody pays it.
        await self._undecided.release(booking_id, keeping=(), at=now)
        proposal.club_cancelled(cancelled.still_in, at=now)
        await self._proposals.save(proposal)
        await self._uow.commit()
        return CancelOutcome(moved_to=None)


async def _the_clubs(
    bookings: PlayerBookings, club_id: UUID, booking_id: UUID
) -> BookedGame:
    game = await bookings.find(booking_id)
    if game is None or game.club_id != club_id:
        raise BookingNotFound()
    return game


async def _still_the_clubs_to_play(
    bookings: PlayerBookings, club_id: UUID, booking_id: UUID, *, now: Instant
) -> BookedGame:
    """The club's game, refused unless it may still be moved or cancelled."""

    game = await _the_clubs(bookings, club_id, booking_id)
    if game.called_off_reason(now) is not None:
        raise BookingIsCalledOff()
    if now >= game.start:
        raise GameHasStarted()
    return game

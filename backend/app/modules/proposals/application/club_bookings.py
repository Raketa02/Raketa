"""**The club runs its Raketa bookings** (#547; the mechanics §15.1, §16.7–§16.10,
§16.14, §16.16; the screens B4, B6).

Four acts and two reads on the club surface, each for the desk's own club:

- **the day** — every booking whose game starts on a calendar day at the club,
  filtered, each with its status, its players (name, *paid*, *checked in*), its
  money (the court's price, what was collected, what was refunded) and the group
  it came from;
- **the free courts** — where a game may be moved: every other court of its sport
  the club still has for Raketa at its hour;
- **Move** — onto one of them; the players read the new number;
- **Cancel**, with the club's reason — everybody still in refunded **in full**,
  and a leaver whose open seat was still paid for; nothing on anybody's record;
  the game, its room and its court hour off; and **the people still in dealt a
  new card first** — never at this club and hour — by the proposer, which the
  cancel makes due (``propose_games.py``);
- **Check in** — a code scanned or typed at the desk, on the game's day: the
  player was there, and can never be reported as not coming.

Move and Cancel are the club's **until the game starts**, and never on a game
called off or still waiting for the club's answer. **Every act locks the game
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
    ClubFilter,
    ClubStatus,
    CodeAtTheDesk,
    CourtToMoveTo,
    Takings,
    club_status,
    shown_under,
    still_to_be_played,
)
from app.modules.proposals.domain.errors import (
    AlreadyCheckedIn,
    BookingIsCalledOff,
    BookingNotBooked,
    BookingNotFound,
    CheckInCodeForAnotherClub,
    CheckInCodeForAnotherDay,
    CheckInCodeUnknown,
    CheckInIsOff,
    CourtNotFree,
    GameHasStarted,
)
from app.modules.proposals.domain.home import (
    BookedGame,
    BookingStage,
    ClubCancelReason,
)
from app.modules.proposals.domain.ports import (
    BookingTakings,
    ClubBookings,
    DeskCheckIns,
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
        self, *, club_id: UUID, booking_id: UUID, because: ClubCancelReason
    ) -> None:
        now = instant(self._clock.now())
        proposal = await self._proposals.load_for_update(booking_id)
        await _still_the_clubs_to_play(self._bookings, club_id, booking_id, now=now)
        proposal = invariant(proposal, f"a booking {booking_id} with no proposal")
        cancelled = await self._club.cancel(booking_id, because=because, at=now)
        await self._refunds.refund(
            booking_id,
            cancelled.refunded,
            reason=RefundReason.CANCELLED_BY_THE_CLUB,
            because=because,
            at=now,
        )
        # A rescue's payment somebody confirmed for a seat here and never took
        # is let go with the game: nobody pays it.
        await self._undecided.release(booking_id, keeping=(), at=now)
        proposal.club_cancelled(cancelled.still_in, at=now)
        await self._proposals.save(proposal)
        await self._uow.commit()


async def _the_clubs(
    bookings: PlayerBookings, club_id: UUID, booking_id: UUID
) -> BookedGame:
    game = await bookings.find(booking_id)
    # A request taken back is no booking of the club's: the game is filling
    # again, as it was before it was full (#624).
    if game is None or game.club_id != club_id or game.filling_again:
        raise BookingNotFound()
    return game


async def _still_the_clubs_to_play(
    bookings: PlayerBookings, club_id: UUID, booking_id: UUID, *, now: Instant
) -> BookedGame:
    """The club's game, refused unless it may still be moved or cancelled."""

    game = await _the_clubs(bookings, club_id, booking_id)
    if game.stage is BookingStage.WAITING_FOR_THE_CLUB:
        raise BookingNotBooked()
    if game.called_off_reason(now) is not None:
        raise BookingIsCalledOff()
    if now >= game.start:
        raise GameHasStarted()
    return game


# --------------------------------------------------------------------------- #
# Check in
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class CheckedIn:
    game: BookedGame
    player_id: UUID
    name: str | None
    at: Instant


@final
class CheckInAtTheDesk:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        bookings: PlayerBookings,
        club: ClubBookings,
        desk: DeskCheckIns,
        names: PlayerNames,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._bookings = bookings
        self._club = club
        self._desk = desk
        self._names = names
        self._uow = uow
        self._clock = clock

    async def execute(self, *, club_id: UUID, code: str) -> CheckedIn:
        now = instant(self._clock.now())
        if not await self._desk.checks_players_in(club_id):
            raise CheckInIsOff()
        seat = await self._club.seat_for(code, club_id=club_id, now=now)
        if seat.where is CodeAtTheDesk.ANOTHER_CLUB:
            raise CheckInCodeForAnotherClub()
        if seat.booking_id is None or seat.player_id is None:
            raise CheckInCodeUnknown()
        booking_id, player_id = seat.booking_id, seat.player_id
        await self._proposals.load_for_update(booking_id)
        found = await self._bookings.find(booking_id)
        if found is not None and found.filling_again:
            # A seat on a request taken back: no Game at the desk (#624).
            raise CheckInCodeUnknown()
        game = await _the_clubs(self._bookings, club_id, booking_id)
        if seat.where is CodeAtTheDesk.ANOTHER_DAY:
            raise CheckInCodeForAnotherDay(starts_at=game.start.isoformat())
        if game.called_off_reason(now) is not None:
            raise BookingIsCalledOff()
        if game.stage is BookingStage.WAITING_FOR_THE_CLUB or not game.has_a_seat_for(
            player_id
        ):
            # A seat on a request, or one its player left: no seat to check in.
            raise CheckInCodeUnknown()
        names = await self._names.names_of([player_id])
        if player_id in game.checked_in:
            raise AlreadyCheckedIn(checked_in_at=game.checked_in[player_id].isoformat())
        await self._club.check_in(booking_id, player_id, at=now)
        await self._uow.commit()
        return CheckedIn(
            game=game, player_id=player_id, name=names.get(player_id), at=now
        )

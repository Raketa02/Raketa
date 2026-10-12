"""The Booking repository and directory: the stream, and the two projections
written beside it.

The same shape as the other aggregate repositories (``docs/adr/0018``), and,
like a proposal's, **its projections are written by ``save``, in the caller's
transaction, and flushed** — so the court hour is gone from what the club
sells, and the game counted in the player's week, the moment the fill commits.

**What each read counts is the state's** (#543): a booking waiting for its club
holds its court hour, as a booked one does, and a called-off one holds nothing;
only a **booked** game is a game in a player's week or a group's *Games* — whole,
or with a seat open (#544); and a player's games are every booking they have a
seat on, whatever it came to — a request taken back because a seat opened is
still the game of the people it left In (Q106), whose rows stay while the
openers' go, and a leaver no longer has one. **A rescue is a seat row like any
other** (#545): the game is the joiner's from the moment they take it — and a
seat kept for a rescuer whose share was refused is a ``booking_keeps`` row,
never a seat of theirs (#640).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import final
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import Executable
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.infrastructure.database.stored_time import stored_instant
from app.kernel import Instant, Sport
from app.modules.bookings.domain.booking import Booking, BookingState
from app.modules.bookings.domain.errors import CourtTaken
from app.modules.bookings.domain.events import (
    BookingAccepted,
    BookingAwaitingAPayment,
    BookingConfirmed,
    BookingRefused,
    BookingRequested,
    BookingTimedOut,
    CalledOffAtCutOff,
    CancelledByClub,
    CardFixed,
    CardToFix,
    CourtMoved,
    KeptSeatRanOut,
    PaymentNotInTime,
    PlayerCheckedIn,
    RequestWithdrawn,
    NoSaidToTheSeat,
    SeatKept,
    SeatLeft,
    SeatRescued,
)
from app.modules.bookings.domain.ports import HeldCourtHour
from app.modules.bookings.infrastructure.booking_models import (
    BookingKeepORM,
    BookingORM,
    BookingSeatORM,
)

BOOKING_AGGREGATE = "booking"

#: The states a booked game is in while it will be played: whole, or with a
#: seat open (#544).
_BOOKED = (BookingState.BOOKED.value, BookingState.SEAT_OPEN.value)


@final
class EventSourcedBookingRepository:
    """``BookingRepository`` over ``DomainEventStore`` and the projections."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._session = session
        self._event_store = event_store
        self._events = events
        self._versions: dict[UUID, int] = {}

    async def load(self, booking_id: UUID) -> Booking | None:
        stored = await self._event_store.load_stream(
            aggregate_type=BOOKING_AGGREGATE, aggregate_id=booking_id
        )
        if not stored:
            return None
        booking = Booking.from_history(record.event for record in stored)
        self._versions[booking_id] = booking.version
        return booking

    async def save(self, booking: Booking) -> None:
        pending = booking.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=BOOKING_AGGREGATE,
            aggregate_id=booking.booking_id,
            expected_version=self._versions.get(booking.booking_id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        try:
            for event in pending:
                await self._project(event, booking)
            await self._session.flush()
        except IntegrityError as taken:
            # Two games at one hour that read one court free: the second claim
            # meets the court hour's unique index. The transaction is spent.
            raise CourtTaken() from taken
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[booking.booking_id] = booking.version

    async def _project(self, event: object, booking: Booking) -> None:
        if isinstance(event, BookingConfirmed):
            self._session.add(
                BookingORM(
                    id=event.booking_id,
                    pool_id=event.pool_id,
                    club_id=event.club_id,
                    court_id=event.court_id,
                    sport=event.sport,
                    start=event.start,
                    share_grosze=event.share_grosze,
                    cut_off=event.cut_off,
                    state=BookingState.BOOKED.value,
                    game_id=event.game_id,
                    booked_at=event.occurred_at,
                )
            )
            self._seat(event.booking_id, event.first_side, event.second_side)
        elif isinstance(event, BookingRequested):
            await self._requested(event)
        elif isinstance(event, BookingAccepted):
            await self._row(
                event.booking_id,
                state=BookingState.BOOKED.value,
                game_id=event.game_id,
                booked_at=event.occurred_at,
            )
        elif isinstance(event, (BookingRefused, BookingTimedOut)):
            await self._row(event.booking_id, state=BookingState.CALLED_OFF.value)
        elif isinstance(event, BookingAwaitingAPayment):
            # The club's yes keeps the court: the row holds its hour still.
            await self._row(
                event.booking_id, state=BookingState.WAITING_FOR_A_PAYMENT.value
            )
        elif isinstance(event, PaymentNotInTime):
            await self._row(event.booking_id, state=BookingState.CALLED_OFF.value)
            if not event.for_good:
                # The payers' seats reopen; the people still In keep theirs,
                # so the game stays on their Home (Q106).
                await self._statement(
                    delete(BookingSeatORM).where(
                        BookingSeatORM.booking_id == event.booking_id,
                        BookingSeatORM.player_id.in_(event.player_ids),
                    )
                )
        elif isinstance(event, RequestWithdrawn):
            await self._row(event.booking_id, state=BookingState.CALLED_OFF.value)
            # The seats that opened go; the people still In keep theirs, so
            # the game stays on their Home (Q106).
            await self._statement(
                delete(BookingSeatORM).where(
                    BookingSeatORM.booking_id == event.booking_id,
                    BookingSeatORM.player_id.in_(event.player_ids),
                )
            )
        elif isinstance(event, SeatLeft):
            await self._row(
                event.booking_id,
                state=BookingState.SEAT_OPEN.value,
                open_since=booking.open_since,
            )
            await self._statement(
                update(BookingSeatORM)
                .where(
                    BookingSeatORM.booking_id == event.booking_id,
                    BookingSeatORM.player_id == event.player_id,
                )
                .values(left_at=event.occurred_at, card_to_fix_until=None)
            )
        elif isinstance(event, (CardToFix, CardFixed)):
            await self._statement(
                update(BookingSeatORM)
                .where(
                    BookingSeatORM.booking_id == event.booking_id,
                    BookingSeatORM.player_id == event.player_id,
                )
                .values(
                    card_to_fix_until=event.until
                    if isinstance(event, CardToFix)
                    else None
                )
            )
        elif isinstance(event, SeatRescued):
            # The row before its seat, as a request's are.
            await self._row(
                event.booking_id,
                state=booking.state.value,
                open_since=booking.open_since,
            )
            self._session.add(
                BookingSeatORM(
                    booking_id=event.booking_id,
                    player_id=event.player_id,
                    side=event.side,
                )
            )
            # A seat kept for them is the one they took (#640).
            await self._unkeep(event.booking_id, event.player_id)
        elif isinstance(event, SeatKept):
            # Kept again, with the time they had: one row a rescuer.
            await self._unkeep(event.booking_id, event.player_id)
            self._session.add(
                BookingKeepORM(
                    booking_id=event.booking_id,
                    player_id=event.player_id,
                    until=event.until,
                )
            )
        elif isinstance(event, KeptSeatRanOut):
            # Their refused payment is still theirs to confirm while the seat
            # is free: the row stays, out of the job's read.
            await self._statement(
                update(BookingKeepORM)
                .where(
                    BookingKeepORM.booking_id == event.booking_id,
                    BookingKeepORM.player_id == event.player_id,
                )
                .values(ran_out=True)
            )
        elif isinstance(event, NoSaidToTheSeat):
            # A no to a card is the booking's to fold; no read asks it of a row.
            pass
        elif isinstance(event, (CalledOffAtCutOff, CancelledByClub)):
            await self._row(event.booking_id, state=BookingState.CALLED_OFF.value)
            # A game off has no card to fix (#639), and no seat to keep (#640).
            await self._statement(
                update(BookingSeatORM)
                .where(BookingSeatORM.booking_id == event.booking_id)
                .values(card_to_fix_until=None)
            )
            await self._statement(
                delete(BookingKeepORM).where(
                    BookingKeepORM.booking_id == event.booking_id
                )
            )
        elif isinstance(event, CourtMoved):
            # The court hour's own index refuses a court another game holds.
            await self._row(event.booking_id, court_id=event.court_id)
        elif isinstance(event, PlayerCheckedIn):
            # Retired (#651): nothing writes it, and no row ever held it.
            pass
        else:
            raise TypeError(f"Unsupported booking event {event!r}")

    async def _requested(self, event: BookingRequested) -> None:
        """A request — the first, or the same game asked again with whoever is
        In now, on the court free now."""

        if await self._session.get(BookingORM, event.booking_id) is None:
            self._session.add(
                BookingORM(
                    id=event.booking_id,
                    pool_id=event.pool_id,
                    club_id=event.club_id,
                    court_id=event.court_id,
                    sport=event.sport,
                    start=event.start,
                    share_grosze=event.share_grosze,
                    cut_off=event.cut_off,
                    state=BookingState.WAITING_FOR_THE_CLUB.value,
                    answer_by=event.answer_by,
                )
            )
        else:
            await self._row(
                event.booking_id,
                court_id=event.court_id,
                cut_off=event.cut_off,
                state=BookingState.WAITING_FOR_THE_CLUB.value,
                answer_by=event.answer_by,
            )
            await self._statement(
                delete(BookingSeatORM).where(
                    BookingSeatORM.booking_id == event.booking_id
                )
            )
        # The row before its seats, which reference it.
        await self._session.flush()
        self._seat(event.booking_id, event.first_side, event.second_side)

    def _seat(
        self,
        booking_id: UUID,
        first_side: tuple[UUID, ...],
        second_side: tuple[UUID, ...],
    ) -> None:
        for side, players in (("A", first_side), ("B", second_side)):
            for player_id in players:
                self._session.add(
                    BookingSeatORM(
                        booking_id=booking_id, player_id=player_id, side=side
                    )
                )

    async def _unkeep(self, booking_id: UUID, player_id: UUID) -> None:
        await self._statement(
            delete(BookingKeepORM).where(
                BookingKeepORM.booking_id == booking_id,
                BookingKeepORM.player_id == player_id,
            )
        )

    async def _row(self, booking_id: UUID, **values: object) -> None:
        await self._statement(
            update(BookingORM).where(BookingORM.id == booking_id).values(**values)
        )

    async def _statement(self, statement: Executable) -> None:
        # A statement, not a unit-of-work change, so whatever this save added
        # before it is flushed first — the row it touches may be one.
        await self._session.flush()
        await self._session.execute(statement)


@final
class SqlAlchemyBookingDirectory:
    """``BookingDirectory`` over the projections."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def held_at(
        self, club_id: UUID, *, start: Instant, end: Instant | None
    ) -> Sequence[HeldCourtHour]:
        query = select(BookingORM.court_id, BookingORM.start, BookingORM.id).where(
            BookingORM.club_id == club_id,
            BookingORM.start >= start,
            # Waiting for the club holds the court as booked does.
            BookingORM.state != BookingState.CALLED_OFF.value,
        )
        if end is not None:
            query = query.where(BookingORM.start < end)
        rows = await self._session.execute(query)
        return [
            HeldCourtHour(
                court_id=court_id, start=stored_instant(at), booking_id=booking_id
            )
            for court_id, at, booking_id in rows.all()
        ]

    async def cards_to_fix_past(self, *, now: Instant) -> Sequence[UUID]:
        rows = await self._session.scalars(
            select(BookingSeatORM.booking_id)
            .where(
                BookingSeatORM.card_to_fix_until <= now,
                BookingSeatORM.left_at.is_(None),
            )
            .group_by(BookingSeatORM.booking_id)
            .order_by(
                func.min(BookingSeatORM.card_to_fix_until), BookingSeatORM.booking_id
            )
        )
        return tuple(rows.all())

    async def cards_to_fix_of(self, player_id: UUID) -> Sequence[UUID]:
        rows = await self._session.scalars(
            select(BookingSeatORM.booking_id).where(
                BookingSeatORM.player_id == player_id,
                BookingSeatORM.card_to_fix_until.is_not(None),
                BookingSeatORM.left_at.is_(None),
            )
        )
        return tuple(rows.all())

    async def keeps_past(self, *, now: Instant) -> Sequence[UUID]:
        rows = await self._session.scalars(
            select(BookingKeepORM.booking_id)
            .where(BookingKeepORM.until <= now, BookingKeepORM.ran_out.is_(False))
            .group_by(BookingKeepORM.booking_id)
            .order_by(func.min(BookingKeepORM.until), BookingKeepORM.booking_id)
        )
        return tuple(rows.all())

    async def kept_for(self, player_id: UUID) -> Sequence[UUID]:
        rows = await self._session.scalars(
            select(BookingKeepORM.booking_id).where(
                BookingKeepORM.player_id == player_id
            )
        )
        return tuple(rows.all())

    async def starts_for(
        self, player_id: UUID, *, start: Instant, end: Instant | None
    ) -> Sequence[Instant]:
        query = (
            select(BookingORM.start)
            .join(BookingSeatORM, BookingSeatORM.booking_id == BookingORM.id)
            .where(
                BookingSeatORM.player_id == player_id,
                BookingSeatORM.left_at.is_(None),
                BookingORM.start >= start,
                BookingORM.state.in_(_BOOKED),
            )
            .order_by(BookingORM.start)
        )
        if end is not None:
            query = query.where(BookingORM.start < end)
        rows = await self._session.scalars(query)
        return [stored_instant(at) for at in rows.all()]

    async def of_player(
        self, player_id: UUID, *, since: Instant | None
    ) -> Sequence[UUID]:
        query = (
            select(BookingORM.id)
            .join(BookingSeatORM, BookingSeatORM.booking_id == BookingORM.id)
            .where(
                BookingSeatORM.player_id == player_id,
                BookingSeatORM.left_at.is_(None),
            )
            .order_by(BookingORM.start, BookingORM.id)
        )
        if since is not None:
            query = query.where(BookingORM.start >= since)
        rows = await self._session.scalars(query)
        return list(rows.all())

    async def games_before(
        self, player_id: UUID, *, before: Instant
    ) -> Mapping[UUID, UUID]:
        rows = await self._session.execute(
            select(BookingORM.game_id, BookingORM.id)
            .join(BookingSeatORM, BookingSeatORM.booking_id == BookingORM.id)
            .where(
                BookingSeatORM.player_id == player_id,
                BookingSeatORM.left_at.is_(None),
                BookingORM.start < before,
                BookingORM.game_id.is_not(None),
            )
        )
        return {game_id: booking_id for game_id, booking_id in rows.all()}

    async def counted_in(self, pool_ids: Collection[UUID]) -> Mapping[UUID, int]:
        if not pool_ids:
            return {}
        rows = await self._session.execute(
            select(BookingORM.pool_id, func.count(BookingORM.id))
            .where(
                BookingORM.pool_id.in_(sorted(set(pool_ids))),
                BookingORM.state.in_(_BOOKED),
            )
            .group_by(BookingORM.pool_id)
        )
        return {pool_id: count for pool_id, count in rows.all()}

    async def waiting_at(self, club_id: UUID) -> Sequence[UUID]:
        rows = await self._session.scalars(
            select(BookingORM.id)
            .where(
                BookingORM.club_id == club_id,
                BookingORM.state == BookingState.WAITING_FOR_THE_CLUB.value,
            )
            .order_by(BookingORM.answer_by, BookingORM.id)
        )
        return list(rows.all())

    async def unanswered(self, *, now: Instant) -> Sequence[UUID]:
        rows = await self._session.scalars(
            select(BookingORM.id)
            .where(
                BookingORM.state == BookingState.WAITING_FOR_THE_CLUB.value,
                BookingORM.answer_by <= now,
            )
            .order_by(BookingORM.answer_by, BookingORM.id)
        )
        return list(rows.all())

    async def rescues_in(
        self, pool_id: UUID, *, sport: Sport, now: Instant
    ) -> Sequence[UUID]:
        rows = await self._session.scalars(
            select(BookingORM.id)
            .where(
                BookingORM.pool_id == pool_id,
                BookingORM.sport == sport.value,
                BookingORM.state == BookingState.SEAT_OPEN.value,
                BookingORM.start > now,
            )
            .order_by(BookingORM.start, BookingORM.id)
        )
        return list(rows.all())

    async def at_club(
        self, club_id: UUID, *, start: Instant, end: Instant
    ) -> Sequence[UUID]:
        rows = await self._session.scalars(
            select(BookingORM.id)
            .where(
                BookingORM.club_id == club_id,
                BookingORM.start >= start,
                BookingORM.start < end,
            )
            .order_by(BookingORM.start, BookingORM.id)
        )
        return list(rows.all())

    async def booked_between(
        self, *, start: Instant, end: Instant
    ) -> Mapping[UUID, Sequence[UUID]]:
        rows = await self._session.execute(
            select(BookingORM.club_id, BookingORM.id)
            .where(BookingORM.booked_at >= start, BookingORM.booked_at < end)
            .order_by(BookingORM.club_id, BookingORM.start, BookingORM.id)
        )
        booked: dict[UUID, list[UUID]] = {}
        for club_id, booking_id in rows.all():
            booked.setdefault(club_id, []).append(booking_id)
        return booked

    async def booked_starting(self, *, after: Instant, by: Instant) -> Sequence[UUID]:
        rows = await self._session.scalars(
            select(BookingORM.id)
            .where(
                BookingORM.state == BookingState.BOOKED.value,
                BookingORM.start > after,
                BookingORM.start <= by,
            )
            .order_by(BookingORM.start, BookingORM.id)
        )
        return list(rows.all())

    async def short_at_the_cut_off(self, *, now: Instant) -> Sequence[UUID]:
        rows = await self._session.scalars(
            select(BookingORM.id)
            .where(
                BookingORM.state == BookingState.SEAT_OPEN.value,
                BookingORM.cut_off <= now,
                BookingORM.open_since < BookingORM.cut_off,
            )
            .order_by(BookingORM.cut_off, BookingORM.id)
        )
        return list(rows.all())

    async def ever_seated(
        self, player_ids: Collection[UUID]
    ) -> Sequence[tuple[UUID, UUID]]:
        if not player_ids:
            return []
        rows = await self._session.execute(
            select(BookingSeatORM.player_id, BookingSeatORM.booking_id)
            .join(BookingORM, BookingORM.id == BookingSeatORM.booking_id)
            .where(
                BookingSeatORM.player_id.in_(sorted(set(player_ids))),
                BookingORM.booked_at.is_not(None),
            )
            .order_by(BookingSeatORM.player_id, BookingSeatORM.booking_id)
        )
        return [(player_id, booking_id) for player_id, booking_id in rows.all()]

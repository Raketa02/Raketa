"""The facts that pass between proposals and bookings, every one answered by
an adapter **signed here**, so the arrow runs ``proposals → bookings`` only
(#541, #542).

``BookingsGameBookings`` is the fill's demand — a court for a full game, and the
booking that opens its Game — over the Bookings context's own use cases;
``BookingsBookedGameChanges`` is what happens to a booked game after (#544,
#545): a player leaving it, somebody taking the seat they left or saying no to
it, a seat kept for a rescuer whose share was refused (#640), and the cut-off
calling off one still short.
``BookingsClubRequests`` is an On request club's (#543): the request a full game
is put to the club as, the club's yes or no, and a seat opening while it waits.
``BookingsBookedGames`` answers *games per week* and *one game per hour* — the
deck's, the proposer's and the fill's — with a player's booked games, replacing
the stand-in that answered nothing while no game could be booked.
``BookingsPlayerBookings`` is Home's and the details': a player's booked games
as their bookings record them, folded from each stream — and a pool's booked
games with a seat open (#545).
``BookingsClubBookings`` is the club website's (#547): a day of its bookings, a
court to move one to, the move and the cancel.
``BookingsGroupBornGames`` is the club's *Games* figure, which
``groups`` asks in its own words: **a group's pool is filed under the group's own
id**, which is this context's fact, so the games booked in a group are the
bookings in its pool.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import final
from uuid import UUID

from app.kernel import Instant, Sport, invariant
from app.modules.bookings.application.at_the_club import (
    CancelTheBooking,
    MoveTheBooking,
)
from app.modules.bookings.application.book_the_game import (
    BookTheGame,
    FindACourt,
    GameToBook,
)
from app.modules.bookings.application.leaving import (
    CallOffAtTheCutOff,
    LeaveTheBooking,
    TimeToFixTheCard,
)
from app.modules.bookings.application.rescues import (
    KeepTheSeat,
    RescueTheSeat,
    SayNoToTheSeat,
)
from app.modules.bookings.application.requests import (
    BookTheRequest,
    CallOffForAPayment,
    GameToRequest,
    RequestTheGame,
    CallOffTheRequest,
    WaitForThePayment,
    WithdrawTheRequest,
)
from app.modules.bookings.domain.booking import (
    BookedCourt,
    Booking,
    BookingState,
    CalledOff,
    CancelReason,
    Departure,
)
from app.modules.bookings.domain.errors import CourtTaken
from app.modules.bookings.domain.ports import (
    BookingDirectory,
    BookingRepository,
)
from app.modules.proposals.domain.club_bookings import (
    ClubCancellation,
    CourtToMoveTo,
)
from app.modules.proposals.domain.errors import CourtJustTaken
from app.modules.proposals.domain.home import (
    BookedGame,
    BookingStage,
    CalledOffReason,
    RefusedHolding,
    ClubCancelReason,
    KeptSeat,
    OpenSeat,
)
from app.modules.proposals.domain.ports import (
    BookableCourt,
    ClubRequest,
    FullGame,
    GameToAsk,
    RefusedPayment,
)
from app.modules.proposals.domain.proposal import ClubAnswer, ReopenReason, TimeTo


@final
class BookingsGameBookings:
    def __init__(self, *, find: FindACourt, book: BookTheGame) -> None:
        self._find = find
        self._book = book

    async def court_for(
        self, club_id: UUID, *, sport: Sport, start: Instant
    ) -> BookableCourt | None:
        offered = await self._find.execute(club_id, sport=sport, start=start)
        if offered is None:
            return None
        return BookableCourt(
            court_id=offered.court.court_id,
            name=offered.court.name,
            cut_off=offered.cut_off,
            time_to_confirm=offered.time_to_confirm,
        )

    async def book(self, game: FullGame, *, at: Instant) -> UUID:
        try:
            return await self._booked(game, at=at)
        except CourtTaken as taken:
            raise CourtJustTaken() from taken

    async def _booked(self, game: FullGame, *, at: Instant) -> UUID:
        booking = await self._book.execute(
            GameToBook(
                booking_id=game.proposal_id,
                pool_id=game.pool_id,
                club_id=game.club_id,
                sport=game.sport,
                kind=game.kind,
                start=game.start,
                share_grosze=game.share_grosze,
                first_side=game.first_side,
                second_side=game.second_side,
                court=BookedCourt(court_id=game.court.court_id, name=game.court.name),
                cut_off=game.court.cut_off,
            ),
            at=at,
        )
        return invariant(booking.game_id, f"{booking.booking_id} booked with no game")


@final
class BookingsBookedGameChanges:
    def __init__(
        self,
        *,
        leave: LeaveTheBooking,
        rescue: RescueTheSeat,
        say_no: SayNoToTheSeat,
        call_off: CallOffAtTheCutOff,
        fix: TimeToFixTheCard,
        keep: KeepTheSeat,
        directory: BookingDirectory,
    ) -> None:
        self._leave = leave
        self._rescue = rescue
        self._say_no = say_no
        self._call_off = call_off
        self._fix = fix
        self._keep = keep
        self._directory = directory

    async def leave(self, booking_id: UUID, player_id: UUID, *, at: Instant) -> None:
        await self._leave.execute(booking_id, player_id, at=at)

    async def rescue(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> OpenSeat:
        return _open_seat(await self._rescue.execute(booking_id, player_id, at=at))

    async def say_no_to_the_seat(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> bool:
        return await self._say_no.execute(booking_id, player_id, at=at)

    async def short_at_the_cut_off(self, *, now: Instant) -> Sequence[UUID]:
        return await self._directory.short_at_the_cut_off(now=now)

    async def call_off_at_the_cut_off(
        self, booking_id: UUID, *, at: Instant
    ) -> tuple[UUID, ...] | None:
        return await self._call_off.execute(booking_id, at=at)

    async def card_to_fix(
        self,
        booking_id: UUID,
        player_id: UUID,
        *,
        until: Instant,
        refused: RefusedPayment,
        at: Instant,
    ) -> None:
        await self._fix.give(
            booking_id,
            player_id,
            until=until,
            seat_charge_id=refused.seat_charge_id,
            reason=refused.refusal.value,
            at=at,
        )

    async def card_fixed(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> bool:
        return await self._fix.fixed(booking_id, player_id, at=at)

    async def card_not_fixed(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> bool:
        return await self._fix.not_fixed(booking_id, player_id, at=at)

    async def cards_to_fix_past(self, *, now: Instant) -> Sequence[UUID]:
        return await self._directory.cards_to_fix_past(now=now)

    async def cards_to_fix_of(self, player_id: UUID) -> Sequence[UUID]:
        return await self._directory.cards_to_fix_of(player_id)

    async def keep_the_seat(
        self,
        booking_id: UUID,
        player_id: UUID,
        *,
        until: Instant,
        refused: RefusedPayment,
        time_to: TimeTo,
        at: Instant,
    ) -> None:
        await self._keep.keep(
            booking_id,
            player_id,
            until=until,
            seat_charge_id=refused.seat_charge_id,
            reason=refused.refusal.value,
            to_fix_the_card=time_to is TimeTo.FIX_THE_CARD,
            at=at,
        )

    async def kept_seat_ran_out(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> bool:
        return await self._keep.ran_out(booking_id, player_id, at=at)

    async def keeps_past(self, *, now: Instant) -> Sequence[UUID]:
        return await self._directory.keeps_past(now=now)

    async def kept_for(self, player_id: UUID) -> Sequence[UUID]:
        return await self._directory.kept_for(player_id)


@final
class BookingsClubRequests:
    def __init__(
        self,
        *,
        bookings: BookingRepository,
        directory: BookingDirectory,
        ask: RequestTheGame,
        accept: BookTheRequest,
        turn_down: CallOffTheRequest,
        withdraw: WithdrawTheRequest,
        wait: WaitForThePayment,
        not_in_time: CallOffForAPayment,
    ) -> None:
        self._bookings = bookings
        self._directory = directory
        self._ask = ask
        self._accept = accept
        self._turn_down = turn_down
        self._withdraw = withdraw
        self._wait = wait
        self._not_in_time = not_in_time

    async def ask(self, game: GameToAsk, *, at: Instant) -> None:
        try:
            await self._ask.execute(
                GameToRequest(
                    booking_id=game.proposal_id,
                    pool_id=game.pool_id,
                    club_id=game.club_id,
                    sport=game.sport,
                    kind=game.kind,
                    start=game.start,
                    share_grosze=game.share_grosze,
                    first_side=game.first_side,
                    second_side=game.second_side,
                    court=BookedCourt(
                        court_id=game.court.court_id, name=game.court.name
                    ),
                    cut_off=game.court.cut_off,
                    answer_by=game.answer_by,
                    filled_by=game.filled_by,
                ),
                at=at,
            )
        except CourtTaken as taken:
            raise CourtJustTaken() from taken

    async def find(self, booking_id: UUID) -> ClubRequest | None:
        booking = await self._bookings.load(booking_id)
        return None if booking is None else _request(booking)

    async def waiting_at(self, club_id: UUID) -> Sequence[ClubRequest]:
        found: list[ClubRequest] = []
        for booking_id in await self._directory.waiting_at(club_id):
            request = await self.find(booking_id)
            if request is not None and request.waiting:
                found.append(request)
        return found

    async def unanswered(self, *, now: Instant) -> Sequence[UUID]:
        return await self._directory.unanswered(now=now)

    async def accept(self, booking_id: UUID, *, at: Instant) -> UUID:
        booking = await self._accept.execute(booking_id, at=at)
        return invariant(booking.game_id, f"{booking_id} accepted with no game")

    async def turn_down(
        self,
        booking_id: UUID,
        *,
        answer: ClubAnswer,
        reason: str | None,
        at: Instant,
    ) -> None:
        if answer is ClubAnswer.REFUSED:
            await self._turn_down.refused(booking_id, reason=reason, at=at)
        else:
            await self._turn_down.unanswered(booking_id, at=at)

    async def withdraw(
        self,
        booking_id: UUID,
        *,
        player_ids: tuple[UUID, ...],
        left: tuple[UUID, ...] = (),
        at: Instant,
    ) -> bool:
        return await self._withdraw.execute(
            booking_id, player_ids=player_ids, left=left, at=at
        )

    async def await_a_payment(
        self,
        booking_id: UUID,
        *,
        player_ids: tuple[UUID, ...],
        until: Instant,
        to_fix_the_card: bool,
        at: Instant,
    ) -> None:
        await self._wait.execute(
            booking_id,
            player_ids=player_ids,
            until=until,
            to_fix_the_card=to_fix_the_card,
            at=at,
        )

    async def payment_not_in_time(
        self,
        booking_id: UUID,
        *,
        player_ids: tuple[UUID, ...],
        for_good: bool,
        at: Instant,
    ) -> bool:
        return await self._not_in_time.execute(
            booking_id, player_ids=player_ids, for_good=for_good, at=at
        )


def _request(booking: Booking) -> ClubRequest | None:
    """The request a booking was put to its club as — ``None`` for one born
    booked, which no club was asked about."""

    if booking.answer_by is None:
        return None
    return ClubRequest(
        booking_id=booking.booking_id,
        club_id=booking.club_id,
        sport=booking.sport,
        kind=booking.kind,
        start=booking.start,
        share_grosze=booking.share_grosze,
        court_name=booking.court.name,
        first_side=booking.first_side,
        second_side=booking.second_side,
        cut_off=booking.cut_off,
        answer_by=booking.answer_by,
        waiting=booking.is_waiting,
        pay_by=booking.pay_by,
    )


@final
class BookingsBookedGames:
    def __init__(self, directory: BookingDirectory) -> None:
        self._directory = directory

    async def starts_of(
        self, player_id: UUID, *, start: Instant, end: Instant
    ) -> Sequence[Instant]:
        return await self._directory.starts_for(player_id, start=start, end=end)


@final
class BookingsPlayerBookings:
    def __init__(
        self,
        *,
        directory: BookingDirectory,
        bookings: BookingRepository,
    ) -> None:
        self._directory = directory
        self._bookings = bookings

    async def of_player(
        self, player_id: UUID, *, since: Instant | None
    ) -> Sequence[BookedGame]:
        found: list[BookedGame] = []
        for booking_id in await self._directory.of_player(player_id, since=since):
            booking = await self._bookings.load(booking_id)
            if booking is not None:
                found.append(_booked_game(booking))
        return found

    async def games_before(
        self, player_id: UUID, *, before: Instant
    ) -> Mapping[UUID, UUID]:
        return await self._directory.games_before(player_id, before=before)

    async def find(self, booking_id: UUID) -> BookedGame | None:
        booking = await self._bookings.load(booking_id)
        return None if booking is None else _booked_game(booking)

    async def rescues_in(
        self, pool_id: UUID, *, sport: Sport, now: Instant
    ) -> Sequence[BookedGame]:
        found: list[BookedGame] = []
        for booking_id in await self._directory.rescues_in(
            pool_id, sport=sport, now=now
        ):
            game = await self.find(booking_id)
            if game is not None:
                found.append(game)
        return found


_STAGES = {
    BookingState.WAITING_FOR_THE_CLUB: BookingStage.WAITING_FOR_THE_CLUB,
    BookingState.WAITING_FOR_A_PAYMENT: BookingStage.WAITING_FOR_A_PAYMENT,
    BookingState.BOOKED: BookingStage.BOOKED,
    BookingState.SEAT_OPEN: BookingStage.SEAT_OPEN,
    BookingState.CALLED_OFF: BookingStage.CALLED_OFF,
}

_CALLED_OFF = {
    CalledOff.REFUSED: CalledOffReason.REFUSED,
    CalledOff.NO_ANSWER: CalledOffReason.NO_ANSWER,
    CalledOff.SHORT_AT_THE_CUT_OFF: CalledOffReason.SHORT_AT_THE_CUT_OFF,
    CalledOff.CANCELLED_BY_THE_CLUB: CalledOffReason.CANCELLED_BY_THE_CLUB,
    CalledOff.PAYMENT_NOT_IN_TIME: CalledOffReason.PAYMENT_NOT_IN_TIME,
}

_CANCEL_REASONS = {
    CancelReason.WEATHER: ClubCancelReason.WEATHER,
    CancelReason.REPAIR: ClubCancelReason.REPAIR,
    CancelReason.DOUBLE_BOOKING: ClubCancelReason.DOUBLE_BOOKING,
    CancelReason.OTHER: ClubCancelReason.OTHER,
}


def _booked_game(booking: Booking, *, for_the_club: bool = False) -> BookedGame:
    """The game a booking is to its players — a request taken back because a
    seat opened, or because the payment the club's yes waited on did not come
    (#626), is a game gone back to filling (``FILLING_AGAIN``), the people still
    In as the booking left them: Proposals folds it against the proposal
    (``as_filling_again``). **To its club** a request taken back is nothing
    (#624), and one whose payment did not come is called off (#626, Q112)."""

    filling_again = booking.taken_back and not for_the_club
    return BookedGame(
        booking_id=booking.booking_id,
        pool_id=booking.pool_id,
        club_id=booking.club_id,
        court_name=booking.court.name,
        sport=booking.sport,
        kind=booking.kind,
        start=booking.start,
        share_grosze=booking.share_grosze,
        first_side=booking.first_side,
        second_side=booking.second_side,
        cut_off=booking.cut_off,
        game_id=booking.game_id,
        stage=BookingStage.FILLING_AGAIN if filling_again else _STAGES[booking.state],
        called_off=(
            None
            if booking.called_off is None or filling_again
            else _CALLED_OFF[booking.called_off]
        ),
        short_from=booking.short_from,
        open=tuple(_open_seat(left) for left in booking.open_departures),
        leavers=booking.leavers,
        said_no=booking.said_no,
        cancel_reason=(
            None
            if booking.cancel_reason is None
            else _CANCEL_REASONS[booking.cancel_reason]
        ),
        answer_by=booking.answer_by,
        version=booking.version,
        paying={
            **(
                {}
                if booking.pay_by is None
                else {payer: booking.pay_by for payer in booking.payers}
            ),
            # A booked game whose holding was refused (#639): the payer's own
            # time to fix the card.
            **booking.fixing_until,
        },
        time_to=(
            TimeTo.FIX_THE_CARD
            if booking.cards_to_fix
            or (booking.pay_by is not None and booking.to_fix_the_card)
            else TimeTo.PAY
            if booking.pay_by is not None
            else None
        ),
        booked_at=booking.booked_at,
        cancelled_at=booking.cancelled_at,
        cards_to_fix={
            player: RefusedHolding(
                until=to_fix.until,
                seat_charge_id=to_fix.seat_charge_id,
                reason=ReopenReason(to_fix.reason),
            )
            for player, to_fix in booking.cards_to_fix.items()
        },
        kept={
            player: KeptSeat(
                until=kept.until,
                seat_charge_id=kept.seat_charge_id,
                reason=ReopenReason(kept.reason),
                time_to=TimeTo.FIX_THE_CARD if kept.to_fix_the_card else TimeTo.PAY,
            )
            for player, kept in booking.kept.items()
        },
        keeps_ran_out=booking.keeps_ran_out,
    )


def _open_seat(left: Departure) -> OpenSeat:
    """A leaver's seat, in this context's words."""

    return OpenSeat(side=left.side, left_by=left.player_id, left_at=left.at)


@final
class BookingsClubBookings:
    def __init__(
        self,
        *,
        bookings: BookingRepository,
        directory: BookingDirectory,
        move: MoveTheBooking,
        cancel: CancelTheBooking,
    ) -> None:
        self._bookings = bookings
        self._directory = directory
        self._move = move
        self._cancel = cancel

    async def on_day(
        self, club_id: UUID, *, start: Instant, end: Instant
    ) -> Sequence[BookedGame]:
        found: list[BookedGame] = []
        for booking_id in await self._directory.at_club(club_id, start=start, end=end):
            booking = await self._bookings.load(booking_id)
            # A request taken back is no booking of the club's: the game is
            # filling again (#624). One whose payment did not come in time is
            # called off at its club (#626).
            if booking is not None and booking.called_off is not CalledOff.SEAT_OPENED:
                found.append(_booked_game(booking, for_the_club=True))
        return found

    async def free_courts(self, booking_id: UUID) -> Sequence[CourtToMoveTo]:
        return [
            CourtToMoveTo(court_id=court.court_id, name=court.name)
            for court in await self._move.free_courts(booking_id)
        ]

    async def move(
        self, booking_id: UUID, court_id: UUID, *, at: Instant
    ) -> CourtToMoveTo | None:
        try:
            court = await self._move.execute(booking_id, court_id, at=at)
        except CourtTaken as taken:
            raise CourtJustTaken() from taken
        return None if court is None else CourtToMoveTo(court.court_id, court.name)

    async def cancel(
        self, booking_id: UUID, *, because: ClubCancelReason, at: Instant
    ) -> ClubCancellation:
        cancelled = await self._cancel.execute(
            booking_id, CancelReason(because.value), at=at
        )
        return ClubCancellation(
            still_in=cancelled.still_in, refunded=cancelled.refunded
        )


@final
class BookingsGroupBornGames:
    def __init__(self, directory: BookingDirectory) -> None:
        self._directory = directory

    async def born_in(self, group_ids: Collection[UUID]) -> Mapping[UUID, int]:
        return await self._directory.counted_in(group_ids)

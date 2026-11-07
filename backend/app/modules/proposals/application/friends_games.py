"""**A friends game: sent, it books the court at once; its friends answer with
their money** (#751; ``docs/adr/0202`` §5–§6; the friends mechanics §8–§9,
§11.2).

**The send** (``SendAFriendsGame``) reads the line-up exactly as the friends
card does (``ReadFriendsLineUp``, #750), so the card and the send cannot
disagree, then asks what the send sheet's button asks, in its order: a saved
payment method, **at most 2 friends games waiting for answers**, the sender's
own hour and week free — then the court the card named, still free. **The
court is claimed first** (``FriendsGameBookings``), under an id of its own, so
a court somebody took a second earlier is ``court_just_taken`` before anybody's
bank is asked. **Then the money, all or nothing, with the sender present**:
their share and a **cover** for each other seat, held on their card
(``SendersCourts``). Every hold in, the booking stands — its Game and chat open
with the sender on it — and the sender's other yeses at that hour are
withdrawn, a full week pausing the rest, as a fill does. **A refused card books
nothing**: the claim is undone, and the same holds asked again under the same
keys — answered the same — are recorded as refused, each the sender's to
confirm in the app; sent again with the same ``booking_id``, the send takes
what they confirmed.

**An invited friend answers** (``AcceptAFriendsGame``, ``DeclineAFriendsGame``)
— within their 24 hours,
never past the cut-off: **accepting** is refused for a full week or a game at
that hour, holds their own share with them present under *Split the cost*
(nothing under *Whole court*), seats them, and withdraws their other yeses at
the hour; a refused card leaves the seat theirs to retry until their clock
ends. **Declining** empties the seat. **Silence runs out** by the invitations
job (``RunOutTheInvitations``). The sender is told either way, and the last seat
taken is *It's a game!* to all four — Notifications', off the booking's events.

**The sender may call it off before the cut-off** (``CallOffAFriendsGame``):
every hold and cover let go, everybody told, the court the club's again.

**Its empty seats** (#752; the friends mechanics §10–§11): anybody In
**invites** one of their own friends into one (``InviteIntoASeat``) — refused,
naming nobody, for a block, no level, a game at that hour or a full week —
and the first accept, or the first rescue, takes it; **the sender opens** one
to the group before the cut-off (``OpenASeat``), a rescue from then on; **the
cover warning** (``WarnTheCovers``) tells a *Split* sender once, a day before
the cut-off, what it will take for seats still without their own payment.
Leaving and the cut-off are ``leave_the_game.py``'s and ``cut_off.py``'s.

**Every act locks the booking's own row first** — no proposal stands for a
friends game — and commits once.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import SPORT_SPECS, Clock, Instant, instant
from app.modules.bookings.domain.booking import invited_until
from app.modules.proposals.application.commands import (
    FriendsGameCommand,
    SeatActCommand,
    SendAFriendsGameCommand,
)
from app.modules.proposals.application.answers import JoinsARescue, YesAnswer
from app.modules.proposals.application.fill import Booked, Fill
from app.modules.proposals.application.friends_card import ReadFriendsLineUp
from app.modules.proposals.application.members import ReadMembers
from app.modules.proposals.application.rescues import the_seat_paid_back
from app.modules.proposals.domain.deck import cut_off_of, hour_taken, week_of
from app.modules.proposals.domain.errors import (
    AlreadyOnTheGame,
    BookingIsCalledOff,
    BookingNotFound,
    CannotPlayTogether,
    CourtHourNotForSale,
    CourtJustTaken,
    CutOffHasPassed,
    FriendPlaysThen,
    FriendsGamesWaiting,
    FriendsWeekIsFull,
    GameHasStarted,
    GamesPerWeekBooked,
    InvitationNotWaiting,
    NoLevel,
    NotAFriend,
    PaymentMethodRequired,
    RescueNotOffered,
    SeatJustTaken,
    YouPlayThen,
)
from app.modules.proposals.domain.friends_card import court_at, the_sides, ways_to_stand
from app.modules.proposals.domain.home import (
    BookedGame,
    InvitationAnswer,
    PayMode,
    SeatState,
)
from app.modules.proposals.domain.limits import FRIENDS_GAMES_WAITING
from app.modules.proposals.domain.ports import (
    BalanceForecasts,
    BookableCourt,
    BookedGameChanges,
    CardsToFix,
    ClubTerms,
    FriendsGame,
    FriendsGameBookings,
    GameToCharge,
    PlayerBookings,
    PlayerFit,
    ReaderRelations,
    RefundReason,
    RefusedPayment,
    SavedMethods,
    SeatCharges,
    SeatRefunds,
    SendersCourt,
    SendersCourts,
    UndecidedCharges,
)
from app.modules.proposals.domain.proposer import Member, capped_weeks_of
from app.shared.ids import new_uuid

# --------------------------------------------------------------------------- #
# Sending
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class FriendsGameSent:
    """What a send did: the game booked — its booking and Game — or nothing
    booked, and the sender's payments to confirm before sending again under
    the same ``booking_id``."""

    booking_id: UUID
    booked: Booked | None = None
    your_payments: tuple[RefusedPayment, ...] = ()


@final
class SendAFriendsGame:
    def __init__(
        self,
        *,
        line_up: ReadFriendsLineUp,
        forecasts: BalanceForecasts,
        terms: ClubTerms,
        methods: SavedMethods,
        friends_games: FriendsGameBookings,
        bookings: PlayerBookings,
        courts: SendersCourts,
        fill: Fill,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._line_up = line_up
        self._forecasts = forecasts
        self._terms = terms
        self._methods = methods
        self._friends_games = friends_games
        self._bookings = bookings
        self._courts = courts
        self._fill = fill
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SendAFriendsGameCommand) -> FriendsGameSent:
        now = instant(self._clock.now())
        sender = command.line_up.player_id
        if command.booking_id is not None:
            sent = await self._sent_already(command.booking_id, sender)
            if sent is not None:
                return sent
        read = await self._line_up.read(command.line_up, now=now)
        options = ways_to_stand(read.line_up)
        sides, _ = the_sides(
            read.line_up,
            options,
            await self._forecasts.forecasts(options, sport=read.sport),
            partner=command.partner_id,
        )
        # The button's guards, in its order.
        if not await self._methods.saved_for(sender):
            raise PaymentMethodRequired()
        if (
            await self._friends_games.waiting_of(sender, now=now)
            >= FRIENDS_GAMES_WAITING
        ):
            raise FriendsGamesWaiting(cap=FRIENDS_GAMES_WAITING)
        _refuse_unless_free(
            next(p for p in read.people if p.player_id == sender),
            start=command.starts_at,
            now=now,
        )
        court = court_at(read.courts, command.court_id, command.starts_at)
        if court is None:
            # The card named it free a moment ago: another game took it.
            raise CourtJustTaken()
        terms = (await self._terms.of([court.club_id], now=now)).get(court.club_id)
        if terms is None:
            raise CourtHourNotForSale()
        cut_off = cut_off_of(court.start, cut_off_hours=terms.cut_off_hours)
        booking_id = command.booking_id or new_uuid()
        on_the_card = SendersCourt(
            booking_id=booking_id,
            club_id=court.club_id,
            sport=read.sport,
            start=court.start,
            share_grosze=court.share_grosze,
            court_name=court.court.name,
            seats=SPORT_SPECS[read.sport].players,
            pay_mode=command.pay_mode,
            free_to_leave_until=cut_off if now < cut_off else None,
            covers_until=None
            if now < cut_off
            else invited_until(now, cut_off=cut_off, start=court.start),
        )
        try:
            # The court first: a court gone is refused before any bank is asked.
            game_id = await self._friends_games.book(
                FriendsGame(
                    booking_id=booking_id,
                    pool_id=read.pool_id,
                    club_id=court.club_id,
                    sport=read.sport,
                    kind=command.kind,
                    start=court.start,
                    share_grosze=court.share_grosze,
                    sender=sender,
                    first_side=tuple(sides.yours),
                    second_side=tuple(sides.theirs),
                    pay_mode=command.pay_mode,
                    court=BookableCourt(
                        court_id=court.court.court_id,
                        name=court.court.name,
                        indoor=court.court.indoor,
                        cut_off=cut_off,
                    ),
                ),
                at=now,
            )
        except CourtJustTaken:
            # Spent, and nothing was asked of the sender's bank.
            await self._uow.rollback()
            raise
        held = await self._courts.hold(on_the_card, sender, at=now)
        if held.refused:
            # A refused card books nothing: the claim is undone, and the same
            # holds — the same keys, answered the same — recorded as refused.
            await self._uow.rollback()
            refused = await self._courts.refused(on_the_card, sender, at=now)
            await self._uow.commit()
            return FriendsGameSent(booking_id=booking_id, your_payments=refused.refused)
        await self._fill.other_yeses(
            [sender], booked_id=booking_id, start=court.start, now=now
        )
        await self._uow.commit()
        return FriendsGameSent(
            booking_id=booking_id, booked=Booked(booking_id=booking_id, game_id=game_id)
        )

    async def _sent_already(
        self, booking_id: UUID, sender: UUID
    ) -> FriendsGameSent | None:
        """A send retried after it booked is answered what it booked; somebody
        else's id is nobody's."""

        game = await self._bookings.find(booking_id)
        if game is None:
            return None
        if game.sender != sender or game.game_id is None:
            raise BookingNotFound()
        return FriendsGameSent(
            booking_id=booking_id,
            booked=Booked(booking_id=booking_id, game_id=game.game_id),
        )


def _refuse_unless_free(person: Member, *, start: Instant, now: Instant) -> None:
    """*One game per hour*, then *games per week* — the posting's own two."""

    if hour_taken(start, person.booked):
        raise YouPlayThen()
    week = week_of(start)
    if week in capped_weeks_of(person, now=now):
        raise GamesPerWeekBooked(
            games_per_week=person.limits.games_per_week, week=week.isoformat()
        )


# --------------------------------------------------------------------------- #
# Answering
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class FriendsGameAnswer:
    """What an accept did: the friend In — and whether that made the game
    whole — or, with *Split the cost*, their share refused and the seat still
    theirs to take until their invitation ends."""

    booking_id: UUID
    accepted: bool
    #: Every seat is taken now: *It's a game!*.
    whole: bool = False
    your_payment: RefusedPayment | None = None
    #: Until when the seat stays theirs to retry, with ``your_payment``.
    confirm_by: Instant | None = None


@final
class Accepting:
    """**The accept itself** (#751), on a friends game its caller has locked —
    the route's (``AcceptAFriendsGame``) and a refused share's confirmation's
    (``FriendsGameConfirmation``). **No commit.**"""

    def __init__(
        self,
        *,
        friends_games: FriendsGameBookings,
        members: ReadMembers,
        methods: SavedMethods,
        charges: SeatCharges,
        refunds: SeatRefunds,
        undecided: UndecidedCharges,
        fill: Fill,
    ) -> None:
        self._friends_games = friends_games
        self._members = members
        self._methods = methods
        self._charges = charges
        self._refunds = refunds
        self._undecided = undecided
        self._fill = fill

    async def locked(self, booking_id: UUID, player: UUID) -> BookedGame:
        """The friends game, its row locked — refused ``booking_not_found`` to
        anybody neither In nor invited: a stranger learns nothing about
        somebody's game."""

        return await _locked_for(self._friends_games, booking_id, player)

    async def accepted(
        self, game: BookedGame, player: UUID, *, now: Instant
    ) -> FriendsGameAnswer:
        if player in game.players:
            # In already: a second tap, or a confirmation arriving twice.
            return FriendsGameAnswer(
                booking_id=game.booking_id, accepted=True, whole=game.whole
            )
        seat = game.invited_now(player, now=now)
        if seat is None:
            _refuse_a_game_no_longer_on(game, now=now)
            raise InvitationNotWaiting()
        friend = (await self._members.of([player], sport=game.sport, now=now))[0]
        _refuse_unless_free(friend, start=game.start, now=now)
        # Invited into a seat open to the group (#752): taken from whoever
        # paid it, once theirs is paid.
        open_seat = next(
            (
                left
                for left in game.open
                if seat.seat_of is not None and left.left_by == seat.seat_of
            ),
            None,
        )
        taken: frozenset[UUID] = frozenset()
        if game.pay_mode is PayMode.SPLIT_THE_COST:
            if not await self._methods.saved_for(player):
                raise PaymentMethodRequired()
            charged = await self._charges.charge(
                GameToCharge(
                    proposal_id=game.booking_id,
                    club_id=game.club_id,
                    sport=game.sport,
                    start=game.start,
                    share_grosze=game.share_grosze,
                    court_name=game.court_name,
                    free_to_leave_until=game.cut_off if now < game.cut_off else None,
                    pay_by=seat.until,
                    accepting=True,
                ),
                [player],
                attempt=game.version,
                at=now,
            )
            refused = charged.refused.get(player)
            if refused is not None:
                # The seat stays theirs to retry until their clock ends.
                return FriendsGameAnswer(
                    booking_id=game.booking_id,
                    accepted=False,
                    your_payment=refused,
                    confirm_by=seat.until,
                )
            taken = frozenset(charged.taken.values())
        accepted = await self._friends_games.accept(game.booking_id, player, at=now)
        if open_seat is not None:
            if game.pay_mode is PayMode.SPLIT_THE_COST:
                # Their own share pays the seat now; with *Whole court* the
                # sender's still does, as he agreed.
                await the_seat_paid_back(self._refunds, game, open_seat, now=now)
            if not accepted.open:
                # The board is gone: a rescue's payment confirmed for a seat
                # here is let go, and nobody pays it.
                await self._undecided.release(game.booking_id, keeping=taken, at=now)
        await self._fill.other_yeses(
            [player], booked_id=game.booking_id, start=game.start, now=now
        )
        return FriendsGameAnswer(
            booking_id=game.booking_id, accepted=True, whole=accepted.whole
        )


@final
class AcceptAFriendsGame:
    """*Accept and pay 25 zł* — or *Accept*, with *Whole court* — on a FRIENDS
    GAME card (#751)."""

    def __init__(self, *, accepting: Accepting, uow: UnitOfWork, clock: Clock) -> None:
        self._accepting = accepting
        self._uow = uow
        self._clock = clock

    async def execute(self, command: FriendsGameCommand) -> FriendsGameAnswer:
        now = instant(self._clock.now())
        game = await self._accepting.locked(command.booking_id, command.player_id)
        answer = await self._accepting.accepted(game, command.player_id, now=now)
        await self._uow.commit()
        return answer


@final
class DeclineAFriendsGame:
    """*Not this time* on a FRIENDS GAME card (#751): the seat is empty, and a
    payment the friend was refused, or confirmed, for it is let go. A second
    tap records nothing."""

    def __init__(
        self,
        *,
        friends_games: FriendsGameBookings,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._friends_games = friends_games
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(self, command: FriendsGameCommand) -> None:
        now = instant(self._clock.now())
        game = await _locked_for(
            self._friends_games, command.booking_id, command.player_id
        )
        seat = game.invitation_of(command.player_id)
        if game.invited_now(command.player_id, now=now) is None:
            if seat is not None and seat.answer is InvitationAnswer.DECLINED:
                return
            _refuse_a_game_no_longer_on(game, now=now)
            raise InvitationNotWaiting()
        await self._friends_games.decline(game.booking_id, command.player_id, at=now)
        await self._undecided.release(
            game.booking_id, keeping=(), of_player=command.player_id, at=now
        )
        await self._uow.commit()


async def _locked_for(
    friends_games: FriendsGameBookings, booking_id: UUID, player: UUID
) -> BookedGame:
    game = await friends_games.locked(booking_id)
    if (
        game is None
        or not game.is_friends_game
        or (game.invitation_of(player) is None and player not in game.players)
    ):
        raise BookingNotFound()
    return game


def _refuse_a_game_no_longer_on(game: BookedGame, *, now: Instant) -> None:
    called_off = game.called_off_reason(now)
    if called_off is not None:
        raise BookingIsCalledOff(reason=called_off.value)
    if now >= game.start:
        raise GameHasStarted()


# --------------------------------------------------------------------------- #
# A payment confirmed in the app
# --------------------------------------------------------------------------- #


@final
class FriendsGameConfirmation:
    """*I confirmed my payment in the app*, on a friends game (#751) — the
    ``ConfirmPayment`` route's answer where no proposal stands for the game:

    - **before the court is booked**, the sender's hold refused at send: held
      now, the next send under the same ``booking_id`` takes it;
    - **an invited friend's share**: their accept again, on the share they
      confirmed — and, the seat no longer theirs or the game no longer on,
      the hold let go and the accept's refusal answered;
    - **a holding refused far ahead**, its card fixed in time: kept until the
      cut-off, as any seat's (#639).

    **No commit**, but for a refused accept: the hold confirmed for a seat that
    is no longer theirs is let go and committed before the refusal is raised,
    as ``ConfirmPayment`` lets a deck game's go."""

    def __init__(
        self,
        *,
        friends_games: FriendsGameBookings,
        accepting: Accepting,
        rescuer: JoinsARescue,
        cards: CardsToFix,
        games: BookedGameChanges,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
    ) -> None:
        self._friends_games = friends_games
        self._accepting = accepting
        self._rescuer = rescuer
        self._cards = cards
        self._games = games
        self._undecided = undecided
        self._uow = uow

    async def confirmed(
        self, game_id: UUID, player: UUID, *, confirmed: UUID, now: Instant
    ) -> YesAnswer | None:
        game = await self._friends_games.locked(game_id)
        if game is None:
            # A send's payment, confirmed before anything was booked.
            return YesAnswer(proposal_id=game_id, open_seats=0)
        if not game.is_friends_game:
            return None
        to_fix = game.cards_to_fix.get(player)
        if to_fix is not None and to_fix.seat_charge_id == confirmed:
            await self._cards.keep_fixed(confirmed, at=now)
            await self._games.card_fixed(game_id, player, at=now)
            return self._answered(game)
        if player in game.players:
            return self._answered(game)
        if game.invitation_of(player) is None:
            # Nobody invited them: a rescuer's payment, on a seat open to the
            # group (#752) — the join again.
            return await self._rescued(game, player, confirmed=confirmed, now=now)
        try:
            answer = await self._accepting.accepted(game, player, now=now)
        except (
            InvitationNotWaiting,
            BookingIsCalledOff,
            GameHasStarted,
            YouPlayThen,
            GamesPerWeekBooked,
        ):
            # Nobody pays a hold for a seat they cannot take.
            await self._undecided.release(game_id, keeping=(), of_player=player, at=now)
            await self._uow.commit()
            raise
        return YesAnswer(
            proposal_id=game_id,
            open_seats=0,
            booked=None
            if not answer.accepted or game.game_id is None
            else Booked(booking_id=game_id, game_id=game.game_id),
            your_payment=answer.your_payment,
            kept_until=answer.confirm_by,
        )

    async def _rescued(
        self, game: BookedGame, player: UUID, *, confirmed: UUID, now: Instant
    ) -> YesAnswer:
        try:
            return await self._rescuer.join(
                None, game.booking_id, player, now=now, confirmed=confirmed
            )
        except (
            SeatJustTaken,
            BookingIsCalledOff,
            GameHasStarted,
            RescueNotOffered,
            BookingNotFound,
        ):
            # Nobody pays a hold for a seat they cannot take.
            await self._undecided.release(
                game.booking_id, keeping=(), of_player=player, at=now
            )
            await self._uow.commit()
            raise

    @staticmethod
    def _answered(game: BookedGame) -> YesAnswer:
        return YesAnswer(
            proposal_id=game.booking_id,
            open_seats=0,
            booked=None
            if game.game_id is None
            else Booked(booking_id=game.booking_id, game_id=game.game_id),
        )


# --------------------------------------------------------------------------- #
# An empty seat (#752)
# --------------------------------------------------------------------------- #


async def _an_empty_seat(
    friends_games: FriendsGameBookings,
    game: BookedGame,
    seat_of: UUID,
    *,
    now: Instant,
) -> tuple[BookedGame, SeatState]:
    """The seat named ``seat_of`` while nobody holds it — or ``seat_just_taken``.
    A friend's time up and not yet run out is run out first, as the job would,
    so the seat is empty on the record as it reads."""

    seat = game.vacancy(seat_of, now=now)
    if seat is None:
        raise SeatJustTaken()
    invited = game.invitation_of(seat_of)
    if (
        invited is not None
        and invited.seat_of is None
        and invited.answer is InvitationAnswer.WAITING
    ):
        await friends_games.run_out(game.booking_id, at=now)
        again = await friends_games.locked(game.booking_id)
        assert again is not None
        game = again
    return game, seat.state


@final
class InviteIntoASeat:
    """***Invite a friend*** into an empty seat (#752; the friends mechanics
    §10.1, §10.3, Q44): anybody In, before or after the cut-off, invites one of
    **their own** friends — the same invitation and clock as the card's, 24
    hours never past the cut-off (or, made after it, the start). Refused,
    **naming nobody**: not their friend, no level in the sport, a block with
    anybody on the game, a game at that hour, a full week — and somebody
    already on the game or ever invited to it."""

    def __init__(
        self,
        *,
        friends_games: FriendsGameBookings,
        relations: ReaderRelations,
        members: ReadMembers,
        fit: PlayerFit,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._friends_games = friends_games
        self._relations = relations
        self._members = members
        self._fit = fit
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SeatActCommand) -> None:
        now = instant(self._clock.now())
        inviter, friend = command.player_id, command.friend_id
        assert friend is not None
        game = await _locked_for(self._friends_games, command.booking_id, inviter)
        if inviter not in game.players:
            # Only somebody In invites: an invitee still answering learns
            # nothing they may do.
            raise BookingNotFound()
        if not game.may_invite(inviter, now=now):
            _refuse_a_game_no_longer_on(game, now=now)
            raise BookingNotFound()
        if (
            friend in game.players
            or friend in game.leavers
            or game.invitation_of(friend) is not None
        ):
            raise AlreadyOnTheGame()
        if not await self._relations.friends_among(inviter, [friend]):
            raise NotAFriend()
        person = (await self._members.of([friend], sport=game.sport, now=now))[0]
        if person.level is None:
            raise NoLevel()
        # Everybody they would share the court with: those In, and every friend
        # still invited into another seat.
        others = {
            *game.players,
            *(
                seat.player_id
                for seat in game.invited
                if seat.waiting_at(now) and seat.seat != command.seat_of
            ),
        }
        blocked = await self._fit.blocked_pairs({*others, friend})
        if any(friend in pair for pair in blocked):
            raise CannotPlayTogether()
        if hour_taken(game.start, person.booked):
            raise FriendPlaysThen()
        if week_of(game.start) in capped_weeks_of(person, now=now):
            raise FriendsWeekIsFull()
        game, _ = await _an_empty_seat(
            self._friends_games, game, command.seat_of, now=now
        )
        await self._friends_games.invite(
            game.booking_id, friend, by=inviter, seat_of=command.seat_of, at=now
        )
        await self._uow.commit()


@final
class OpenASeat:
    """***Open to Ogrody*** (#752; the friends mechanics §10.1): the sender
    puts an empty seat to the group before the cut-off — from then on a rescue,
    offered as any rescue is: to members who fit, are free and aren't blocked,
    never to a guest. Opened already, nothing more is recorded."""

    def __init__(
        self, *, friends_games: FriendsGameBookings, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._friends_games = friends_games
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SeatActCommand) -> None:
        now = instant(self._clock.now())
        game = await self._friends_games.locked(command.booking_id)
        if (
            game is None
            or game.sender != command.player_id
            or command.player_id not in game.players
        ):
            raise BookingNotFound()
        _refuse_a_game_no_longer_on(game, now=now)
        if now >= game.cut_off:
            # Every seat still empty opened at the cut-off on its own.
            raise CutOffHasPassed()
        game, state = await _an_empty_seat(
            self._friends_games, game, command.seat_of, now=now
        )
        if state is SeatState.SEAT_OPEN:
            return
        await self._friends_games.open(game.booking_id, command.seat_of, at=now)
        await self._uow.commit()


@final
@dataclass(frozen=True, slots=True)
class CoverWarningsRun:
    """What one run of the cover warning recorded, and how many games another
    process reached first."""

    warned: int
    conflicts: int


@final
class WarnTheCovers:
    """**The cover warning** (#752; the friends mechanics §10.2, Q42): 24 hours
    before the cut-off of a *Split* game its sender covers from inside it, while
    a seat lacks its own payment, he is warned once what the cut-off will take
    — *Saturday 10:00 · 1 seat still empty · At Fri 10:00 you pay 50 zł* — by
    Notifications, off the booking's ``bookings.cover_warned``. **It buys the
    telling, not correctness**: the cut-off takes the covers whether or not it
    ran. One transaction per game, its row locked first, over a clock-derived
    list in one order on every process; the booking's own *once* refuses a
    second warning, and a conflict is counted and stepped over."""

    def __init__(
        self, *, friends_games: FriendsGameBookings, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._friends_games = friends_games
        self._uow = uow
        self._clock = clock

    async def execute(self) -> CoverWarningsRun:
        now = instant(self._clock.now())
        warned = conflicts = 0
        for booking_id in await self._friends_games.cover_warnings_due(now=now):
            try:
                if await self._friends_games.locked(
                    booking_id
                ) is not None and await self._friends_games.warn(booking_id, at=now):
                    await self._uow.commit()
                    warned += 1
                else:
                    await self._uow.rollback()
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return CoverWarningsRun(warned=warned, conflicts=conflicts)


# --------------------------------------------------------------------------- #
# The sender calls it off
# --------------------------------------------------------------------------- #


@final
class CallOffAFriendsGame:
    def __init__(
        self,
        *,
        friends_games: FriendsGameBookings,
        refunds: SeatRefunds,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._friends_games = friends_games
        self._refunds = refunds
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(self, command: FriendsGameCommand) -> None:
        now = instant(self._clock.now())
        game = await self._friends_games.locked(command.booking_id)
        if (
            game is None
            or game.sender != command.player_id
            # A sender who left calls nothing off for those playing on (#752).
            or command.player_id not in game.players
        ):
            raise BookingNotFound()
        _refuse_a_game_no_longer_on(game, now=now)
        if now >= game.cut_off:
            raise CutOffHasPassed()
        called_off = await self._friends_games.call_off(game.booking_id, at=now)
        # Every hold and cover let go: nothing was taken.
        await self._refunds.refund(
            game.booking_id,
            called_off.players,
            reason=RefundReason.CALLED_OFF_BY_THE_SENDER,
            at=now,
        )
        # And a payment an invitee confirmed, or was refused, for a seat they
        # never took.
        await self._undecided.release(game.booking_id, keeping=(), at=now)
        await self._uow.commit()


# --------------------------------------------------------------------------- #
# Silence runs out
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class InvitationsRun:
    """What one run of the invitations job recorded, and how many games
    another process reached first."""

    ran_out: int
    conflicts: int


@final
class RunOutTheInvitations:
    """**The invitations job** (#751): every invitation whose 24 hours ended
    with no answer is run out — *Not this time*, and the sender told *Ania
    didn't answer*. One transaction per game, its row locked first, over a
    clock-derived list in one order on every process, so two processes
    reaching one game meet at the lock or the stream version, and the second
    is counted and stepped over. Every read says *didn't answer* from the
    clock already; this records it, so the sender is told."""

    def __init__(
        self,
        *,
        friends_games: FriendsGameBookings,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._friends_games = friends_games
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(self) -> InvitationsRun:
        now = instant(self._clock.now())
        ran_out = conflicts = 0
        for booking_id in await self._friends_games.invitations_past(now=now):
            try:
                players = await self._run_out(booking_id, now=now)
                if not players:
                    await self._uow.rollback()
                    continue
                await self._uow.commit()
                ran_out += len(players)
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return InvitationsRun(ran_out=ran_out, conflicts=conflicts)

    async def _run_out(self, booking_id: UUID, *, now: Instant) -> Collection[UUID]:
        if await self._friends_games.locked(booking_id) is None:
            return ()
        players = await self._friends_games.run_out(booking_id, at=now)
        for player in players:
            await self._undecided.release(
                booking_id, keeping=(), of_player=player, at=now
            )
        return players


__all__ = [
    "AcceptAFriendsGame",
    "Accepting",
    "CoverWarningsRun",
    "InviteIntoASeat",
    "OpenASeat",
    "WarnTheCovers",
    "DeclineAFriendsGame",
    "FriendsGameConfirmation",
    "CallOffAFriendsGame",
    "FriendsGameAnswer",
    "FriendsGameSent",
    "InvitationsRun",
    "RunOutTheInvitations",
    "SendAFriendsGame",
]

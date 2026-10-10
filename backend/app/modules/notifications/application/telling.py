"""**Players are told, through the outbox, by contexts that do not know it**
(#549; the mechanics §6.3, §6.4, §9.2, §10.1, §12–§13, §17.2; the screens A9).

``proposals``, ``bookings`` and ``payments`` publish what happened to a game and
its money; this subscribes, as a room does (``docs/adr/0146`` §5), and asks them
nothing but reads. Each event is read against the game **as it stands** —
``GameBriefs``, at the event's own instant — so a game that moved on before the
delivery is told as it is, and a card that filled meanwhile needs nobody.

**The table** (``_TELLING``) — what each event tells, and whom:

- ``SeatChargeKept`` — *It's a game! · 30 zł held*, to the payer, the cut-off
  kept on the notice as when it is taken (#637, Q113); and ``SeatChargeTaken``
  at once after the cut-off — *It's a game! · you paid*; or *the club
  confirmed*, at an On request club's yes; or *booked*, on a game that booked
  on the payment it waited for (Q110). **The take at the cut-off tells
  nothing**: *It's a game!* was told when the share was held. **The payer whose
  own act booked the seat** — the yes that filled the game, the seat they took
  — saw *It's a game!* on their own screen, so theirs is **their own**: born
  seen, never counted nor pushed (the mechanics Q102).
- ``BookingRequested`` — *It's a game! · Kazimierz Padel answers by 21:15*,
  to the four, each time the game goes to its On request club; the player
  whose act put it there saw it happen, so theirs is their own (Q103).
- ``SeatChargeFailed`` — *Confirm your payment*, to the payer — *by 14:40*,
  while their time to pay runs (#625, #626); before the cut-off, where their
  time is to fix the card, *Fix your card by 14:40 to keep your seat* (#638).
- ``TimeToPayGiven`` — *It's a game! · waiting for one payment until 14:40*
  to everybody In but the payer, never naming them — *Your Fri 19:00 is
  waiting for one payment, until 21:20* at the club's yes; the player whose
  act filled it saw it happen, so theirs is their own (Q110).
- ``TimeToPayRanOut`` — *Your time to pay ran out* to the payer — *Your time
  to fix your card ran out*, before the cut-off (#638) — and *filling again*
  to everybody else still In; past the book-by, *called off · nobody paid* to
  them all (#625, #626).
- ``FellBackToFilling`` — a full game waiting for one payment falling back, at a
  club that books at once: as ``RequestWithdrawn`` is told (#625).
- ``PaymentNotInTime`` — a share refused at the club's yes with no time left:
  *called off · nobody paid* to everybody on it (#626).
- ``SeatChargeRefundDecided`` — *Game called off · with the refund*, to the
  refunded; never a leaver's own refund. A leaver the club's cancel refunds is
  told in a leaver's words (Q108).
- ``SeatChargeRefunded`` — a seat-taken refund, **told when it is made**
  (#641): *You've been refunded 38,24 zł · your seat was taken* / *40 zł less
  the 1,76 zł kept on your payment* — the sum is known to the grosz only then,
  since a fee not yet known makes the refund wait.
- ``SeatChargeReleased`` with a reason — a held share let go: *Game called off ·
  nothing was taken*, at the cut-off or the club's cancel before it (#637);
  never a leaver's own let-go.
- ``BookingRefused``, ``BookingTimedOut`` — *Kazimierz Padel said no* and
  *… didn't answer in time*, to everybody waiting on it (Q105).
- ``SeatLeft`` — *Someone left your game*, to everybody still seated; and *Fill
  in alerts*, to the pool the seat is offered to.
- ``CalledOffAtCutOff`` — to each leaver whose empty seat called it off, in a
  leaver's words: it counts on their record, and their refund stands (Q108).
- ``RequestWithdrawn`` — a full game falling back, to everybody still In
  (Q104): *Oscar Bertran left your game — it's filling again* for a yes taken
  back, *Your Fri 19:00 at Kazimierz Padel is filling again* for anything else,
  never saying whose week filled, who no longer fits or whose card failed —
  and, after the book-by, *Your Fri 19:00 is called off · nobody paid*.
- ``ProposalExpired`` — *Your post didn't fill*, to its poster, still In; and
  a full game gone back to filling, *called off · nobody paid*, to everybody
  still In.
- ``CourtHourLost`` — a full game gone back to filling, *called off · nobody
  paid*, to everybody still In. A card that never filled still goes untold.
- ``YesSaid``, ``YesResumed`` — *You complete it*, to the people named on the
  card whose yes would book it.
- ``VersionDealt`` on a post — *Challenges for you*, to the newly dealt.
- ``Redealt`` — *Your new game*, to the people a club's no, silence or cancel
  promised a new card first, on the card they were dealt (Q107). **Every
  other card the proposer deals tells nobody.**

**An alert never points at a card the reader cannot find**: *You complete it*,
a challenge and *Your new game* go only to a reader whose deck shows the card
now (``Decks``, the deck's own filters). **And *You complete it* is the named player's**
(§6.3: *the named player keeps two advantages … they get the You complete it
alert*) — never a next best fit dealt into the card after somebody's no.

**No notice is ever sent for a single swipe** (§6.1, §6.2): a yes tells nobody
*that* it was said — only, when it leaves one seat, the people named on the
card that it needs them; a no and a withdrawn yes tell nobody anything.

**Nothing here commits, and every write is idempotent**: the transaction is the
delivery's, and a notice's key — the delivered event for one that is always
on, the kind and the game for a chosen one — is told once.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Collection
from dataclasses import replace
from typing import Any, Final, final
from uuid import UUID

from app.application.events import DeliveryContext
from app.kernel import Instant, instant
from app.modules.bookings.domain.events import (
    BookingRefused,
    BookingRequested,
    BookingTimedOut,
    CalledOffAtCutOff,
    PaymentNotInTime,
    RequestWithdrawn,
    SeatLeft,
)
from app.modules.clubs.domain.court_hours import local_day
from app.modules.notifications.domain.notices import (
    CHOSEN,
    Notice,
    NoticeKind,
    NoticeReason,
    Opens,
)
from app.modules.notifications.domain.ports import (
    Decks,
    GameBrief,
    GameBriefs,
    NoticeDayRepository,
    NotificationPreferencesRepository,
    PaidShares,
    SeatOffers,
)
from app.modules.notifications.domain.preferences import NotificationChoice
from app.modules.payments.domain.events import (
    SeatChargeFailed,
    SeatChargeKept,
    SeatChargeRefundDecided,
    SeatChargeRefunded,
    SeatChargeReleased,
    SeatChargeTaken,
)
from app.modules.payments.domain.seat_charge import RefundReason
from app.modules.proposals.domain.events import (
    CourtHourLost,
    FellBackToFilling,
    ProposalExpired,
    Redealt,
    TimeToPayGiven,
    TimeToPayRanOut,
    VersionDealt,
    YesResumed,
    YesSaid,
)
from app.shared.domain import DomainEvent

#: A refund's reason, and what the player is told when it is decided — a
#: leaver's own refund is told nobody: it is their act, and its email says so.
#: **A seat-taken refund is told when it is made** (#641,
#: ``_seat_taken_refunded``): its sum is known to the grosz only then. ``None``
#: is the club's own reason for cancelling.
_REFUNDS: Final[dict[RefundReason, tuple[NoticeKind, NoticeReason | None]]] = {
    RefundReason.CALLED_OFF_AT_THE_CUT_OFF: (
        NoticeKind.GAME_CALLED_OFF,
        NoticeReason.SHORT_AT_THE_CUT_OFF,
    ),
    RefundReason.CANCELLED_BY_THE_CLUB: (NoticeKind.GAME_CALLED_OFF, None),
    RefundReason.CANCELLED_AFTER_YOU_LEFT: (NoticeKind.GAME_CALLED_OFF, None),
}


@final
class GiveNotice:
    """Tell one player one notice — **if they chose to be told**, for a chosen
    kind, and **as their day allows**: the day in Kraków the notice happened
    on, whose caps and bundling are ``NoticesOfADay``'s. **No commit.**"""

    def __init__(
        self,
        *,
        preferences: NotificationPreferencesRepository,
        days: NoticeDayRepository,
    ) -> None:
        self._preferences = preferences
        self._days = days

    async def execute(self, player_id: UUID, notice: Notice, *, at: Instant) -> None:
        chosen = CHOSEN.get(notice.kind)
        if chosen is not None:
            if not (await self._preferences.load(player_id)).wants(chosen.choice):
                return
        day = await self._days.load(player_id, local_day(at))
        if day.give(notice, at=at) is not None:
            await self._days.save(day)


def _notice(
    kind: NoticeKind,
    game: GameBrief,
    *,
    key: str,
    opens: Opens,
    amount_grosze: int | None = None,
    people: tuple[UUID, ...] = (),
    reason: str | None = None,
    own: bool = False,
    until: Instant | None = None,
    you_left: bool = False,
    kept_grosze: int | None = None,
) -> Notice:
    return Notice(
        kind=kind,
        key=key,
        game_id=game.game_id,
        pool_id=game.pool_id,
        sport=game.sport,
        game_kind=game.game_kind,
        club_id=game.club_id,
        starts_at=game.starts_at,
        opens=opens,
        amount_grosze=amount_grosze,
        people=people,
        reason=reason,
        own=own,
        until=until,
        you_left=you_left,
        kept_grosze=kept_grosze,
    )


@final
class TellThePlayers:
    """One handler for every event a player is told about."""

    def __init__(
        self,
        *,
        give: GiveNotice,
        games: GameBriefs,
        decks: Decks,
        shares: PaidShares,
        offers: SeatOffers,
        preferences: NotificationPreferencesRepository,
    ) -> None:
        self._give = give
        self._games = games
        self._decks = decks
        self._shares = shares
        self._offers = offers
        self._preferences = preferences

    async def __call__(self, event: DomainEvent, context: DeliveryContext) -> None:
        # Always on: the event is the news, so the delivered event is the key.
        await _TELLING[type(event)](
            self, event, key=str(context.event_id), at=instant(event.occurred_at)
        )

    async def _tell(
        self,
        players: Collection[UUID],
        notice: Notice,
        *,
        at: Instant,
        whose_act: UUID | None = None,
    ) -> None:
        """``whose_act`` is the player whose own act it tells: their copy is
        born seen (Q102)."""

        # In a stable order, so two processes take the day streams alike.
        for player in sorted(set(players), key=str):
            await self._give.execute(
                player,
                replace(notice, own=True) if player == whose_act else notice,
                at=at,
            )

    # -- the money ------------------------------------------------------------

    async def _seats_booked(
        self, event: SeatChargeKept | SeatChargeTaken, *, key: str, at: Instant
    ) -> None:
        """*It's a game!* — the share held until the cut-off, which the notice
        keeps as when it is taken (#637), or taken at once after it."""

        if isinstance(event, SeatChargeTaken) and event.kept:
            # Taken at the cut-off off a hold: it was told when it was held.
            return
        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked:
            return
        # At an On request club the seats are taken at the club's yes, and that
        # yes is the news: one notice, never two at once.
        confirmed = (
            game.asked_the_club and event.player_id not in game.seats_taken.values()
        )
        kind = NoticeKind.CLUB_CONFIRMED if confirmed else NoticeKind.GAME_BOOKED
        # Booked on the payment it waited for, it was *It's a game!* already
        # when it filled: *booked · you paid* now, never twice (Q110).
        # The payer whose payment booked it sees *It's a game!*: theirs says
        # so, and is their own.
        reason = (
            NoticeReason.PAYMENT_CAME_IN
            if kind is NoticeKind.GAME_BOOKED
            and game.booked_on_a_payment
            and event.player_id != game.filled_by
            and event.player_id not in game.seats_taken.values()
            else None
        )
        # Their own yes filled it, or they took the seat: it is no news to
        # them. The club's yes is the club's act, and news to all four.
        own = (
            event.player_id == game.filled_by
            or event.player_id in game.seats_taken.values()
        )
        await self._give.execute(
            event.player_id,
            _notice(
                kind,
                game,
                key=f"{kind}:{key}",
                opens=Opens.BOOKING,
                amount_grosze=game.share_grosze,
                reason=reason,
                own=own,
                until=instant(event.until)
                if isinstance(event, SeatChargeKept)
                else None,
            ),
            at=at,
        )

    async def _payment_refused(
        self, event: SeatChargeFailed, *, key: str, at: Instant
    ) -> None:
        game = await self._games.about(event.game_id, at=at)
        # A game over before this was delivered — called off at the club's yes
        # with no time left to pay (#626) — has nothing to confirm a payment
        # into: its call-off tells it.
        if game is None or not (game.booked or game.filling):
            return
        # A refused share on a booked game was a rescue's: confirming it takes
        # the seat, from the booking's details. Within their time to pay the
        # notice names it (#625, #626) — and before the cut-off, where their
        # time is to fix the card, says so (#638).
        until = game.paying.get(event.player_id)
        if until is not None and at >= until:
            until = None
        kind = (
            NoticeKind.FIX_YOUR_CARD
            if until is not None and event.player_id in game.fixing
            else NoticeKind.CONFIRM_PAYMENT
        )
        await self._give.execute(
            event.player_id,
            _notice(
                kind,
                game,
                # One key whichever words it takes, so a delivery retried
                # either side of a run-out tells it once.
                key=f"{NoticeKind.CONFIRM_PAYMENT}:{key}",
                opens=Opens.BOOKING if game.booked else Opens.PROPOSAL,
                amount_grosze=event.amount_grosze,
                reason=event.reason,
                until=until,
            ),
            at=at,
        )

    async def _waiting_for_a_payment(
        self, event: TimeToPayGiven, *, key: str, at: Instant
    ) -> None:
        """**The four matched, one payment missing** (#625, #626; Q110):
        everybody In but the payers is told the game waits for one payment and
        until when — never whose. Once per time to pay: two refused at one
        fill, or a payer refused again, tell nothing more. Only while the game
        still waits for it — a payment in, or a seat opened, before this was
        delivered is told by what came of it."""

        game = await self._games.about(event.proposal_id, at=at)
        until = instant(event.until)
        if (
            game is None
            or not game.waiting_for_a_payment
            or game.paying.get(event.player_id) != until
        ):
            return
        await self._tell(
            [player for player in game.in_ if player not in game.paying],
            _notice(
                NoticeKind.WAITING_FOR_A_PAYMENT,
                game,
                key=f"{NoticeKind.WAITING_FOR_A_PAYMENT}:{game.game_id}:{until}",
                opens=Opens.PROPOSAL,
                reason=NoticeReason.AT_THE_CLUBS_YES
                if event.at_the_clubs_yes
                else None,
                until=until,
            ),
            at=at,
            whose_act=event.filled_by,
        )

    async def _time_ran_out(
        self, event: TimeToPayRanOut, *, key: str, at: Instant
    ) -> None:
        """**Out of time** (#625, #626): the payers are told their seat is open
        to others, and theirs to take back while free — each in the words of
        what their time was for, to fix the card or to pay (#638); everybody
        else still In that the game is filling again, never whose payment it
        was. Past the book-by it can no longer fill: *called off · nobody paid*
        to them all."""

        game = await self._games.about(event.proposal_id, at=at)
        if game is None:
            return
        payers = tuple(event.player_ids)
        if at >= game.book_by:
            await self._payment_not_in_time(game, (*payers, *game.in_), key=key, at=at)
            return
        for kind, theirs in (
            (
                NoticeKind.TIME_TO_FIX_RAN_OUT,
                [player for player in payers if player in event.fixing],
            ),
            (
                NoticeKind.TIME_TO_PAY_RAN_OUT,
                [player for player in payers if player not in event.fixing],
            ),
        ):
            await self._tell(
                theirs,
                _notice(kind, game, key=f"{kind}:{key}", opens=Opens.PROPOSAL),
                at=at,
            )
        # Full again before this was delivered — booked, asked of its club, or
        # waiting for a payment once more — it is told by that.
        if game.waiting_for_the_club or game.booked or game.waiting_for_a_payment:
            return
        await self._tell(
            [player for player in game.in_ if player not in payers],
            _notice(
                NoticeKind.SOMEONE_LEFT,
                game,
                key=f"{NoticeKind.SOMEONE_LEFT}:{key}",
                opens=Opens.PROPOSAL,
                reason=NoticeReason.FELL_BACK,
            ),
            at=at,
        )

    async def _called_off_at_once(
        self, event: PaymentNotInTime, *, key: str, at: Instant
    ) -> None:
        """A share refused at the club's yes with no time left to pay — its
        book-by had come (#626): called off, nobody paid, to everybody on it.
        A time to pay that ran out is told by ``TimeToPayRanOut``."""

        if not event.at_once:
            return
        game = await self._games.about(event.booking_id, at=at)
        if game is None:
            return
        await self._payment_not_in_time(
            game, (*event.player_ids, *game.seated, *game.in_), key=key, at=at
        )

    async def _payment_not_in_time(
        self, game: GameBrief, players: Collection[UUID], *, key: str, at: Instant
    ) -> None:
        await self._tell(
            players,
            _notice(
                NoticeKind.GAME_CALLED_OFF,
                game,
                key=f"{NoticeKind.GAME_CALLED_OFF}:{key}",
                opens=Opens.PROPOSAL,
                reason=NoticeReason.PAYMENT_NOT_IN_TIME,
            ),
            at=at,
        )

    async def _refunded(
        self, event: SeatChargeRefundDecided, *, key: str, at: Instant
    ) -> None:
        told = (
            None if event.reason is None else _REFUNDS.get(RefundReason(event.reason))
        )
        if told is None:
            return
        kind, reason = told
        share = await self._shares.of(event.charge_id)
        game = None if share is None else await self._games.about(share.game_id, at=at)
        if share is None or game is None:
            return
        # A leaver the club's cancel refunds is told in a leaver's words, and
        # opens the game they left, which they no longer have a seat on (Q108).
        you_left = event.reason == RefundReason.CANCELLED_AFTER_YOU_LEFT
        await self._give.execute(
            event.player_id,
            _notice(
                kind,
                game,
                key=f"{kind}:{key}",
                opens=Opens.PROPOSAL if you_left else Opens.BOOKING,
                amount_grosze=share.refunded_grosze,
                # The club's cancel says the club's own reason.
                reason=reason if reason is not None else game.cancel_reason,
                you_left=you_left,
            ),
            at=at,
        )

    async def _seat_taken_refunded(
        self, event: SeatChargeRefunded, *, key: str, at: Instant
    ) -> None:
        """**A leaver whose seat was taken is told when the refund is made**
        (#641; the mechanics §13, Q113): *You've been refunded 38,24 zł · your
        seat was taken* / *40 zł less the 1,76 zł kept on your payment* — the
        sum and what was kept, both the provider's own. Every other refund was
        told when it was decided."""

        share = await self._shares.of(event.charge_id)
        if share is None or not share.seat_taken:
            return
        game = await self._games.about(share.game_id, at=at)
        if game is None:
            return
        await self._give.execute(
            event.player_id,
            _notice(
                NoticeKind.REFUNDED,
                game,
                key=f"{NoticeKind.REFUNDED}:{key}",
                opens=Opens.BOOKING,
                amount_grosze=share.refunded_grosze,
                kept_grosze=share.kept_grosze,
            ),
            at=at,
        )

    async def _let_go(
        self, event: SeatChargeReleased, *, key: str, at: Instant
    ) -> None:
        """**A held share let go is told as nothing taken** (#637, Q113): the
        game called off at its cut-off, or cancelled by its club before it.
        An undecided hold released at the fill tells nothing."""

        # What a refund would have told, but nothing was taken (#637): a
        # leaver's own let-go is told nobody — their act, and emailed — and so
        # is one whose seat was taken before the cut-off took their share.
        told = (
            None if event.reason is None else _REFUNDS.get(RefundReason(event.reason))
        )
        if told is None:
            return
        kind, reason = told
        share = await self._shares.of(event.charge_id)
        game = None if share is None else await self._games.about(share.game_id, at=at)
        if share is None or game is None:
            return
        you_left = event.reason == RefundReason.CANCELLED_AFTER_YOU_LEFT
        await self._give.execute(
            event.player_id,
            _notice(
                kind,
                game,
                key=f"{kind}:{key}",
                opens=Opens.PROPOSAL if you_left else Opens.BOOKING,
                # Nothing was taken, so nothing comes back.
                amount_grosze=None,
                reason=reason if reason is not None else game.cancel_reason,
                you_left=you_left,
            ),
            at=at,
        )

    # -- the club's answer ----------------------------------------------------

    async def _gone_to_the_club(
        self, event: BookingRequested, *, key: str, at: Instant
    ) -> None:
        game = await self._games.about(event.booking_id, at=at)
        answer_by = instant(event.answer_by)
        # Told while the game still waits on this very request: one taken back
        # or answered before this was delivered is told by what came of it.
        if game is None or game.answer_by != answer_by:
            return
        await self._tell(
            (*event.first_side, *event.second_side),
            _notice(
                NoticeKind.WAITING_FOR_THE_CLUB,
                game,
                key=f"{NoticeKind.WAITING_FOR_THE_CLUB}:{key}",
                opens=Opens.PROPOSAL,
                until=answer_by,
            ),
            at=at,
            whose_act=event.filled_by,
        )

    async def _turned_down(
        self, event: BookingRefused | BookingTimedOut, *, key: str, at: Instant
    ) -> None:
        game = await self._games.about(event.booking_id, at=at)
        if game is None:
            return
        answer = (
            NoticeReason.REFUSED
            if isinstance(event, BookingRefused)
            else NoticeReason.NO_ANSWER
        )
        await self._tell(
            game.seated,
            _notice(
                NoticeKind.CLUB_COULD_NOT_TAKE_IT,
                game,
                key=f"{NoticeKind.CLUB_COULD_NOT_TAKE_IT}:{key}",
                opens=Opens.PROPOSAL,
                reason=answer,
            ),
            at=at,
        )

    # -- somebody leaving -----------------------------------------------------

    async def _left(self, event: SeatLeft, *, key: str, at: Instant) -> None:
        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked:
            return
        # Whoever took the leaver's seat before this was delivered is not told
        # the seat they took was left.
        taken_by = game.seats_taken.get(event.player_id)
        await self._tell(
            [p for p in game.seated if p not in (event.player_id, taken_by)],
            _notice(
                NoticeKind.SOMEONE_LEFT,
                game,
                key=f"{NoticeKind.SOMEONE_LEFT}:{key}",
                opens=Opens.BOOKING,
                people=(event.player_id,),
                reason=NoticeReason.SEAT_OPEN,
            ),
            at=at,
        )
        await self._alert_the_pool(game, left=event.player_id, at=at)

    async def _alert_the_pool(
        self, game: GameBrief, *, left: UUID, at: Instant
    ) -> None:
        """*Fill in alerts*: everybody in the pool the open seat is offered to,
        who switched them on. Who switched them on is asked first, so a pool
        nobody asked to be alerted in is never read whole."""

        outside = {*game.seated, left}
        wanting = await self._preferences.wanting(
            NotificationChoice.FILL_IN_ALERTS,
            [p for p in await self._offers.pool_of(game.game_id) if p not in outside],
        )
        if not wanting:
            return
        await self._tell(
            await self._offers.offered_among(game.game_id, wanting, at=at),
            _notice(
                NoticeKind.FILL_IN_ALERT,
                game,
                key=f"{NoticeKind.FILL_IN_ALERT}:{game.game_id}",
                opens=Opens.BOOKING,
                amount_grosze=game.share_grosze,
            ),
            at=at,
        )

    async def _called_off_short(
        self, event: CalledOffAtCutOff, *, key: str, at: Instant
    ) -> None:
        """**A leaver is told only when it touches them** (Q108): each leaver
        whose empty seat called the game off at its cut-off — it counts on
        their record, and nothing was taken from them (#637, Q113) — or, for a
        share taken before they left, their refund stands. Everybody still in
        is told by their hold let go."""

        game = await self._games.about(event.booking_id, at=at)
        if game is None:
            return
        for leaver in game.left_it_short:
            share = await self._shares.of_player(game.game_id, leaver)
            await self._give.execute(
                leaver,
                _notice(
                    NoticeKind.GAME_CALLED_OFF,
                    game,
                    key=f"{NoticeKind.GAME_CALLED_OFF}:{key}",
                    # They have no seat on it: the game they left opens.
                    opens=Opens.PROPOSAL,
                    amount_grosze=None if share is None else share.refunded_grosze,
                    reason=NoticeReason.SHORT_AT_THE_CUT_OFF,
                    you_left=True,
                ),
                at=at,
            )

    async def _fell_back(
        self, event: RequestWithdrawn | FellBackToFilling, *, key: str, at: Instant
    ) -> None:
        """**A full game falls back, and everybody still In is told** (Q104):
        a seat opened while the club decided, so the request is off — or while
        the game waited for a payment, at a club that books at once (#625).
        Somebody who took their own yes back is named — *it's filling again*;
        any other seat opened by what happened to its player, which is never
        said. Past its book-by it can no longer fill: *called off · nobody
        paid*."""

        game_id = (
            event.booking_id
            if isinstance(event, RequestWithdrawn)
            else event.proposal_id
        )
        game = await self._games.about(game_id, at=at)
        # Full again before this was delivered — asked again, booked, or
        # waiting for a payment once more — it is told by that.
        if (
            game is None
            or game.waiting_for_the_club
            or game.booked
            or game.waiting_for_a_payment
        ):
            return
        opened = set(event.player_ids)
        # Still out by their own act; one who came back since is nobody's
        # departure.
        left = tuple(player for player in event.left if player in game.withdrawn)
        if at >= game.book_by:
            kind, reason = (
                NoticeKind.GAME_CALLED_OFF,
                NoticeReason.LEFT_AFTER_THE_BOOK_BY,
            )
        elif left:
            kind, reason = NoticeKind.SOMEONE_LEFT, NoticeReason.FILLING_AGAIN
        else:
            kind, reason = NoticeKind.SOMEONE_LEFT, NoticeReason.FELL_BACK
        await self._tell(
            [player for player in game.in_ if player not in opened],
            _notice(
                kind,
                game,
                key=f"{kind}:{key}",
                opens=Opens.PROPOSAL,
                people=left,
                reason=reason,
            ),
            at=at,
        )

    async def _expired(self, event: ProposalExpired, *, key: str, at: Instant) -> None:
        """A full game gone back to filling that reached its book-by first is
        called off, nobody paid, to everybody still In (Q104, Q106) — told
        already if it fell back after its book-by. Any other card that never
        filled goes untold, a post's poster but for *your post didn't fill*."""

        game = await self._games.about(event.proposal_id, at=at)
        if game is None:
            return
        if game.asked_the_club and game.fell_back_at is None:
            # Called off at its club's yes, no time left to pay (#626): told
            # then, and never as a post that did not fill.
            return
        if game.fell_back_at is None:
            await self._post_unfilled(game, key=key, at=at)
        elif game.fell_back_at < game.book_by:
            await self._fallen_back_ended(
                game, NoticeReason.BOOK_BY_PASSED, key=key, at=at
            )

    async def _court_lost(self, event: CourtHourLost, *, key: str, at: Instant) -> None:
        """A full game gone back to filling whose court went to another game
        first is called off, nobody paid (Q104). A card that never filled goes
        untold."""

        game = await self._games.about(event.proposal_id, at=at)
        if game is not None and game.paying and game.open_seats == 0:
            # It went while the game waited for a payment, at a club that
            # books at once (#625): the people In are dealt a new card first.
            await self._fallen_back_ended(
                game,
                NoticeReason.COURT_LOST_WAITING_FOR_A_PAYMENT,
                key=key,
                at=at,
            )
        elif game is not None and game.fell_back:
            await self._fallen_back_ended(
                game, NoticeReason.COURT_HOUR_LOST, key=key, at=at
            )

    async def _fallen_back_ended(
        self, game: GameBrief, reason: NoticeReason, *, key: str, at: Instant
    ) -> None:
        await self._tell(
            game.in_,
            _notice(
                NoticeKind.GAME_CALLED_OFF,
                game,
                key=f"{NoticeKind.GAME_CALLED_OFF}:{key}",
                opens=Opens.PROPOSAL,
                reason=reason,
            ),
            at=at,
        )

    async def _post_unfilled(self, game: GameBrief, *, key: str, at: Instant) -> None:
        if game.posted_by is None or game.posted_by not in game.in_:
            return
        await self._give.execute(
            game.posted_by,
            _notice(
                NoticeKind.POST_DID_NOT_FILL,
                game,
                key=f"{NoticeKind.POST_DID_NOT_FILL}:{key}",
                opens=Opens.PROPOSAL,
            ),
            at=at,
        )

    # -- the cards ------------------------------------------------------------

    async def _one_seat_left(
        self, event: YesSaid | YesResumed, *, key: str, at: Instant
    ) -> None:
        game = await self._games.about(event.proposal_id, at=at)
        if game is None or not game.filling or game.waiting_for_the_club:
            return
        if game.open_seats != 1:
            return
        if (
            isinstance(event, YesSaid)
            and event.player_id == game.posted_by
            and at == game.made_at
        ):
            # A post's own yes is its birth: the people it names are challenged
            # by it, which ``VersionDealt`` tells.
            return
        await self._tell(
            await self._decks.showing(game.game_id, game.named, at=at),
            _notice(
                NoticeKind.YOU_COMPLETE_IT,
                game,
                key=f"{NoticeKind.YOU_COMPLETE_IT}:{game.game_id}",
                opens=Opens.DECK,
            ),
            at=at,
        )

    async def _new_card(self, event: Redealt, *, key: str, at: Instant) -> None:
        """The card first a club's no, silence or cancel promised: told to
        those it was promised to, on the card they find on top of the deck."""

        if event.card_id is None:
            return
        card = await self._games.about(event.card_id, at=at)
        if card is None or not card.filling:
            return
        await self._tell(
            await self._decks.showing(card.game_id, event.player_ids, at=at),
            _notice(
                NoticeKind.NEW_GAME,
                card,
                key=f"{NoticeKind.NEW_GAME}:{key}",
                opens=Opens.DECK,
                amount_grosze=card.share_grosze,
            ),
            at=at,
        )

    async def _dealt(self, event: VersionDealt, *, key: str, at: Instant) -> None:
        game = await self._games.about(event.proposal_id, at=at)
        if game is None or game.posted_by is None:
            return
        if not game.filling or game.waiting_for_the_club:
            return
        dealt = [player for player in event.player_ids if player in game.undecided]
        poster = (game.posted_by,) if game.posted_by in game.in_ else ()
        await self._tell(
            await self._decks.showing(game.game_id, dealt, at=at),
            _notice(
                NoticeKind.CHALLENGE,
                game,
                key=f"{NoticeKind.CHALLENGE}:{game.game_id}",
                opens=Opens.DECK,
                people=poster,
            ),
            at=at,
        )


_Telling = Callable[..., Awaitable[None]]

#: Every event a player is told about, and how — the one list, so what is
#: subscribed and what is handled cannot drift apart.
_TELLING: Final[dict[type[Any], _Telling]] = {
    SeatChargeKept: TellThePlayers._seats_booked,
    SeatChargeTaken: TellThePlayers._seats_booked,
    BookingRequested: TellThePlayers._gone_to_the_club,
    SeatChargeFailed: TellThePlayers._payment_refused,
    TimeToPayGiven: TellThePlayers._waiting_for_a_payment,
    TimeToPayRanOut: TellThePlayers._time_ran_out,
    FellBackToFilling: TellThePlayers._fell_back,
    PaymentNotInTime: TellThePlayers._called_off_at_once,
    SeatChargeRefundDecided: TellThePlayers._refunded,
    SeatChargeRefunded: TellThePlayers._seat_taken_refunded,
    SeatChargeReleased: TellThePlayers._let_go,
    BookingRefused: TellThePlayers._turned_down,
    BookingTimedOut: TellThePlayers._turned_down,
    SeatLeft: TellThePlayers._left,
    CalledOffAtCutOff: TellThePlayers._called_off_short,
    RequestWithdrawn: TellThePlayers._fell_back,
    ProposalExpired: TellThePlayers._expired,
    CourtHourLost: TellThePlayers._court_lost,
    YesSaid: TellThePlayers._one_seat_left,
    YesResumed: TellThePlayers._one_seat_left,
    VersionDealt: TellThePlayers._dealt,
    Redealt: TellThePlayers._new_card,
}

#: What ``subscribe_the_teller`` hears.
TOLD_ABOUT: Final[tuple[type[Any], ...]] = tuple(_TELLING)

"""**Players are told, through the outbox, by contexts that do not know it**
(#549; the mechanics §6.3, §6.4, §9.2, §10.1, §12–§13, §17.2; the screens A9).

``proposals``, ``bookings`` and ``payments`` publish what happened to a game and
its money; this subscribes, as a room does (``docs/adr/0146`` §5), and asks them
nothing but reads. Each event is read against the game **as it stands** —
``GameBriefs``, at the event's own instant — so a game that moved on before the
delivery is told as it is, and a card that filled meanwhile needs nobody.

**The table** (``_TELLING``) — what each event tells, and whom:

- ``SeatChargeTaken`` — *It's a game! · you paid*, to the payer; or *the club
  confirmed*, at an On request club's yes. **The payer whose own act booked the
  seat** — the yes that filled the game, the seat they took — saw *It's a game!*
  on their own screen, so theirs is **their own**: born seen, never counted nor
  pushed (the mechanics Q102).
- ``SeatChargeFailed`` — *Confirm your payment*, to the payer.
- ``SeatChargeRefundDecided`` — *Game called off · with the refund* or *You've
  been refunded*, to the refunded; never a leaver's own refund.
- ``BookingRefused``, ``BookingTimedOut`` — *The club couldn't take it*, to
  everybody waiting on it.
- ``SeatLeft`` — *Someone left your game*, to everybody still seated; and *Fill
  in alerts*, to the pool the seat is offered to.
- ``RequestWithdrawn`` — *Someone left your game*, to everybody still In, only
  for a yes taken back.
- ``ProposalExpired`` — *Your post didn't fill*, to its poster, still In.
- ``YesSaid``, ``YesResumed`` — *You complete it*, to the people named on the
  card whose yes would book it.
- ``VersionDealt`` on a post — *Challenges for you*, to the newly dealt.

**An alert never points at a card the reader cannot find**: *You complete it*
and a challenge go only to a reader whose deck shows the card now (``Decks``,
the deck's own filters). **And *You complete it* is the named player's**
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
from typing import Any, Final, final
from uuid import UUID

from app.application.events import DeliveryContext
from app.kernel import Instant, instant
from app.modules.bookings.domain.events import (
    BookingRefused,
    BookingTimedOut,
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
    SeatChargeRefundDecided,
    SeatChargeTaken,
)
from app.modules.payments.domain.seat_charge import RefundReason
from app.modules.proposals.domain.events import (
    ProposalExpired,
    VersionDealt,
    YesResumed,
    YesSaid,
)
from app.shared.domain import DomainEvent

#: A refund's reason, and what the player is told — a leaver's own refund is
#: told nobody: it is their act, and its email says so.
_REFUNDS: Final[dict[RefundReason, tuple[NoticeKind, NoticeReason | None]]] = {
    RefundReason.CALLED_OFF_AT_THE_CUT_OFF: (
        NoticeKind.GAME_CALLED_OFF,
        NoticeReason.SHORT_AT_THE_CUT_OFF,
    ),
    RefundReason.CANCELLED_BY_THE_CLUB: (NoticeKind.GAME_CALLED_OFF, None),
    RefundReason.SEAT_TAKEN: (NoticeKind.REFUNDED, None),
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
        self, players: Collection[UUID], notice: Notice, *, at: Instant
    ) -> None:
        # In a stable order, so two processes take the day streams alike.
        for player in sorted(set(players), key=str):
            await self._give.execute(player, notice, at=at)

    # -- the money ------------------------------------------------------------

    async def _seats_taken(
        self, event: SeatChargeTaken, *, key: str, at: Instant
    ) -> None:
        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked:
            return
        # At an On request club the seats are taken at the club's yes, and that
        # yes is the news: one notice, never two at once.
        confirmed = (
            game.asked_the_club and event.player_id not in game.seats_taken.values()
        )
        kind = NoticeKind.CLUB_CONFIRMED if confirmed else NoticeKind.GAME_BOOKED
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
                own=own,
            ),
            at=at,
        )

    async def _payment_refused(
        self, event: SeatChargeFailed, *, key: str, at: Instant
    ) -> None:
        game = await self._games.about(event.game_id, at=at)
        if game is None:
            return
        # A refused share on a booked game was a rescue's: confirming it takes
        # the seat, from the booking's details.
        await self._give.execute(
            event.player_id,
            _notice(
                NoticeKind.CONFIRM_PAYMENT,
                game,
                key=f"{NoticeKind.CONFIRM_PAYMENT}:{key}",
                opens=Opens.BOOKING if game.booked else Opens.PROPOSAL,
                amount_grosze=event.amount_grosze,
                reason=event.reason,
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
        await self._give.execute(
            event.player_id,
            _notice(
                kind,
                game,
                key=f"{kind}:{key}",
                opens=Opens.BOOKING,
                amount_grosze=share.refunded_grosze,
                # The club's cancel says the club's own reason.
                reason=reason if reason is not None else game.cancel_reason,
            ),
            at=at,
        )

    # -- the club's answer ----------------------------------------------------

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

    async def _left_while_waiting(
        self, event: RequestWithdrawn, *, key: str, at: Instant
    ) -> None:
        game = await self._games.about(event.booking_id, at=at)
        if game is None:
            return
        # A seat opens while the club decides because somebody left — or because
        # a share was refused at its yes, which is the refused player's to be
        # told and nobody's departure.
        leavers = tuple(p for p in event.player_ids if p in game.withdrawn)
        if not leavers:
            return
        await self._tell(
            [player for player in game.in_ if player not in event.player_ids],
            _notice(
                NoticeKind.SOMEONE_LEFT,
                game,
                key=f"{NoticeKind.SOMEONE_LEFT}:{key}",
                opens=Opens.PROPOSAL,
                people=leavers,
                reason=NoticeReason.FILLING_AGAIN,
            ),
            at=at,
        )

    async def _post_unfilled(
        self, event: ProposalExpired, *, key: str, at: Instant
    ) -> None:
        game = await self._games.about(event.proposal_id, at=at)
        if game is None or game.posted_by is None or game.posted_by not in game.in_:
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
    SeatChargeTaken: TellThePlayers._seats_taken,
    SeatChargeFailed: TellThePlayers._payment_refused,
    SeatChargeRefundDecided: TellThePlayers._refunded,
    BookingRefused: TellThePlayers._turned_down,
    BookingTimedOut: TellThePlayers._turned_down,
    SeatLeft: TellThePlayers._left,
    RequestWithdrawn: TellThePlayers._left_while_waiting,
    ProposalExpired: TellThePlayers._post_unfilled,
    YesSaid: TellThePlayers._one_seat_left,
    YesResumed: TellThePlayers._one_seat_left,
    VersionDealt: TellThePlayers._dealt,
}

#: What ``subscribe_the_teller`` hears.
TOLD_ABOUT: Final[tuple[type[Any], ...]] = tuple(_TELLING)

"""**Players are told, through the outbox, by contexts that do not know it**
(#549; the mechanics §6.3, §6.4, §9.2, §10.1, §12–§13, §17.2; the screens A9).

``proposals``, ``bookings``, ``payments`` and ``games`` publish what happened
to a game and its money, and ``friends`` a request and its answer; this
subscribes, as a room does (``docs/adr/0146`` §5), and asks them nothing but
reads. Each event is read against the game **as it
stands** — ``GameBriefs``, and for a game's own events its court (``GameCourts``),
at the event's own instant — so a game that moved on before the delivery is
told as it is, and a card that filled meanwhile needs nobody.

**The table** (``_TELLING``) — what each event tells, and whom:

- ``SeatChargeKept`` — *It's a game! · 30 zł held*, to the payer, the cut-off
  kept on the notice as when it is taken (#637, Q113); and ``SeatChargeTaken``
  at once after the cut-off — *It's a game! · you paid*; or *booked*, on a game
  that booked on the payment it waited for (Q110). **The take at the cut-off tells
  nothing**: *It's a game!* was told when the share was held. **The payer whose
  own act booked the seat** — the yes that filled the game, the seat they took
  — saw *It's a game!* on their own screen, so theirs is **their own**: born
  seen, never counted nor pushed (the mechanics Q102).
- ``SeatChargeFailed`` — *Confirm your payment*, to the payer — *by 14:40*,
  while their time to pay runs (#625); before the cut-off, where their
  time is to fix the card, *Fix your card by 14:40 to keep your seat* (#638) —
  and ``SeatChargeHoldingRefused`` the same, on a booked game whose holding
  was refused (#639). **A rescuer's**, the seat kept for them, *… by 14:40 to
  take the seat* (#640); ``KeptSeatRanOut`` tells them their time ran out and
  the seat is offered again — unless they took it in the same act.
  ``SeatChargeChecked`` is *It's a game!* as a hold kept is, free to leave
  until the cut-off all the same.
- ``TimeToPayGiven`` — *It's a game! · waiting for one payment until 14:40*
  to everybody In but the payer, never naming them; the player whose act
  filled it saw it happen, so theirs is their own (Q110).
- ``TimeToPayRanOut`` — *Your time to pay ran out* to the payer — *Your time
  to fix your card ran out*, before the cut-off (#638) — and *filling again*
  to everybody else still In; past the book-by, *called off · nobody paid* to
  them all (#625).
- ``FellBackToFilling`` — a full game waiting for one payment falling back, to
  everybody still In (#625, Q104): *Oscar Bertran left your game — it's
  filling again* for a yes taken back, *Your Fri 19:00 at Bonarka Arena is
  filling again* for anything else, never saying whose week filled, who no
  longer fits or whose card failed.
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
- ``SeatLeft`` — *Someone left your game*, to everybody still seated; and *Fill
  in alerts*, to the pool the seat is offered to. A seat let go because its
  card wasn't fixed at its holding (#639) tells its player *Your time to fix
  your card ran out*, and that they owe nothing.
- ``CalledOffAtCutOff`` — to each leaver whose empty seat called it off, in a
  leaver's words: it counts on their record, and their refund stands (Q108).
- ``CourtMoved`` — *Game moved*, to everybody with a seat on the booking: the
  court it is on now and its kind, and that nothing else changes (#671, Q122)
  — and, when a club's cancel moved it, why the court it left can't be played
  (#672). Always on, opening the booked game, never emailed.
- ``ProposalExpired`` — *Your post didn't fill*, to its poster, still In; and
  a full game gone back to filling, *called off · nobody paid*, to everybody
  still In.
- ``CourtHourLost`` — a full game gone back to filling, *called off · nobody
  paid*, to everybody still In. A card that never filled still goes untold.
- ``YesSaid``, ``YesResumed`` — *You complete it*, to the people named on the
  card whose yes would book it.
- ``VersionDealt`` on a post — *Challenges for you*, to the newly dealt.
- ``Redealt`` — *Your new game*, to the people a club's cancel promised a new
  card first, on the card they were dealt (Q107) — naming its kind of court
  when it is at the club and hour the cancel took (#673). **Every
  other card the proposer deals tells nobody.**
- ``AbsenceNoted`` — *Ivan is at Ogrody 33 and you're not there yet*, to the
  player tapped, while they are still awaited; ``ArrivalNoted`` — *Oscar is at
  Ogrody 33*, to whoever tapped *isn't here yet* about them (#663).
- ``PresenceClaimed`` — *Was Oscar at Ogrody 33?*, to everybody else on the
  court who may confirm it, while the claim waits.
- ``ResultProposed``, ``ResultCorrected``, ``ResultCountered`` — *Is that
  right?*, to those across the net whose agreement the score waits on. **Every
  one of these is a Competitive game's**: For fun asks nobody anything, and is
  told none of them; and each opens **the game's result screen**. *How did it
  go?* is no event's — a clock passing announces nothing — so ``asking.py``
  tells it when the hour ends.

- ``FriendRequested`` — *Inés wants to be your friend*, to the person asked,
  once per request and only while its card is on their Home; ``FriendsMade``
  — *Kuba said yes — you're friends* to whoever asked, *You and Kuba are
  friends now* to both when the requests crossed (#745). About no game; always
  on. *Not now*, a cancel, a removal and a block are told nobody.

- ``BookedByAFriend`` — *Tomek invited you to a game*, to each friend invited,
  opening Home on the card, ``until`` their 24 hours' end (#751).
  ``InvitedSeatDeclined`` and ``InvitedSeatRanOut`` — *Ania can't make it* / *Ania
  didn't answer*, to the sender. ``InvitedSeatAccepted`` that takes the last
  seat — *It's a game!*, to all four, the accepter's their own.
  ``CalledOffBySender`` — *Tomek called off Saturday 10:00 · Nobody paid.*, to
  everybody In and every friend still invited, the sender's own copy born
  seen. **A friends game's money tells
  nothing on its own**: the sender's holds at send and a friend's at their
  accept are their own acts, and *It's a game!* is the last seat taken. Every
  one always on, never emailed.

- ``LevelAsked`` — *Tomek wants to play padel with you.*, to the friend asked;
  ``LevelGot`` — *Zofia has a padel level — you can seat Zofia now.*, to the
  friend who asked, naming the group the ask was made from (#749). Both about
  no game, always on, and **only while the two are still friends**.

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
from app.kernel import Instant, Sport, instant
from app.modules.bookings.domain.events import (
    BookedByAFriend,
    CoverWarned,
    InvitedSeatTaken,
    SeatInvited,
    SeatOpened,
    CalledOffAtCutOff,
    CalledOffBySender,
    CourtMoved,
    InvitedSeatAccepted,
    InvitedSeatDeclined,
    InvitedSeatRanOut,
    KeptSeatRanOut,
    SeatLeft,
)
from app.modules.clubs.domain.court_hours import local_day
from app.modules.games.domain.events import (
    AbsenceNoted,
    ArrivalNoted,
    PresenceClaimed,
    ResultCorrected,
    ResultCountered,
    ResultProposed,
)
from app.modules.friends.domain.events import (
    FriendRequested,
    FriendsMade,
    LevelAsked,
    LevelGot,
)
from app.modules.friends.domain.relation import HowFriendsWereMade, RequestOrigin
from app.modules.notifications.domain.notices import (
    CHOSEN,
    Notice,
    NoticeKind,
    NoticeReason,
    Opens,
    friend_request_notice,
    friends_made_notice,
    level_asked_notice,
    level_got_notice,
)
from app.modules.notifications.domain.ports import (
    Friendships,
    WaitingRequest,
    CourtBrief,
    GameCourts,
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
    SeatChargeChecked,
    SeatChargeFailed,
    SeatChargeHoldingRefused,
    SeatChargeKept,
    SeatChargeRefundDecided,
    SeatChargeRefunded,
    SeatChargeReleased,
    SeatChargeTaken,
)
from app.modules.payments.domain.seat_charge import RefundReason
from app.modules.proposals.domain.events import (
    ClubCancelled,
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

#: How friends made by two requests crossing are recorded (#745).
CROSSED_REQUESTS: Final = HowFriendsWereMade.CROSSED.value

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

    async def execute(self, player_id: UUID, notice: Notice, *, at: Instant) -> bool:
        """Whether it was given — or gathered into the day's last of its kind."""

        chosen = CHOSEN.get(notice.kind)
        if chosen is not None:
            if not (await self._preferences.load(player_id)).wants(chosen.choice):
                return False
        day = await self._days.load(player_id, local_day(at))
        if day.give(notice, at=at) is None:
            return False
        await self._days.save(day)
        return True


def notice_about(
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
    rescue: bool = False,
    court_name: str | None = None,
    indoor: bool | None = None,
    moved_from: str | None = None,
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
        rescue=rescue,
        court_name=court_name,
        indoor=indoor,
        moved_from=moved_from,
    )


def _what_the_cover_takes(game: GameBrief, unpaid: Collection[UUID]) -> int:
    """What the cut-off takes from a *Split* sender (#752): his own share, and
    one for each seat still unpaid."""

    return game.share_grosze * (1 + len(unpaid))


@final
class TellThePlayers:
    """One handler for every event a player is told about."""

    def __init__(
        self,
        *,
        give: GiveNotice,
        games: GameBriefs,
        courts: GameCourts,
        decks: Decks,
        shares: PaidShares,
        offers: SeatOffers,
        preferences: NotificationPreferencesRepository,
        friendships: Friendships,
    ) -> None:
        self._give = give
        self._games = games
        self._courts = courts
        self._decks = decks
        self._shares = shares
        self._offers = offers
        self._preferences = preferences
        self._friendships = friendships

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

    # -- a friends game (#751) ------------------------------------------------

    async def _invited(self, event: BookedByAFriend, *, key: str, at: Instant) -> None:
        """*Tomek invited you to a game*, to each friend whose invitation
        still waits at the delivery — opening Home, on the card."""

        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked:
            return
        # The card's own friends: one invited into an empty seat since is told
        # by that invitation (#752).
        drawn = {*event.first_side, *event.second_side}
        await self._tell(
            [player for player in game.invited if player in drawn],
            notice_about(
                NoticeKind.FRIENDS_GAME_INVITATION,
                game,
                key=f"{NoticeKind.FRIENDS_GAME_INVITATION}:{key}",
                opens=Opens.HOME,
                people=(event.sender_id,),
                until=instant(event.invited_until),
            ),
            at=at,
        )

    async def _seat_answered(
        self,
        event: InvitedSeatDeclined | InvitedSeatRanOut,
        *,
        key: str,
        at: Instant,
    ) -> None:
        """*Ania can't make it* / *Ania didn't answer*, to the sender — an
        invitation into an empty seat's too, whoever made it (#752) — while the
        game is still on, the cover line inside the day before the cut-off.
        **A seat that opened by it** — after the cut-off, or on a game turned
        ordinary — alerts the pool as any rescue does."""

        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked or game.sender is None:
            return
        kind = (
            NoticeKind.CANT_MAKE_IT
            if isinstance(event, InvitedSeatDeclined)
            else NoticeKind.DIDNT_ANSWER
        )
        await self._give.execute(
            game.sender,
            self._with_the_cover_line(
                notice_about(
                    kind,
                    game,
                    key=f"{kind}:{key}",
                    opens=Opens.BOOKING,
                    people=(event.player_id,),
                ),
                game,
                to=game.sender,
            ),
            at=at,
        )
        # Nobody is offered a seat left empty: the alert reaches only a rescue.
        await self._alert_the_pool(game, left=event.player_id, at=at)

    @staticmethod
    def _with_the_cover_line(notice: Notice, game: GameBrief, *, to: UUID) -> Notice:
        """**The cover line** (#752; the friends mechanics §10.2): a seat that
        empties inside the day before the cut-off tells its *Split* sender what
        the cut-off will take — his share and every seat still unpaid — in the
        notice that tells him. Anybody else's notice is as it was."""

        if to != game.sender or not game.unpaid or game.cut_off is None:
            return notice
        return replace(
            notice,
            people=(*notice.people, *game.unpaid),
            amount_grosze=_what_the_cover_takes(game, game.unpaid),
            until=game.cut_off,
        )

    async def _seat_invited(self, event: SeatInvited, *, key: str, at: Instant) -> None:
        """*Piotr invited you to a game* — a friend invited into an empty seat
        (#752), whoever invited them named, while it still waits at the
        delivery: opening Home, on the card."""

        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked or event.player_id not in game.invited:
            return
        await self._give.execute(
            event.player_id,
            notice_about(
                NoticeKind.FRIENDS_GAME_INVITATION,
                game,
                key=f"{NoticeKind.FRIENDS_GAME_INVITATION}:{key}",
                opens=Opens.HOME,
                people=(event.invited_by,),
                until=instant(event.until),
            ),
            at=at,
        )

    async def _invited_seat_taken(
        self, event: InvitedSeatTaken, *, key: str, at: Instant
    ) -> None:
        """*Someone took that seat first.* (#752) — to the friend whose
        invitation into an empty seat ended so, naming nobody."""

        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked:
            return
        await self._give.execute(
            event.player_id,
            notice_about(
                NoticeKind.INVITED_SEAT_TAKEN,
                game,
                key=f"{NoticeKind.INVITED_SEAT_TAKEN}:{key}",
                opens=Opens.BOOKING,
            ),
            at=at,
        )

    async def _seat_opened(self, event: SeatOpened, *, key: str, at: Instant) -> None:
        """A friends game's seat put to the group (#752) is a rescue: *Fill in
        alerts* to everybody in the pool it is offered to, who switched them
        on — as a leaver's seat."""

        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked:
            return
        await self._alert_the_pool(game, left=event.seat_of, at=at)

    async def _cover_warned(self, event: CoverWarned, *, key: str, at: Instant) -> None:
        """**The cover warning** (#752): *Saturday 10:00 · 1 seat still empty*
        / *At Fri 10:00 you pay 50 zł: your 25 zł and Ania's seat.* — to the
        sender, while the game is on, opening it with its three actions."""

        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked or game.cut_off is None:
            return
        await self._give.execute(
            event.sender_id,
            notice_about(
                NoticeKind.COVER_WARNING,
                game,
                key=f"{NoticeKind.COVER_WARNING}:{key}",
                opens=Opens.BOOKING,
                people=event.seats,
                amount_grosze=_what_the_cover_takes(game, event.seats),
                until=game.cut_off,
            ),
            at=at,
        )

    async def _accepted(
        self, event: InvitedSeatAccepted, *, key: str, at: Instant
    ) -> None:
        """**The last seat taken** — *It's a game!*, to everybody on it; the
        friend who took it saw it on their own screen. An accept that leaves a
        seat to answer tells nobody."""

        if not event.last_seat:
            return
        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked:
            return
        await self._tell(
            game.seated,
            notice_about(
                NoticeKind.GAME_BOOKED,
                game,
                key=f"{NoticeKind.GAME_BOOKED}:{key}",
                opens=Opens.BOOKING,
                reason=NoticeReason.LAST_SEAT_TAKEN,
            ),
            at=at,
            whose_act=event.player_id,
        )

    async def _called_off_by_the_sender(
        self, event: CalledOffBySender, *, key: str, at: Instant
    ) -> None:
        """*Tomek called off Saturday 10:00 · Nobody paid.*, to everybody In
        and every friend still invited — the sender's own copy born seen, since
        it was their act (Q102)."""

        game = await self._games.about(event.booking_id, at=at)
        if game is None or game.sender is None:
            return
        await self._tell(
            (*event.player_ids, *event.invited),
            notice_about(
                NoticeKind.GAME_CALLED_OFF,
                game,
                key=f"{NoticeKind.GAME_CALLED_OFF}:{key}",
                opens=Opens.BOOKING,
                people=(game.sender,),
                reason=NoticeReason.BY_THE_SENDER,
            ),
            at=at,
            whose_act=game.sender,
        )

    # -- friends (#745) ---------------------------------------------------------

    async def _friend_request(
        self, event: FriendRequested, *, key: str, at: Instant
    ) -> None:
        """*{nickname} wants to be your friend*, to the person asked — **once per
        request**, and only while its card is on their Home: a request cancelled,
        answered or set aside before the delivery, or one the reader's own block
        hides, is told nobody (``docs/adr/0202`` §2)."""

        waiting = await self._friendships.waiting_on(event.addressee_id)
        if WaitingRequest(requester_id=event.requester_id, asked_at=at) not in waiting:
            return
        await self._give.execute(
            event.addressee_id,
            friend_request_notice(
                key=key,
                requester=event.requester_id,
                group_id=event.group_id,
                sport=None if event.sport is None else Sport(event.sport),
                by_link=event.made_from == RequestOrigin.LINK.value,
                from_the_ranking=event.made_from == RequestOrigin.RANKING.value,
                from_new_players=event.made_from == RequestOrigin.NEW_PLAYERS.value,
                from_same_level=event.made_from == RequestOrigin.SAME_LEVEL.value,
            ),
            at=at,
        )

    async def _friends_made(self, event: FriendsMade, *, key: str, at: Instant) -> None:
        """*{nickname} said yes — you're friends*, to whoever asked; *You and
        {nickname} are friends now* to both, when the requests crossed — while
        they still are."""

        if not await self._friendships.are_friends(
            event.requester_id, event.addressee_id
        ):
            return
        crossed = event.how == CROSSED_REQUESTS
        await self._give.execute(
            event.requester_id,
            friends_made_notice(key=key, friend=event.addressee_id, crossed=crossed),
            at=at,
        )
        if crossed:
            await self._give.execute(
                event.addressee_id,
                friends_made_notice(key=key, friend=event.requester_id, crossed=True),
                at=at,
            )

    async def _level_asked(self, event: LevelAsked, *, key: str, at: Instant) -> None:
        """*{asker} wants to play {sport} with you.*, to the friend asked — once
        per ask, and only while they are still friends: a friend removed or
        blocked before the delivery is told nothing (#749)."""

        if not await self._friendships.are_friends(event.asker_id, event.friend_id):
            return
        await self._give.execute(
            event.friend_id,
            level_asked_notice(key=key, asker=event.asker_id, sport=Sport(event.sport)),
            at=at,
        )

    async def _level_got(self, event: LevelGot, *, key: str, at: Instant) -> None:
        """*{friend} has a {sport} level — you can seat {friend} now.*, to the
        friend who asked, naming the group the ask was made from — only while
        they are still friends (#749)."""

        if not await self._friendships.are_friends(event.asker_id, event.friend_id):
            return
        await self._give.execute(
            event.asker_id,
            level_got_notice(
                key=key,
                friend=event.friend_id,
                sport=Sport(event.sport),
                group_id=event.group_id,
            ),
            at=at,
        )

    # -- the money ------------------------------------------------------------

    async def _seats_booked(
        self,
        event: SeatChargeKept | SeatChargeTaken | SeatChargeChecked,
        *,
        key: str,
        at: Instant,
    ) -> None:
        """*It's a game!* — the share held until the cut-off, which the notice
        keeps as when it is taken (#637), or taken at once after it — or only
        checked, far ahead of the cut-off, and free to leave until it the same
        (#639)."""

        if isinstance(event, SeatChargeTaken) and event.kept:
            # Taken at the cut-off off a hold: it was told when it was held.
            return
        if isinstance(event, SeatChargeKept) and event.fixed:
            # A card fixed at its holding, on a game told *It's a game!* when
            # it filled — the player's own act, on their own screen.
            return
        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked or game.is_friends_game:
            # A friends game's holds are its sender's and each friend's own
            # acts; *It's a game!* is its last seat taken (#751).
            return
        # Booked on the payment it waited for, it was *It's a game!* already
        # when it filled: *booked · you paid* now, never twice (Q110).
        # The payer whose payment booked it sees *It's a game!*: theirs says
        # so, and is their own.
        reason = (
            NoticeReason.PAYMENT_CAME_IN
            if game.booked_on_a_payment
            and event.player_id != game.filled_by
            and event.player_id not in game.seats_taken.values()
            else None
        )
        # Their own yes filled it, or they took the seat: it is no news to
        # them.
        own = (
            event.player_id == game.filled_by
            or event.player_id in game.seats_taken.values()
        )
        await self._give.execute(
            event.player_id,
            notice_about(
                NoticeKind.GAME_BOOKED,
                game,
                key=f"{NoticeKind.GAME_BOOKED}:{key}",
                opens=Opens.BOOKING,
                amount_grosze=game.share_grosze,
                reason=reason,
                own=own,
                until=instant(event.until)
                if isinstance(event, (SeatChargeKept, SeatChargeChecked))
                else None,
            ),
            at=at,
        )

    async def _payment_refused(
        self,
        event: SeatChargeFailed | SeatChargeHoldingRefused,
        *,
        key: str,
        at: Instant,
    ) -> None:
        game = await self._games.about(event.game_id, at=at)
        # A game over before this was delivered has nothing to confirm a
        # payment into: its ending tells it.
        if game is None or not (game.booked or game.filling):
            return
        # A refused share on a booked game was a rescue's: confirming it takes
        # the seat, from the booking's details — or its holding's (#639), the
        # card to fix by its time. Within their time to pay the notice names it
        # (#625) — and before the cut-off, where their time is to fix the
        # card, says so (#638).
        until = game.paying.get(event.player_id)
        if until is not None and at >= until:
            until = None
        kind = (
            NoticeKind.FIX_YOUR_CARD
            if until is not None and event.player_id in game.fixing
            else NoticeKind.CONFIRM_PAYMENT
        )
        # A seat they went for and do not hold: a rescue's, kept for them
        # while their time runs (#640).
        rescue = game.booked and event.player_id not in game.seated
        await self._give.execute(
            event.player_id,
            notice_about(
                kind,
                game,
                # One key whichever words it takes, so a delivery retried
                # either side of a run-out tells it once.
                key=f"{NoticeKind.CONFIRM_PAYMENT}:{key}",
                opens=Opens.BOOKING if game.booked else Opens.PROPOSAL,
                amount_grosze=event.amount_grosze,
                reason=event.reason,
                until=until,
                rescue=rescue,
            ),
            at=at,
        )

    async def _kept_seat_ran_out(
        self, event: KeptSeatRanOut, *, key: str, at: Instant
    ) -> None:
        """**A refused rescuer's time ran out** (#640): the seat is offered to
        others again — in the words of what their time was for — and still
        theirs to take while it is free. Not told to one who took it in the
        same act: their late confirmation ran it out, then took the seat."""

        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked or event.player_id in game.seated:
            return
        kind = (
            NoticeKind.TIME_TO_FIX_RAN_OUT
            if event.to_fix_the_card
            else NoticeKind.TIME_TO_PAY_RAN_OUT
        )
        await self._give.execute(
            event.player_id,
            notice_about(
                kind, game, key=f"{kind}:{key}", opens=Opens.BOOKING, rescue=True
            ),
            at=at,
        )

    async def _waiting_for_a_payment(
        self, event: TimeToPayGiven, *, key: str, at: Instant
    ) -> None:
        """**The four matched, one payment missing** (#625; Q110):
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
            notice_about(
                NoticeKind.WAITING_FOR_A_PAYMENT,
                game,
                key=f"{NoticeKind.WAITING_FOR_A_PAYMENT}:{game.game_id}:{until}",
                opens=Opens.PROPOSAL,
                until=until,
            ),
            at=at,
            whose_act=event.filled_by,
        )

    async def _time_ran_out(
        self, event: TimeToPayRanOut, *, key: str, at: Instant
    ) -> None:
        """**Out of time** (#625): the payers are told their seat is open
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
                notice_about(kind, game, key=f"{kind}:{key}", opens=Opens.PROPOSAL),
                at=at,
            )
        # Full again before this was delivered — booked, or waiting for a
        # payment once more — it is told by that.
        if game.booked or game.waiting_for_a_payment:
            return
        await self._tell(
            [player for player in game.in_ if player not in payers],
            notice_about(
                NoticeKind.SOMEONE_LEFT,
                game,
                key=f"{NoticeKind.SOMEONE_LEFT}:{key}",
                opens=Opens.PROPOSAL,
                reason=NoticeReason.FELL_BACK,
            ),
            at=at,
        )

    async def _payment_not_in_time(
        self, game: GameBrief, players: Collection[UUID], *, key: str, at: Instant
    ) -> None:
        await self._tell(
            players,
            notice_about(
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
            notice_about(
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
            notice_about(
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
            notice_about(
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

    # -- somebody leaving -----------------------------------------------------

    async def _left(self, event: SeatLeft, *, key: str, at: Instant) -> None:
        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked:
            return
        if event.card_not_fixed:
            # Their time to fix the card at its holding ran out (#639): their
            # seat is the others' to fill now, and they owe nothing.
            await self._give.execute(
                event.player_id,
                notice_about(
                    NoticeKind.TIME_TO_FIX_RAN_OUT,
                    game,
                    key=f"{NoticeKind.TIME_TO_FIX_RAN_OUT}:{key}",
                    opens=Opens.PROPOSAL,
                    reason=NoticeReason.SEAT_OPEN,
                    you_left=True,
                ),
                at=at,
            )
        # Whoever took the leaver's seat before this was delivered is not told
        # the seat they took was left.
        taken_by = game.seats_taken.get(event.player_id)
        # A friends game its sender covers keeps a seat left before the
        # cut-off empty, the sender's to fill — no rescue (#752).
        empty = event.player_id in game.empty
        notice = notice_about(
            NoticeKind.SOMEONE_LEFT,
            game,
            key=f"{NoticeKind.SOMEONE_LEFT}:{key}",
            opens=Opens.BOOKING,
            people=(event.player_id,),
            reason=NoticeReason.SEAT_EMPTY if empty else NoticeReason.SEAT_OPEN,
        )
        for player in sorted(
            {p for p in game.seated if p not in (event.player_id, taken_by)}, key=str
        ):
            await self._give.execute(
                player, self._with_the_cover_line(notice, game, to=player), at=at
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
            notice_about(
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
                notice_about(
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

    async def _club_cancelled(
        self, event: ClubCancelled, *, key: str, at: Instant
    ) -> None:
        """**A club's cancel tells the players it never charged** (#711). Every
        player still in was charged a seat charge, and that charge already tells
        them what the cancel did to their money — a held share let go, a checked
        one closed, a paid one refunded — so only a player with **no** charge on
        the game is told here, and nobody twice. The booking is the proposal's
        own id (``bookings`` is born under it)."""

        game = await self._games.about(event.proposal_id, at=at)
        if game is None:
            return
        uncharged = [
            player
            for player in event.player_ids
            if not await self._shares.has_a_charge(game.game_id, player)
        ]
        await self._tell(
            uncharged,
            notice_about(
                NoticeKind.GAME_CALLED_OFF,
                game,
                key=f"{NoticeKind.GAME_CALLED_OFF}:{key}",
                opens=Opens.BOOKING,
                reason=game.cancel_reason,
            ),
            at=at,
        )

    async def _moved(self, event: CourtMoved, *, key: str, at: Instant) -> None:
        """The club's own Move (#671; the mechanics §17.2, Q122): everybody
        with a seat on the booking reads the court it is on now and its kind,
        and that nothing else changes. The court and its kind are the event's
        — kept on the notice, so it reads the same after a second move. **A
        move by cancel** (#672) says why the court it left can't be played:
        the cancel's reason and that court travel on the event too."""

        game = await self._games.about(event.booking_id, at=at)
        if game is None or not game.booked:
            return
        await self._tell(
            game.seated,
            notice_about(
                NoticeKind.GAME_MOVED,
                game,
                key=f"{NoticeKind.GAME_MOVED}:{key}",
                opens=Opens.BOOKING,
                reason=event.reason,
                court_name=event.court_name,
                indoor=event.indoor,
                moved_from=event.moved_from,
            ),
            at=at,
        )

    async def _fell_back(
        self, event: FellBackToFilling, *, key: str, at: Instant
    ) -> None:
        """**A full game falls back, and everybody still In is told** (Q104):
        a seat opened while the game waited for a payment (#625). Somebody who
        took their own yes back is named — *it's filling again*; any other seat
        opened by what happened to its player, which is never said."""

        game = await self._games.about(event.proposal_id, at=at)
        # Full again before this was delivered — booked, or waiting for a
        # payment once more — it is told by that.
        if game is None or game.booked or game.waiting_for_a_payment:
            return
        opened = set(event.player_ids)
        # Still out by their own act; one who came back since is nobody's
        # departure.
        left = tuple(player for player in event.left if player in game.withdrawn)
        reason = NoticeReason.FILLING_AGAIN if left else NoticeReason.FELL_BACK
        await self._tell(
            [player for player in game.in_ if player not in opened],
            notice_about(
                NoticeKind.SOMEONE_LEFT,
                game,
                key=f"{NoticeKind.SOMEONE_LEFT}:{key}",
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
            # It went while the game waited for a payment (#625): the people
            # In are dealt a new card first.
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
            notice_about(
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
            notice_about(
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
        if game is None or not game.filling or game.open_seats != 1:
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
            notice_about(
                NoticeKind.YOU_COMPLETE_IT,
                game,
                key=f"{NoticeKind.YOU_COMPLETE_IT}:{game.game_id}",
                opens=Opens.DECK,
            ),
            at=at,
        )

    async def _new_card(self, event: Redealt, *, key: str, at: Instant) -> None:
        """The card first a club's cancel promised: told to those it was
        promised to, on the card they find on top of the deck."""

        if event.card_id is None:
            return
        card = await self._games.about(event.card_id, at=at)
        if card is None or not card.filling:
            return
        # At the club and hour the cancel took, what changed is the kind of
        # court or the price: the notice names the kind, as the card shows it
        # (#673, Q123).
        cancelled = await self._games.about(event.proposal_id, at=at)
        at_its_hour = cancelled is not None and (
            cancelled.club_id,
            cancelled.starts_at,
        ) == (card.club_id, card.starts_at)
        await self._tell(
            await self._decks.showing(card.game_id, event.player_ids, at=at),
            notice_about(
                NoticeKind.NEW_GAME,
                card,
                key=f"{NoticeKind.NEW_GAME}:{key}",
                opens=Opens.DECK,
                amount_grosze=card.share_grosze,
                indoor=await self._decks.kind_of_court(card.game_id)
                if at_its_hour
                else None,
            ),
            at=at,
        )

    async def _dealt(self, event: VersionDealt, *, key: str, at: Instant) -> None:
        game = await self._games.about(event.proposal_id, at=at)
        if game is None or game.posted_by is None:
            return
        if not game.filling:
            return
        dealt = [player for player in event.player_ids if player in game.undecided]
        poster = (game.posted_by,) if game.posted_by in game.in_ else ()
        await self._tell(
            await self._decks.showing(game.game_id, dealt, at=at),
            notice_about(
                NoticeKind.CHALLENGE,
                game,
                key=f"{NoticeKind.CHALLENGE}:{game.game_id}",
                opens=Opens.DECK,
                people=poster,
            ),
            at=at,
        )

    # -- the court (#663) ----------------------------------------------------

    async def _on_the_court(
        self, game_id: UUID, *, at: Instant
    ) -> tuple[CourtBrief, GameBrief] | None:
        """A Competitive booked game's court, and the game a notice tells —
        ``None`` for a For fun one, which is told none of these."""

        court = await self._courts.of_game(game_id, at=at)
        if court is None or not court.competitive:
            return None
        game = await self._games.about(court.booking_id, at=at)
        return None if game is None else (court, game)

    async def _not_here_yet(
        self, event: AbsenceNoted, *, key: str, at: Instant
    ) -> None:
        """*Ivan is at Ogrody 33 and you're not there yet* — to the player
        tapped, at once; one who arrived before this was delivered is awaited
        by nobody."""

        found = await self._on_the_court(event.game_id, at=at)
        if found is None:
            return
        court, game = found
        if event.player_id not in court.awaited:
            return
        await self._give.execute(
            event.player_id,
            notice_about(
                NoticeKind.NOT_HERE_YET,
                game,
                key=f"{NoticeKind.NOT_HERE_YET}:{key}",
                opens=Opens.RESULT,
                people=(event.noted_by,),
            ),
            at=at,
        )

    async def _arrived(self, event: ArrivalNoted, *, key: str, at: Instant) -> None:
        """*Oscar is at Ogrody 33* — to whoever tapped *isn't here yet* about
        him; theirs is their own when they said *they're here* themselves."""

        found = await self._on_the_court(event.game_id, at=at)
        if found is None:
            return
        court, game = found
        tapped_by = court.noted_by.get(event.player_id)
        if tapped_by is None:
            return
        await self._tell(
            (tapped_by,),
            notice_about(
                NoticeKind.AT_THE_CLUB,
                game,
                key=f"{NoticeKind.AT_THE_CLUB}:{key}",
                opens=Opens.RESULT,
                people=(event.player_id,),
            ),
            at=at,
            whose_act=event.noted_by,
        )

    async def _were_they_there(
        self, event: PresenceClaimed, *, key: str, at: Instant
    ) -> None:
        """*Was Oscar at Ogrody 33?* — to everybody else on the court who may
        confirm it, by the end of the late claim's day; a claim confirmed
        before this was delivered asks nobody."""

        found = await self._on_the_court(event.game_id, at=at)
        if found is None:
            return
        court, game = found
        if event.player_id not in court.claimed:
            return
        await self._tell(
            [player for player in court.vouching if player != event.player_id],
            notice_about(
                NoticeKind.WERE_THEY_THERE,
                game,
                key=f"{NoticeKind.WERE_THEY_THERE}:{key}",
                opens=Opens.RESULT,
                people=(event.player_id,),
                until=court.claims_close_at,
            ),
            at=at,
        )

    async def _score_up(
        self,
        event: ResultProposed | ResultCorrected | ResultCountered,
        *,
        key: str,
        at: Instant,
    ) -> None:
        """*Is that right?* — to those across the net from whoever put the
        score up, whose agreement it waits on, and by when silence settles it.
        A score agreed with before this was delivered asks nobody."""

        found = await self._on_the_court(event.game_id, at=at)
        if found is None:
            return
        court, game = found
        await self._tell(
            [
                player
                for player in court.to_agree
                if court.sides.get(player) != event.side
            ],
            notice_about(
                NoticeKind.IS_THAT_RIGHT,
                game,
                key=f"{NoticeKind.IS_THAT_RIGHT}:{key}",
                opens=Opens.RESULT,
                people=(event.player_id,),
                reason=_SCORE_PUT_UP[type(event)],
                until=court.settles_at,
            ),
            at=at,
        )


#: How a score went up, as *Is that right?* says it: put up, changed by its own
#: side, or a different one from across the net.
_SCORE_PUT_UP: Final[dict[type[Any], NoticeReason | None]] = {
    ResultProposed: None,
    ResultCorrected: NoticeReason.CORRECTED,
    ResultCountered: NoticeReason.COUNTERED,
}

_Telling = Callable[..., Awaitable[None]]

#: Every event a player is told about, and how — the one list, so what is
#: subscribed and what is handled cannot drift apart.
_TELLING: Final[dict[type[Any], _Telling]] = {
    SeatChargeKept: TellThePlayers._seats_booked,
    SeatChargeChecked: TellThePlayers._seats_booked,
    SeatChargeTaken: TellThePlayers._seats_booked,
    SeatChargeFailed: TellThePlayers._payment_refused,
    SeatChargeHoldingRefused: TellThePlayers._payment_refused,
    TimeToPayGiven: TellThePlayers._waiting_for_a_payment,
    TimeToPayRanOut: TellThePlayers._time_ran_out,
    FellBackToFilling: TellThePlayers._fell_back,
    SeatChargeRefundDecided: TellThePlayers._refunded,
    SeatChargeRefunded: TellThePlayers._seat_taken_refunded,
    SeatChargeReleased: TellThePlayers._let_go,
    SeatLeft: TellThePlayers._left,
    KeptSeatRanOut: TellThePlayers._kept_seat_ran_out,
    CalledOffAtCutOff: TellThePlayers._called_off_short,
    ClubCancelled: TellThePlayers._club_cancelled,
    CourtMoved: TellThePlayers._moved,
    ProposalExpired: TellThePlayers._expired,
    CourtHourLost: TellThePlayers._court_lost,
    YesSaid: TellThePlayers._one_seat_left,
    YesResumed: TellThePlayers._one_seat_left,
    VersionDealt: TellThePlayers._dealt,
    Redealt: TellThePlayers._new_card,
    AbsenceNoted: TellThePlayers._not_here_yet,
    ArrivalNoted: TellThePlayers._arrived,
    PresenceClaimed: TellThePlayers._were_they_there,
    ResultProposed: TellThePlayers._score_up,
    ResultCorrected: TellThePlayers._score_up,
    ResultCountered: TellThePlayers._score_up,
    FriendRequested: TellThePlayers._friend_request,
    FriendsMade: TellThePlayers._friends_made,
    LevelAsked: TellThePlayers._level_asked,
    LevelGot: TellThePlayers._level_got,
    BookedByAFriend: TellThePlayers._invited,
    SeatInvited: TellThePlayers._seat_invited,
    InvitedSeatTaken: TellThePlayers._invited_seat_taken,
    SeatOpened: TellThePlayers._seat_opened,
    CoverWarned: TellThePlayers._cover_warned,
    InvitedSeatDeclined: TellThePlayers._seat_answered,
    InvitedSeatRanOut: TellThePlayers._seat_answered,
    InvitedSeatAccepted: TellThePlayers._accepted,
    CalledOffBySender: TellThePlayers._called_off_by_the_sender,
}

#: What ``subscribe_the_teller`` hears.
TOLD_ABOUT: Final[tuple[type[Any], ...]] = tuple(_TELLING)

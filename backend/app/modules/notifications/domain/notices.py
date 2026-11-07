"""**A player's notices of one day** — what they were told, and the caps on
what they may be (#549; the mechanics §17.2; the screens A7.2, A9).

**Every other kind is always on**: told whenever they happen, pushed and listed.
**Three are the player's to switch** (``preferences.py``) and **capped per day
in Kraków** — *You complete it* once, *Challenges for you* and *Fill in alerts*
three times. Past its cap, *You complete it* and a challenge are **bundled**:
the day's last notice of the kind gathers the rest — the list says how many it
holds — and no phone is pushed again. A *Fill in alert* past its cap is not
given at all: a seat to fill is news for the hour it is open, and a fourth the
same day is not a notice anybody asked for.

**Nothing is told twice about the same thing.** A notice's ``key`` says what
it is about: an always-on notice is the event that caused it, so each departure
from a game is its own news; a chosen one is its kind and its game, so a card
that needs only you after a yes, a withdrawal and a yes again is told once a
day.

**Event-sourced, one stream per player per day** (``day_id_for``), so a second
process telling the same player on the same day collides on the stream instead
of going past a cap — and a day nothing was told about has no stream.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import StrEnum
from typing import Final, Iterable
from uuid import UUID, uuid5

from app.kernel import Instant, Sport, invariant
from app.modules.notifications.domain.events import NoticeBundled, NoticeGiven
from app.modules.notifications.domain.preferences import NotificationChoice
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


class NoticeKind(StrEnum):
    """Every notice a player can be told (the mechanics §17.2)."""

    #: *It's a game! · 30 zł held* — the shares held until the cut-off, which
    #: the notice keeps as ``until`` (#637); *you paid 30 zł* when taken at once
    #: after it.
    GAME_BOOKED = "GAME_BOOKED"
    #: *It's a game! · waiting for one payment until 14:40* — the four are
    #: matched, and one share was refused: its player's time to pay runs, and
    #: nobody pays until it is in (#625, Q110).
    WAITING_FOR_A_PAYMENT = "WAITING_FOR_A_PAYMENT"
    #: *Your time to pay ran out · Tue 19:00* — to the payer: their seat is
    #: open to others, and theirs to take back while it is free (#625).
    TIME_TO_PAY_RAN_OUT = "TIME_TO_PAY_RAN_OUT"
    #: *Your time to fix your card ran out · Tue 19:00* — the same, before the
    #: cut-off, where nothing was being taken: they owe nothing (#638, Q113).
    TIME_TO_FIX_RAN_OUT = "TIME_TO_FIX_RAN_OUT"
    #: *Confirm your payment to keep your seat* — or to take one, on a rescue.
    #: By a time, after the cut-off: their time to pay (#625).
    CONFIRM_PAYMENT = "CONFIRM_PAYMENT"
    #: *Fix your card by 14:40 to keep your seat* — a hold refused before the
    #: cut-off: nothing is taken then, so nothing is paid in their time to fix
    #: the card (#638, Q113).
    FIX_YOUR_CARD = "FIX_YOUR_CARD"
    #: *Game called off · with the refund* — at the cut-off, or by the club.
    GAME_CALLED_OFF = "GAME_CALLED_OFF"
    #: *Someone left your game.*
    SOMEONE_LEFT = "SOMEONE_LEFT"
    #: *You've been refunded* — your seat was taken.
    REFUNDED = "REFUNDED"
    #: *Your new game · Fri 19:00 at Bonarka Arena* — the card first the club's
    #: cancel promised (Q107).
    NEW_GAME = "NEW_GAME"
    #: *Bonarka Arena moved your game to Court 3 · Thu 19:00* / *Padel · indoor
    #: · nothing else changes* — the club's own Move (#671, Q122). Always on,
    #: to everybody on the booking, opening the booked game, never emailed.
    GAME_MOVED = "GAME_MOVED"
    #: *Your post didn't fill.*
    POST_DID_NOT_FILL = "POST_DID_NOT_FILL"
    #: *You complete it* — a card needs only you.
    YOU_COMPLETE_IT = "YOU_COMPLETE_IT"
    #: *Challenges for you* — a member's post names you.
    CHALLENGE = "CHALLENGE"
    #: *Fill in alerts* — a booked game you fit needs one more.
    FILL_IN_ALERT = "FILL_IN_ALERT"
    #: *Ivan is at Ogrody 33 and you're not there yet* — to the player
    #: somebody at the club tapped *isn't here yet* about (#663).
    NOT_HERE_YET = "NOT_HERE_YET"
    #: *Oscar is at Ogrody 33* — to whoever tapped *isn't here yet*, when the
    #: player arrives (#663).
    AT_THE_CLUB = "AT_THE_CLUB"
    #: *How did it go?* — to all four of a Competitive booked game whose hour
    #: has just ended (#663).
    HOW_DID_IT_GO = "HOW_DID_IT_GO"
    #: *Is that right?* — to the other side, when a score goes up on a
    #: Competitive game: put up, changed, or a different one (#663).
    IS_THAT_RIGHT = "IS_THAT_RIGHT"
    #: *Was Oscar at Ogrody 33?* — to the courtmates, when a player who Didn't
    #: come says *I was there* (#663).
    WERE_THEY_THERE = "WERE_THEY_THERE"
    #: *Get your level so your groups can deal you games.* — **about no game
    #: at all**: once per account, ever, a day after a first group join while
    #: rated in nothing (#727, Q126). Always on, opening Home, never emailed.
    GET_YOUR_LEVEL = "GET_YOUR_LEVEL"
    #: *Inés wants to be your friend* — to the person asked, **once per
    #: request** (``docs/adr/0202`` §1; #745). About no game; it names the
    #: requester, and the group and sport it was asked from. Listed only while
    #: its card is on the reader's Home: answered, set aside or cancelled, the
    #: row is gone from the bell too.
    FRIEND_REQUEST = "FRIEND_REQUEST"
    #: *Kuba said yes — you're friends* — to the requester; *You and Kuba are
    #: friends now* to both, for a crossed request (``reason`` ``CROSSED``).
    #: About no game, opening the friend's record.
    FRIENDS_MADE = "FRIENDS_MADE"
    #: *Tomek wants to play padel with you.* — **level asked**: a friend asked
    #: the reader to get a level in a sport (``docs/adr/0202`` §4; #749), not the
    #: once-per-account *Get your level*. About no game; it names the asker and
    #: the sport, and opens that sport's questionnaire.
    LEVEL_ASKED = "LEVEL_ASKED"
    #: *Zofia has a padel level — you can seat Zofia now.* — **level got**: the
    #: friend the reader asked got their first level in the sport (#749). About
    #: no game; it names the friend, the sport and the group the ask was made
    #: from, whose picker it opens.
    LEVEL_GOT = "LEVEL_GOT"
    #: *Tomek invited you to a game* — a friends game's invitation, to each
    #: friend invited (#751; the words §29.8). Always on, opening Home on the
    #: card; ``until`` is when their 24 hours end.
    FRIENDS_GAME_INVITATION = "FRIENDS_GAME_INVITATION"
    #: *Ania can't make it* — to a friends game's sender, the friend named: they
    #: said *Not this time* (#751; the words §29.9).
    CANT_MAKE_IT = "CANT_MAKE_IT"
    #: *Ania didn't answer* — to a friends game's sender: the friend's 24 hours
    #: ran out (#751).
    DIDNT_ANSWER = "DIDNT_ANSWER"
    #: *Someone took that seat first.* — to a friend invited into an empty seat
    #: of a friends game somebody else took first (#752; the words §29.8).
    INVITED_SEAT_TAKEN = "INVITED_SEAT_TAKEN"
    #: *Saturday 10:00 · 1 seat still empty* / *At Fri 10:00 you pay 50 zł:
    #: your 25 zł and Ania's seat.* — **the cover warning**, to a *Split*
    #: friends game's sender a day before the cut-off (#752; the words §29.9):
    #: ``amount_grosze`` what the cut-off takes from him, ``until`` the cut-off,
    #: ``people`` every seat still unpaid, named.
    COVER_WARNING = "COVER_WARNING"


class Opens(StrEnum):
    """The screen a notice opens on when tapped (the screens A9)."""

    #: The booked game's details — the seat, the money, the chat.
    BOOKING = "BOOKING"
    #: A game still filling, or one that did not: its details.
    PROPOSAL = "PROPOSAL"
    #: The group's deck, with the card on top.
    DECK = "DECK"
    #: The booked game's result screen — who turned up, and the score (#663).
    RESULT = "RESULT"
    #: Home — where *Get your level* stands on a card too (#727), and a friend
    #: request (#745).
    HOME = "HOME"
    #: The player record of the person the notice names — a new friend (#745).
    RECORD = "RECORD"
    #: The questionnaire of the notice's sport, through the level pass and its
    #: usual return — *level asked* (#749).
    QUESTIONNAIRE = "QUESTIONNAIRE"
    #: The Friends tab's picker of the notice's group (``pool_id``) in its
    #: sport, where the friend it names can be seated now — *level got* (#749).
    PICKER = "PICKER"


class NoticeReason(StrEnum):
    """The reasons a notice gives in Notifications' own words — beside the codes
    it passes on from the context that said why (a refused payment's, the
    club's cancel)."""

    #: Somebody left a booked game: their seat is open.
    SEAT_OPEN = "SEAT_OPEN"
    #: An accepted friend left a friends game its sender's card covers, before
    #: the cut-off: their seat is **empty**, the sender's to fill, no rescue
    #: (#752).
    SEAT_EMPTY = "SEAT_EMPTY"
    #: Somebody left a full game waiting for one payment: it is filling again.
    FILLING_AGAIN = "FILLING_AGAIN"
    #: A full game went back to filling and nobody is named: whose week
    #: filled, who no longer fits, whose card failed is never said (Q104).
    FELL_BACK = "FELL_BACK"
    #: A full game gone back to filling reached its book-by first (Q106).
    BOOK_BY_PASSED = "BOOK_BY_PASSED"
    #: A full game gone back to filling lost its court hour first.
    COURT_HOUR_LOST = "COURT_HOUR_LOST"
    #: A game still short at the club's cut-off.
    SHORT_AT_THE_CUT_OFF = "SHORT_AT_THE_CUT_OFF"
    #: The game booked the moment the payment it waited for came in: *booked ·
    #: you paid*, never a second *It's a game!* (#625, Q110).
    PAYMENT_CAME_IN = "PAYMENT_CAME_IN"
    #: A payment the game waited for did not come in time and it could no
    #: longer fill — called off, nobody paid (#625).
    PAYMENT_NOT_IN_TIME = "PAYMENT_NOT_IN_TIME"
    #: Its court went to another game before the payment it waited for came in
    #: (#625).
    COURT_LOST_WAITING_FOR_A_PAYMENT = "COURT_LOST_WAITING_FOR_A_PAYMENT"
    #: A side changed the score it put up: *Is that right?* again (#663).
    CORRECTED = "CORRECTED"
    #: The other side put a different score up: two scores stand (#663).
    COUNTERED = "COUNTERED"
    #: Two friend requests crossed: nobody said yes (#745).
    CROSSED = "CROSSED"
    #: A friend request made by the requester's link: *Invited you to Raketa*
    #: (#745, #748).
    BY_LINK = "BY_LINK"
    #: A friends game its sender called off: *Tomek called off Saturday 10:00
    #: · Nobody paid.* (#751; the words §29.10).
    BY_THE_SENDER = "BY_THE_SENDER"
    #: A friends game's last seat taken: *It's a game!*, to all four (#751).
    LAST_SEAT_TAKEN = "LAST_SEAT_TAKEN"


@dataclass(frozen=True, slots=True)
class Chosen:
    """A kind the player chooses to be told: which choice it is, how many a day
    in Kraków, and whether the ones past that join the day's last."""

    choice: NotificationChoice
    daily_cap: int
    bundled: bool


#: Every chosen kind — every other kind is always on, and never capped.
CHOSEN: Final[dict[NoticeKind, Chosen]] = {
    NoticeKind.YOU_COMPLETE_IT: Chosen(
        NotificationChoice.YOU_COMPLETE_IT, daily_cap=1, bundled=True
    ),
    NoticeKind.CHALLENGE: Chosen(
        NotificationChoice.CHALLENGES_FOR_YOU, daily_cap=3, bundled=True
    ),
    NoticeKind.FILL_IN_ALERT: Chosen(
        NotificationChoice.FILL_IN_ALERTS, daily_cap=3, bundled=False
    ),
}

#: How long after its hour ends a game is still asked *How did it go?* (#663) —
#: **while its players are still at the club**, which is the point of asking
#: then: the score is put up where it was played. A run that reaches a game
#: later than this — the process down past it — asks nothing; the game's result
#: screen and Home still ask for the score until its entry window closes.
ASKED_WITHIN: Final = timedelta(minutes=30)

#: How long after an account's first group join, still rated in nothing, it
#: is told *Get your level* (#727, Q126) — **given at that moment**, whenever a
#: run comes to it, so every process tells it on one day's stream.
GET_YOUR_LEVEL_AFTER: Final = timedelta(hours=24)

#: How long past ``GET_YOUR_LEVEL_AFTER`` a run still tells it. A run that
#: reaches an account later — the process down a week — tells nothing, and
#: Home's card still asks: the same bound ``ASKED_WITHIN`` puts on *How did it
#: go?*, so a run reads a week's joiners and never every member there is.
GET_YOUR_LEVEL_WITHIN: Final = timedelta(days=7)

#: What a day's stream id is drawn under — fixed for ever, since a stored stream
#: is found by it.
_DAYS: Final = UUID("0b0b9a0e-5c1d-4d5e-9b0a-6a49f3a2c549")


def day_id_for(player_id: UUID, day: date) -> UUID:
    """The stream of what ``player_id`` was told on ``day`` in Kraków."""

    return uuid5(_DAYS, f"{player_id}:{day.isoformat()}")


def notice_id_for(player_id: UUID, day: date, key: str) -> UUID:
    """The notice ``key`` is, told to ``player_id`` on ``day`` — one id, so a
    notice told again would be the same notice."""

    return uuid5(day_id_for(player_id, day), key)


@dataclass(frozen=True, slots=True)
class Notice:
    """What a player is to be told, before the day decides whether they are."""

    kind: NoticeKind
    key: str
    #: The game it is about — its proposal's id, which its booking takes.
    #: **All six facts of the game are ``None`` on a notice about no game**
    #: (*Get your level*, #727), and every other kind has all six.
    game_id: UUID | None
    pool_id: UUID | None
    sport: Sport | None
    #: ``COMPETITIVE`` or ``FOR_FUN``.
    game_kind: str | None
    club_id: UUID | None
    starts_at: Instant | None
    opens: Opens
    amount_grosze: int | None = None
    #: The people it names, in order. **The cover line** (#752) — a friends
    #: game's *can't make it*, *didn't answer* or *left your game* to its
    #: *Split* sender inside the day before the cut-off — puts the one it is
    #: about first, then every seat his cover would pay, beside
    #: ``amount_grosze`` (what he pays) and ``until`` (the cut-off).
    people: tuple[UUID, ...] = ()
    reason: str | None = None
    #: Of the player's own act, which they saw happen: born seen — listed, and
    #: never counted on the bell nor pushed (the mechanics Q102).
    own: bool = False
    #: The deadline it names — when the club must answer, on *It's a game!*
    #: at a club that confirms; when a payment is due, on a time to pay.
    until: Instant | None = None
    #: Told to a player who had left the game: said in a leaver's words
    #: (Q108).
    you_left: bool = False
    #: What was kept on the payment a refund gave back less — *40 zł less the
    #: 1,76 zł kept on your payment* (#641).
    kept_grosze: int | None = None
    #: About a seat the player went for on a booked game and does not hold —
    #: a rescue (#640): *to take the seat*, never *to keep your seat*.
    rescue: bool = False
    #: The court a move put the game on, and its kind (#671) — kept on the
    #: notice, so *Court 3 · indoor* reads the same after a second move.
    court_name: str | None = None
    indoor: bool | None = None
    #: The court the game left, said when a club's cancel moved it — *Court 2
    #: can't be played* (#672).
    moved_from: str | None = None


def get_your_level_notice(player_id: UUID) -> Notice:
    """*Get your level so your groups can deal you games.* (#727; Q126) — about
    no game, so none of a game's six facts, opening Home. **Keyed by the
    account**: told once, whichever day and process tells it."""

    return Notice(
        kind=NoticeKind.GET_YOUR_LEVEL,
        key=f"{NoticeKind.GET_YOUR_LEVEL}:{player_id}",
        game_id=None,
        pool_id=None,
        sport=None,
        game_kind=None,
        club_id=None,
        starts_at=None,
        opens=Opens.HOME,
    )


def friend_request_notice(
    *,
    key: str,
    requester: UUID,
    group_id: UUID | None,
    sport: Sport | None,
    by_link: bool,
) -> Notice:
    """*{nickname} wants to be your friend* (#745) — about no game: **the group
    rides as ``pool_id``** (a group's pool is filed under the group's own id) and
    the sport as ``sport``, so the body can say where it was asked; a link's
    request names neither (its ``Where`` cannot) and says so as its ``reason``.
    Opens Home, where the card is."""

    return Notice(
        kind=NoticeKind.FRIEND_REQUEST,
        key=key,
        game_id=None,
        pool_id=group_id,
        sport=sport,
        game_kind=None,
        club_id=None,
        starts_at=None,
        opens=Opens.HOME,
        people=(requester,),
        reason=NoticeReason.BY_LINK.value if by_link else None,
    )


def friends_made_notice(*, key: str, friend: UUID, crossed: bool) -> Notice:
    """*{nickname} said yes — you're friends*, or for a crossed request *You and
    {nickname} are friends now* (#745). About no game; opens the friend's
    record."""

    return Notice(
        kind=NoticeKind.FRIENDS_MADE,
        key=key,
        game_id=None,
        pool_id=None,
        sport=None,
        game_kind=None,
        club_id=None,
        starts_at=None,
        opens=Opens.RECORD,
        people=(friend,),
        reason=NoticeReason.CROSSED.value if crossed else None,
    )


def level_asked_notice(*, key: str, asker: UUID, sport: Sport) -> Notice:
    """*{asker} wants to play {sport} with you.* (#749) — about no game; it names
    the asker and the sport, and opens that sport's questionnaire. It names no
    group: the friend asked may be in none of the asker's."""

    return Notice(
        kind=NoticeKind.LEVEL_ASKED,
        key=key,
        game_id=None,
        pool_id=None,
        sport=sport,
        game_kind=None,
        club_id=None,
        starts_at=None,
        opens=Opens.QUESTIONNAIRE,
        people=(asker,),
    )


def level_got_notice(*, key: str, friend: UUID, sport: Sport, group_id: UUID) -> Notice:
    """*{friend} has a {sport} level — you can seat {friend} now.* (#749) —
    about no game: **the group the ask was made from rides as ``pool_id``**, as
    a friend request's does, and its picker is what a tap opens."""

    return Notice(
        kind=NoticeKind.LEVEL_GOT,
        key=key,
        game_id=None,
        pool_id=group_id,
        sport=sport,
        game_kind=None,
        club_id=None,
        starts_at=None,
        opens=Opens.PICKER,
        people=(friend,),
    )


@dataclass(frozen=True, slots=True)
class _Told:
    notice_id: UUID
    kind: NoticeKind


@dataclass
class NoticesOfADay:
    """What one player was told on one day, rebuilt by folding its stream."""

    player_id: UUID
    day: date
    #: Every notice given, in the order it was.
    given: tuple[_Told, ...] = ()
    #: The key of everything given or gathered — never told again.
    keys: frozenset[str] = frozenset()
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def from_history(
        cls, player_id: UUID, day: date, events: Iterable[DomainEvent]
    ) -> "NoticesOfADay":
        notices = cls(player_id=player_id, day=day)
        for event in events:
            notices._apply(event)
        return notices

    @property
    def day_id(self) -> UUID:
        return day_id_for(self.player_id, self.day)

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    def give(
        self, notice: Notice, *, at: Instant
    ) -> NoticeGiven | NoticeBundled | None:
        """Tell the player ``notice`` — given, gathered into the day's last of
        its kind, or ``None``: already told, or a kind past its cap that is not
        bundled. **Whether the player chose to be told is the caller's**; the
        day counts."""

        if notice.key in self.keys:
            return None
        chosen = CHOSEN.get(notice.kind)
        if chosen is not None and self._count(notice.kind) >= chosen.daily_cap:
            if not chosen.bundled:
                return None
            last = next(t for t in reversed(self.given) if t.kind is notice.kind)
            bundled = NoticeBundled(
                notice_id=last.notice_id,
                player_id=self.player_id,
                day=self.day.isoformat(),
                kind=notice.kind.value,
                key=notice.key,
                # Only a chosen kind is bundled, and every chosen kind is about
                # a game.
                game_id=invariant(notice.game_id, f"{notice.kind} is about a game"),
                occurred_at=at,
            )
            self._record_that(bundled)
            return bundled
        given = NoticeGiven(
            notice_id=notice_id_for(self.player_id, self.day, notice.key),
            player_id=self.player_id,
            day=self.day.isoformat(),
            kind=notice.kind.value,
            key=notice.key,
            game_id=notice.game_id,
            pool_id=notice.pool_id,
            sport=None if notice.sport is None else notice.sport.value,
            game_kind=notice.game_kind,
            club_id=notice.club_id,
            starts_at=notice.starts_at,
            opens=notice.opens.value,
            amount_grosze=notice.amount_grosze,
            people=notice.people,
            reason=notice.reason,
            occurred_at=at,
            own=notice.own,
            until=notice.until,
            you_left=notice.you_left,
            kept_grosze=notice.kept_grosze,
            rescue=notice.rescue,
            court_name=notice.court_name,
            indoor=notice.indoor,
            moved_from=notice.moved_from,
        )
        self._record_that(given)
        return given

    def _count(self, kind: NoticeKind) -> int:
        return sum(1 for told in self.given if told.kind is kind)

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, NoticeGiven):
            self.given = (
                *self.given,
                _Told(notice_id=event.notice_id, kind=NoticeKind(event.kind)),
            )
            self.keys = self.keys | {event.key}
        elif isinstance(event, NoticeBundled):
            self.keys = self.keys | {event.key}
        else:
            invariant(False, f"a day's notices hold {event!r}")
        self.version += 1

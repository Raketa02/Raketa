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
from datetime import date
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


class Opens(StrEnum):
    """The screen a notice opens on when tapped (the screens A9)."""

    #: The booked game's details — the seat, the money, the chat.
    BOOKING = "BOOKING"
    #: A game still filling, or one that did not: its details.
    PROPOSAL = "PROPOSAL"
    #: The group's deck, with the card on top.
    DECK = "DECK"


class NoticeReason(StrEnum):
    """The reasons a notice gives in Notifications' own words — beside the codes
    it passes on from the context that said why (a refused payment's, the
    club's cancel)."""

    #: Somebody left a booked game: their seat is open.
    SEAT_OPEN = "SEAT_OPEN"
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
    game_id: UUID
    pool_id: UUID
    sport: Sport
    #: ``COMPETITIVE`` or ``FOR_FUN``.
    game_kind: str
    club_id: UUID
    starts_at: Instant
    opens: Opens
    amount_grosze: int | None = None
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
                game_id=notice.game_id,
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
            sport=notice.sport.value,
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

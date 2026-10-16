"""What the Notifications context stands on, in its own words (#549, #621).

**Its own**: the three streams' repositories, the recent list, and the **push
service** — the outside world's, behind ``PushNotifications``, with Expo's
adapter and a recording fake (``infrastructure/``).

**Everybody else's, asked and never told**: Notifications is *told* through
the outbox by contexts that do not know it exists, as a room is
(``docs/adr/0146`` §5), and reads what a notice says off them through seven
ports declared here — what a game is now (``GameBriefs``), what its court says
(``GameCourts``, #663), which booked hours have just ended (``EndedHours``), whose
deck shows a card (``Decks``), what a refund gave back (``PaidShares``), who an
open seat is offered to (``SeatOffers``) and what a person and a club are
called (``Names``). Each is signed in ``infrastructure/`` over the context that
owns the fact, and contracted in ``app/bootstrap/notification_demands.py``.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.notifications.domain.bell import Bell
from app.modules.notifications.domain.notices import NoticesOfADay
from app.modules.notifications.domain.preferences import (
    NotificationChoice,
    NotificationPreferences,
)

# --------------------------------------------------------------------------- #
# Its own
# --------------------------------------------------------------------------- #


class NotificationPreferencesRepository(Protocol):
    async def load(self, player_id: UUID) -> NotificationPreferences: ...

    async def save(self, preferences: NotificationPreferences) -> None:
        """Append what was recorded, and keep the phones' and the choices'
        projections beside it. **No commit.**"""
        ...

    async def holder_of(self, device: str) -> UUID | None:
        """The player this phone is pushed to as, if anybody."""
        ...

    async def tokens_of(self, player_id: UUID) -> Mapping[str, str]:
        """Each phone the player is pushed to, by device: its push token."""
        ...

    async def wanting(
        self, choice: NotificationChoice, among: Collection[UUID]
    ) -> frozenset[UUID]:
        """Those of ``among`` with ``choice`` on — the defaults for a player
        who never chose."""
        ...


class NoticeDayRepository(Protocol):
    async def load(self, player_id: UUID, day: date) -> NoticesOfADay: ...

    async def save(self, notices: NoticesOfADay) -> None:
        """Append what was recorded, and keep the recent list beside it. **No
        commit.**"""
        ...


class BellRepository(Protocol):
    async def load(self, player_id: UUID) -> Bell: ...

    async def save(self, bell: Bell) -> None:
        """Append what was recorded, and keep the last visit beside it. **No
        commit.**"""
        ...


@dataclass(frozen=True, slots=True)
class RecordedNotice:
    """A notice as the recent list holds it: what was given, and how many more
    of its kind the day gathered into it."""

    notice_id: UUID
    kind: str
    game_id: UUID
    pool_id: UUID
    sport: Sport
    game_kind: str
    club_id: UUID
    starts_at: Instant
    opens: str
    amount_grosze: int | None
    people: tuple[UUID, ...]
    reason: str | None
    given_at: Instant
    #: How many notices of its kind the day gathered into this one.
    gathered: int
    #: Of the player's own act: born seen, never counted nor pushed (Q102).
    own: bool = False
    #: The deadline it names, if its kind names one.
    until: Instant | None = None
    #: Told to a player who had left the game (Q108).
    you_left: bool = False
    #: What was kept on the payment a refund gave back less (#641).
    kept_grosze: int | None = None
    #: About a seat the player went for and does not hold — a rescue (#640).
    rescue: bool = False
    #: The court a move put the game on, and its kind (#671).
    court_name: str | None = None
    indoor: bool | None = None
    #: The court a club's cancel moved the game from (#672).
    moved_from: str | None = None
    #: Reached the list — given, or gathered into — since the player last
    #: opened it, and not their own: one the bell counts.
    new: bool = False


@dataclass(frozen=True, slots=True)
class RecordedNotices:
    """The newest of a player's notices, and the bell's number over all of
    them."""

    notices: Sequence[RecordedNotice]
    #: **The bell's number**: every notice that reached the list since the
    #: player last opened it, none of their own — past the rows read, too.
    new_count: int
    #: When they last opened it — ``None`` before the first time.
    last_opened_at: Instant | None


class NoticeDirectory(Protocol):
    async def recent(self, player_id: UUID, *, limit: int) -> RecordedNotices:
        """The player's notices, the newest first, each saying whether it is
        new to them — and how many are new in all, in the same reading.

        **New is read in the store's order, never off the clock**: a notice
        is new when it reached the list after the newest one the list held
        when it was last opened — given, or gathered into and so moved up —
        whatever the instant of what it tells, since the outbox delivers after
        the act."""
        ...


@dataclass(frozen=True, slots=True)
class Push:
    """One notification for one phone: what the phone shows, and what a tap
    opens the app with."""

    token: str
    title: str
    body: str
    data: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class PushReceipt:
    """What the push service said back: the phones it no longer knows — the
    app deleted, the phone wiped — which are pushed to no more."""

    gone: frozenset[str]


class PushUnavailable(Exception):
    """The push service could not be reached, or refused the whole request.
    Nothing is known to have been pushed."""


class PushNotifications(Protocol):
    async def send(self, pushes: Sequence[Push]) -> PushReceipt:
        """Push each to its phone. Raises ``PushUnavailable`` when the service
        could not be asked; a phone it does not know is in the receipt."""
        ...


# --------------------------------------------------------------------------- #
# Everybody else's
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class GameBrief:
    """A game as a notice tells it — as it stands, at the instant asked about.

    Filling or booked, it is one game under one id: the proposal's, which its
    booking takes. ``in_``, ``withdrawn``, ``undecided`` and ``named`` are the filling
    game's people; ``seated`` and ``seats_taken`` the booked game's."""

    game_id: UUID
    pool_id: UUID
    sport: Sport
    #: ``COMPETITIVE`` or ``FOR_FUN``.
    game_kind: str
    club_id: UUID
    starts_at: Instant
    #: One seat's share of the court, in grosze.
    share_grosze: int
    made_at: Instant
    #: The member who posted it — ``None`` on the engine's pick.
    posted_by: UUID | None
    #: Still filling — and so not booked, over or past its book-by.
    filling: bool
    #: Seats nobody is In on, while it fills.
    open_seats: int
    #: Everybody In, while it fills.
    in_: tuple[UUID, ...]
    #: Everybody who took their yes back and has not said it again.
    withdrawn: tuple[UUID, ...]
    #: Everybody dealt it — named, or a next best fit dealt into a version
    #: after a no — who has not answered.
    undecided: tuple[UUID, ...]
    #: Those of them **named** when their version was dealt (the mechanics
    #: §6.3): never a next best fit dealt into it after.
    named: tuple[UUID, ...]
    #: A court is held for it and paid for — whole, or with a seat open.
    booked: bool
    #: Everybody with a seat on the booked game now.
    seated: tuple[UUID, ...]
    #: Each leaver whose seat was taken, and who took it.
    seats_taken: Mapping[UUID, UUID]
    #: Why the club cancelled it, once it did — ``WEATHER``, ``REPAIR``,
    #: ``DOUBLE_BOOKING`` or ``OTHER``.
    cancel_reason: str | None
    #: The player whose own act booked it — their yes, a join, a confirmed
    #: payment — which they saw happen; ``None`` while it fills, and when a
    #: paused yes coming back booked it.
    filled_by: UUID | None
    #: The last moment it can fill: past it, a game still filling is over.
    book_by: Instant
    #: When it went back to filling, full: a seat opening or a time to pay
    #: running out while it waited for a payment (#625, Q106) — ``None`` on a
    #: game never full.
    fell_back_at: Instant | None
    #: Each leaver whose seat opened before the club's cut-off and nobody took
    #: — on a game called off at its cut-off, whose empty seat called it off
    #: (Q108). Empty on a game nobody left.
    left_it_short: tuple[UUID, ...]

    #: Everybody In whose refused share the game waits for, and until when —
    #: their time to pay (#625).
    paying: Mapping[UUID, Instant] = field(default_factory=dict)
    #: Those of them whose time is to fix the card, before the cut-off — every
    #: other one's is to pay (#638).
    fixing: frozenset[UUID] = frozenset()
    #: Every seat is In and a payment is awaited: the game waits for it.
    waiting_for_a_payment: bool = False
    #: It booked the moment the payment it waited for came in: its players
    #: were told *It's a game!* already (Q110).
    booked_on_a_payment: bool = False

    @property
    def fell_back(self) -> bool:
        """A full game gone back to filling before it was booked (Q106)."""

        return self.fell_back_at is not None


class GameBriefs(Protocol):
    async def about(self, game_id: UUID, *, at: Instant) -> GameBrief | None:
        """The game as it stands, read against ``at`` — ``None`` for no such
        game."""
        ...


@dataclass(frozen=True, slots=True)
class CourtBrief:
    """A booked game's court as it stands, at the instant asked about — who
    is on it, and what it waits on them for (#663). Read off the game the
    booking opened: its line-up, its attendance and its score.

    **Each wait is read against the instant**, as the court folds it: a
    player still awaited, a score still waiting for its answer, a claim not
    yet confirmed. Something already answered by then is waited on by
    nobody."""

    #: The booking it was opened for — the id ``GameBriefs`` reads the game
    #: under, and a notice carries.
    booking_id: UUID
    #: A Competitive game; a For fun one asks nobody anything.
    competitive: bool
    #: Everybody on the court, each with their side's code (``A``, ``B``).
    sides: Mapping[UUID, str]
    #: When its booked hour ends.
    hour_ends_at: Instant
    #: Nobody has said they played, and nothing stops a score: nobody is
    #: awaited, nobody Didn't come, it is not called off nor short.
    awaiting_a_score: bool
    #: Each player tapped *isn't here yet* — awaited or not — and who first
    #: tapped it.
    noted_by: Mapping[UUID, UUID]
    #: Those still awaited: tapped, not arrived, the tap window running.
    awaited: frozenset[UUID]
    #: Those whose agreement a score on the table waits on.
    to_agree: frozenset[UUID]
    #: When what is on the table settles if nobody answers — ``None`` with
    #: nothing waiting.
    settles_at: Instant | None
    #: Those who said *I was there* and wait for somebody to confirm it.
    claimed: frozenset[UUID]
    #: Those who may confirm a claim: on the court, and not absent themselves.
    vouching: frozenset[UUID]
    #: When *I was there* and its confirmation stop being sayable.
    claims_close_at: Instant


class GameCourts(Protocol):
    async def of_game(self, game_id: UUID, *, at: Instant) -> CourtBrief | None:
        """The court of the game with this id — the Game's own, which its
        events carry — read against ``at``; ``None`` for no such booked
        game."""
        ...

    async def of_booking(self, booking_id: UUID, *, at: Instant) -> CourtBrief | None:
        """The court of the game this booking opened, read against ``at``;
        ``None`` while it has none."""
        ...


class EndedHours(Protocol):
    async def ended(self, *, after: Instant, by: Instant) -> Sequence[UUID]:
        """Every booked game, whole, whose hour ended after ``after`` and by
        ``by`` — its booking's id, the earliest first. **Candidates**: the
        court says whether anything is asked."""
        ...


class Decks(Protocol):
    async def showing(
        self, game_id: UUID, players: Collection[UUID], *, at: Instant
    ) -> tuple[UUID, ...]:
        """Those of ``players`` whose deck shows this card at ``at`` — every
        filter the deck reads passed, and the card not withheld from them —
        so an alert never points at a card the reader cannot find."""
        ...

    async def kind_of_court(self, game_id: UUID) -> bool | None:
        """The kind of court the card promises, as the deck shows it now:
        ``True`` indoor and ``False`` outdoor when every free court it could be
        booked on is of that kind, ``None`` when they are mixed or there is no
        such card (Q122) — what *Your new game* names at the club and hour a
        cancel took (#673)."""
        ...


@dataclass(frozen=True, slots=True)
class PaidShare:
    """A share a player paid, and what giving it back gives them."""

    game_id: UUID
    #: What the player gets back: what the provider gave, once it has —
    #: until then the share, or the share less exactly the fee kept on the
    #: payment; ``None`` while that fee is not yet known (#641). Never an
    #: estimate.
    refunded_grosze: int | None
    #: What was kept on the payment, once a refund less it was given (#641).
    kept_grosze: int | None = None
    #: Given back because somebody took the seat its player left after the
    #: cut-off — told when the refund is made (#641).
    seat_taken: bool = False


class PaidShares(Protocol):
    async def of(self, charge_id: UUID) -> PaidShare | None: ...

    async def of_player(self, game_id: UUID, player_id: UUID) -> PaidShare | None:
        """The share this player paid for this game, and what giving it back
        gives them — ``None`` for one who paid none."""
        ...

    async def has_a_charge(self, game_id: UUID, player_id: UUID) -> bool:
        """Whether this player was ever charged for this game, in whatever state
        — held, checked, paid or let go. ``False`` only for one never charged
        (#711): the club's cancel tells those, and nobody else."""
        ...


class SeatOffers(Protocol):
    async def pool_of(self, game_id: UUID) -> tuple[UUID, ...]:
        """Everybody in the booked game's pool now."""
        ...

    async def offered_among(
        self, game_id: UUID, players: Collection[UUID], *, at: Instant
    ) -> tuple[UUID, ...]:
        """Those of ``players`` its open seat is offered to at ``at`` — on the
        Fill in board, whether or not their deck deals it."""
        ...


class Names(Protocol):
    async def of_people(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        """Each player's Name — never the nickname."""
        ...

    async def of_clubs(self, club_ids: Collection[UUID]) -> Mapping[UUID, str]: ...


__all__ = [
    "BellRepository",
    "CourtBrief",
    "GameCourts",
    "Decks",
    "EndedHours",
    "GameBrief",
    "GameBriefs",
    "Names",
    "NoticeDayRepository",
    "NoticeDirectory",
    "NotificationPreferencesRepository",
    "PaidShare",
    "PaidShares",
    "Push",
    "PushNotifications",
    "PushReceipt",
    "PushUnavailable",
    "RecordedNotice",
    "RecordedNotices",
    "SeatOffers",
]

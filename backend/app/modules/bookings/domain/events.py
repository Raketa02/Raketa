"""The Booking stream: one per filled proposal, filed under the proposal's id.

**Born booked** (#541): ``BookingConfirmed`` is the fill's whole record — the
court and its number, the seats and their sides, the club's cut-off as it stood
then, and the Game it opened — written in the transaction that took every seat's
money.

**Or born waiting for the club** (#543): at an On request club the full game is
``BookingRequested`` — the same record but the Game, and the moment the club's
answer is due — and the court is reserved for it until the club answers.
``BookingAccepted`` books it and names the Game it opened; ``BookingRefused`` and
``BookingTimedOut`` call it off with nobody paid; and ``RequestWithdrawn`` takes
it back because a seat opened while it waited — the game is filling again, the
people still In keep their places on it, and full again it is
``BookingRequested`` once more on the same stream. **A share refused at the
club's yes** keeps the yes and the court while its player has time to pay
(#626): ``BookingAwaitingAPayment``, then ``BookingAccepted`` on the payment, or
``PaymentNotInTime`` when it does not come.

**Then the booked game is lived** (#544): ``SeatLeft`` is a player leaving it —
their seat open, the game still the others' — and ``CalledOffAtCutOff`` is a
seat that opened before the club's cut-off still open at it: the game is off,
and everybody still in is named, to be refunded in full.

**And an open seat is a rescue** (#545): ``SeatRescued`` is somebody taking it
— the leaver's seat and side, paid at once — and ``NoSaidToTheSeat`` is a member
the seat was dealt to as a *Seat open* card saying no to it.

**The club runs it** (#547): ``CourtMoved`` puts the game on another court of
its sport at the same hour, ``CancelledByClub`` calls it off with the club's
reason — everybody still in named, to be refunded in full — and
``PlayerCheckedIn`` is the desk's scan of a player's code on the day.

Every event carries ``booking_id``, the stream's own key. Sport and kind travel
as their codes, as a proposal's do.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


def _uuids(values: tuple[UUID, ...]) -> tuple[UUID, ...]:
    # JSON hands a list of strings back; the codec coerces a bare ``UUID`` hint
    # and nothing inside a tuple (``proposals``' ``VersionDealt`` does the same).
    return tuple(UUID(str(value)) for value in values)


@dataclass(frozen=True)
class BookingConfirmed:
    """The game is booked: a court is held, every seat paid, a Game opened.

    ``first_side`` and ``second_side`` are the sides **drawn for the most even
    game** (the mechanics §11.7) — one player each in singles, two in doubles.
    ``cut_off`` is the club's free cancellation deadline for this game,
    measured with the club's setting at the moment it filled; a game that filled
    after it was never free to leave.
    """

    booking_id: UUID
    pool_id: UUID
    club_id: UUID
    court_id: UUID
    #: What the court is called at the club — *Court 2* — given at booking.
    court_name: str
    sport: str
    #: ``COMPETITIVE`` or ``FOR_FUN``.
    kind: str
    start: datetime
    share_grosze: int
    first_side: tuple[UUID, ...]
    second_side: tuple[UUID, ...]
    cut_off: datetime
    #: The ordinary Game this booking opened.
    game_id: UUID
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "first_side", _uuids(self.first_side))
        object.__setattr__(self, "second_side", _uuids(self.second_side))


@dataclass(frozen=True)
class BookingRequested:
    """A full game was put to its On request club, which has until
    ``answer_by`` to say yes (the mechanics §16.3, §16.8). Nobody has paid.

    Everything ``BookingConfirmed`` records but the Game, which opens only when
    the club accepts: ``court_id`` is the court **held** for the answer — the
    first free one of the sport at the hour, as a booking's is — and the sides
    are drawn already, so the players read the game they are waiting on.
    Recorded again on the same stream when the game fills again after a
    ``RequestWithdrawn``, with whoever is In then.

    ``filled_by`` is the player whose own act left no seat open and so put it
    to the club — their yes, a join, a confirmed payment — who saw *It's a
    game!* on their own screen; ``None`` for a paused yes coming back, and for
    the rows recorded before it was asked (#622).
    """

    booking_id: UUID
    pool_id: UUID
    club_id: UUID
    court_id: UUID
    court_name: str
    sport: str
    kind: str
    start: datetime
    share_grosze: int
    first_side: tuple[UUID, ...]
    second_side: tuple[UUID, ...]
    cut_off: datetime
    #: When the club's time to confirm runs out — the request's own deadline.
    answer_by: datetime
    occurred_at: datetime
    filled_by: UUID | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "first_side", _uuids(self.first_side))
        object.__setattr__(self, "second_side", _uuids(self.second_side))


@dataclass(frozen=True)
class BookingAccepted:
    """The club said yes: every seat was paid, the court is the players', and
    the ordinary Game ``game_id`` is open."""

    booking_id: UUID
    game_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class BookingRefused:
    """The club said no — *Called off · refused*. Nobody paid. ``reason`` is
    the club's own note, for its records; it is never shown to a player."""

    booking_id: UUID
    reason: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class BookingTimedOut:
    """The club did not answer before ``answer_by`` — *Called off · no
    answer*. Nobody paid."""

    booking_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class RequestWithdrawn:
    """A seat opened while the game waited for the club — each of
    ``player_ids`` left, or could no longer be In — so the request is off and
    nobody paid. **The people still In keep their places** (Q106): the game is
    filling again, *Seat open* on their Home, and when it is full the club is
    asked again.

    ``left`` is those of them who took their own yes back — *Leave*,
    *Withdraw*, leaving the group, a block — whom the others are told by name;
    every other seat opened by what happened to its player (another game took
    their hour or their week, a pair stopped fitting, a share refused at the
    club's yes), which nobody is told (Q104). Empty on the rows recorded before
    it was asked."""

    booking_id: UUID
    player_ids: tuple[UUID, ...]
    occurred_at: datetime
    left: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "player_ids", _uuids(self.player_ids))
        object.__setattr__(self, "left", _uuids(self.left))


@dataclass(frozen=True)
class BookingAwaitingAPayment:
    """**The club said yes, and one share could not be held** (#626; the
    mechanics Q109, Q112): the club's yes and its court are kept while
    ``player_ids`` have until ``until`` to pay — thirty minutes, never past the
    game's book-by. Nobody paid; the other holds wait on their cards, and the
    payment in time books it (``BookingAccepted``) without asking the club
    again. The desk reads *Accepted · waiting for one player's payment*."""

    booking_id: UUID
    player_ids: tuple[UUID, ...]
    until: datetime
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "player_ids", _uuids(self.player_ids))


@dataclass(frozen=True)
class PaymentNotInTime:
    """**A payment the club's yes waited on did not come in time** (#626;
    Q109, Q112): the booking is called off, nobody paid, and the court is the
    club's again — its desk is emailed *A game didn't go ahead*. The people
    still In keep their places, the game filling again for them and asked of the
    club again when full, as after ``RequestWithdrawn``; ``player_ids`` are the
    payers whose seats reopened.

    ``for_good`` is a game that can no longer fill — the book-by had come, so no
    time to pay was left, or it ran out on it — called off for everybody on it;
    ``at_once`` the first of those: the share was refused at the club's yes
    with no time left, so it never waited.
    """

    booking_id: UUID
    player_ids: tuple[UUID, ...]
    occurred_at: datetime
    for_good: bool = False
    at_once: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "player_ids", _uuids(self.player_ids))


@dataclass(frozen=True)
class SeatLeft:
    """A player left the booked game before it started — *Leave the game*
    (#544; the mechanics §13). **Their seat is open**, and the game is still
    the others'. Whether they left before the club's cut-off is read off this
    instant against the booking's ``cut_off``; what it costs them is the
    money's, recorded on their Seat charge."""

    booking_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class CalledOffAtCutOff:
    """**A game plays full or not at all** (#544; the mechanics §12.3): a seat
    that opened before the club's cut-off was still open at it, so the game is
    off, the court is the club's again, and everybody still in — ``player_ids``
    — is refunded in full. Recorded by the cut-off job, at or after the
    cut-off."""

    booking_id: UUID
    player_ids: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "player_ids", _uuids(self.player_ids))


@dataclass(frozen=True)
class SeatRescued:
    """Somebody took a seat a leaver left open — a **rescue** (#545; the
    mechanics §10.1). ``player_id`` sits where ``replacing`` sat, on ``side``
    (``A``, the first, or ``B``), and has paid their share; the seat that
    opened first is the one taken. Whether the leaver is refunded now — they
    left after the cut-off — is the money's, recorded on their Seat charge."""

    booking_id: UUID
    player_id: UUID
    side: str
    #: The leaver whose seat this was.
    replacing: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class NoSaidToTheSeat:
    """A member the open seat was dealt to as a *Seat open* card swiped it
    away — *not this time* (#545; the mechanics §6.2). Silent and never on
    their record: the card does not come back to their deck."""

    booking_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class CourtMoved:
    """The club moved the booked game to another court of its sport at the same
    hour — a broken court, a desk's own reshuffle (#547; the mechanics §16.16).
    The players read the new number; nothing else about the game moves."""

    booking_id: UUID
    court_id: UUID
    #: What the new court is called at the club.
    court_name: str
    occurred_at: datetime


@dataclass(frozen=True)
class CancelledByClub:
    """The club cancelled the booked game before it started (#547; the
    mechanics §16.9): everybody still in — ``player_ids`` — is refunded in full,
    it is on nobody's record, and the court hour is the club's again.

    ``reason`` is the club's: ``WEATHER``, ``REPAIR``, ``DOUBLE_BOOKING`` or
    ``OTHER`` — told to the players with the refund."""

    booking_id: UUID
    reason: str
    player_ids: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "player_ids", _uuids(self.player_ids))


@dataclass(frozen=True)
class PlayerCheckedIn:
    """The club's desk scanned this player's code, or typed it, on the day of
    the game (#547; the mechanics §15.1, §16.10): **they were there**, and can
    never be reported as not turning up. Evidence, never a condition for money.
    """

    booking_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class NewBookingsSummarised:
    """The club's desk was sent the day's new bookings (#548; the mechanics
    §16.12, the screens B9 — *a new booking: a daily summary*): every game
    booked at the club in the day up to the close of ``day`` (``YYYY-MM-DD``)
    — ``booking_ids`` — once. **Its own stream, one per club per day**, so a
    second process summing up the same day collides on it."""

    summary_id: UUID
    club_id: UUID
    day: str
    booking_ids: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "booking_ids", _uuids(self.booking_ids))

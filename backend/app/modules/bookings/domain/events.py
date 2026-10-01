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
it back because a seat opened while it waited — nobody has a seat on it any
more, the game is filling again, and full again it is ``BookingRequested`` once
more on the same stream.

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
    nobody paid. **Nobody keeps a seat on it**: the people still In are on the
    game, filling again, and when it is full the club is asked again."""

    booking_id: UUID
    player_ids: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "player_ids", _uuids(self.player_ids))

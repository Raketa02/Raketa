"""The Booking stream: one per filled proposal, filed under the proposal's id.

**Born booked** (#541): ``BookingConfirmed`` is the fill's whole record — the
court and its number, the seats and their sides, the club's cut-off as it stood
then, and the Game it opened — written in the transaction that took every seat's
money. At an On request club a booking will be born *requested* instead (#543).

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

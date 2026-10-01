"""Who kept a booked game, and who broke it — the record's rules (#544; the
mechanics §15.4).

**A booked game is a plan with a moment**, so whether somebody kept it is the
*keeps plans* strand's opportunity: it closes when the game's hour comes, or
when the game is called off at its cut-off. Read off the booking and the clock,
so it says the same before and after anything records it.

**Never on the record**: leaving before the cut-off when the game still plays;
a game that was never booked. **A mark**: leaving before the cut-off when the
game is then called off; leaving after the cut-off when nobody takes the seat.

**Kept is a game whose hour came with every seat held**, for everybody in it.
**Nothing goes on the record of those who stayed** in a game that went ahead
short, or was called off at its cut-off because of somebody else's seat (the
mechanics §14.1): it is not a game they kept or broke. *Not turning up* is the
Game's to say (#547), and a game the club cancels is on nobody's (#547).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.bookings.domain.booking import Booking, CalledOff


@dataclass(frozen=True, slots=True)
class Keeping:
    """One player and one booked game, once it is settled: whether they kept
    it, and the moment that was decided — the hour, or the cut-off."""

    kept: bool
    at: Instant


@dataclass(frozen=True, slots=True)
class KeepingRecord:
    """What became of the booked games one player held a seat on — the *keeps
    plans* strand's whole input. **Per person**, and only the settled ones: a
    game still ahead is in neither half.

    ``last_at`` is the most recent moment one of them was settled — an hour
    that came, or a cut-off that called a game off."""

    kept: int
    broken: int
    last_at: Instant

    def __post_init__(self) -> None:
        invariant(
            self.kept >= 0 and self.broken >= 0,
            f"a negative count: {self.kept} kept, {self.broken} broken",
        )
        invariant(
            self.kept + self.broken >= 1,
            "a record with no settled booked game behind it is an absence, not a "
            "zero — absence is spelled by not being in the answer",
        )


def keeping_of(booking: Booking, player_id: UUID, *, now: Instant) -> Keeping | None:
    """Whether this player kept this booked game at ``now`` — ``None`` while
    it is not settled, and for a game that is nothing on their record."""

    if booking.booked_at is None:
        # Put to its club and never booked: nobody had a seat to keep.
        return None
    called_off = _called_off_at_the_cut_off(booking, now=now)
    if booking.called_off is not None and not called_off:
        return None
    left = next(
        (one for one in reversed(booking.departures) if one.player_id == player_id),
        None,
    )
    if player_id in booking.players:
        # Kept is the hour coming with every seat held; a game called off, or
        # one that went ahead short, puts nothing on the record of who stayed.
        whole = booking.is_booked and booking.open_seats == 0
        return (
            Keeping(kept=True, at=booking.start)
            if whole and now >= booking.start
            else None
        )
    if left is None:
        return None
    if left.at < booking.cut_off:
        # Free to leave — unless the game is then called off because of it.
        return Keeping(kept=False, at=booking.cut_off) if called_off else None
    # After the cut-off the seat was the leaver's to fill. Until rescues arrive
    # (#545) nobody takes it, so a game whose hour came went ahead without them.
    return Keeping(kept=False, at=booking.start) if now >= booking.start else None


def _called_off_at_the_cut_off(booking: Booking, *, now: Instant) -> bool:
    return booking.called_off is CalledOff.SHORT_AT_THE_CUT_OFF or (
        booking.short_at_the_cut_off(now=now)
    )

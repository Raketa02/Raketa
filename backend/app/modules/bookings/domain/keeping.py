"""Who kept a booked game, and who broke it — the record's rules (#544; the
mechanics §15.4).

**A booked game is a plan with a moment**, so whether somebody kept it is
*keeps plans*: it is settled when the game's hour comes, or when the game is
called off at its cut-off. Read off the booking and the clock, so it says the
same before and after anything records it.

**Never on the record**: leaving before the cut-off when the game still plays;
a game that was never booked; leaving when somebody then takes the seat (#545),
whatever becomes of the game. **Broken, in two ways Player reliability prices
apart** (``docs/adr/0195`` §1, #659 — the prices are ``player_score``'s): leaving
after the cut-off when nobody takes the seat, and leaving before it — or a card
not fixed in time losing the seat — when the game is then called off with that
seat still open.

**Kept is a game whose hour came with every seat held**, for everybody in it —
**whoever Didn't come included** (#659): a *Didn't come* is priced once, on
*shows up*, which is the Game's to say, and never also breaks the plan.
**Nothing goes on the record of those who stayed** in a game that went ahead
short, or was called off at its cut-off because of somebody else's seat (the
mechanics §14.1): it is not a game they kept or broke. **A game the club
cancels is on nobody's** (#547): not the people in it, and not a leaver whose
seat it left open.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from app.kernel import Instant
from app.modules.bookings.domain.booking import Booking, CalledOff


class Broken(StrEnum):
    """How a booked game was broken — two prices on Player reliability."""

    #: Left after the cut-off, and nobody took the seat: the game went ahead
    #: short.
    LEFT_AFTER_THE_CUT_OFF = "LEFT_AFTER_THE_CUT_OFF"
    #: Left before the cut-off — or a card not fixed in time lost the seat,
    #: which counts as leaving before it (Q113) — and the seat still open at
    #: the cut-off called the game off for everyone.
    CALLED_OFF_BY_LEAVING = "CALLED_OFF_BY_LEAVING"


@dataclass(frozen=True, slots=True)
class Keeping:
    """One player and one booked game, once it is settled: the moment that was
    decided — the hour, or the cut-off — and how it was broken, or ``None``
    when they kept it."""

    at: Instant
    broken: Broken | None = None

    @property
    def kept(self) -> bool:
        return self.broken is None


def keeping_of(booking: Booking, player_id: UUID, *, now: Instant) -> Keeping | None:
    """Whether this player kept this booked game at ``now`` — ``None`` while
    it is not settled, and for a game that is nothing on their record."""

    if booking.booked_at is None:
        # Put to its club and never booked: nobody had a seat to keep.
        return None
    called_off = _called_off_at_the_cut_off(booking, now=now)
    if booking.called_off is not None and not called_off:
        # Turned down, or cancelled by the club: nobody's doing (#547).
        return None
    left = next(
        (one for one in reversed(booking.departures) if one.player_id == player_id),
        None,
    )
    if player_id in booking.players:
        # Kept is the hour coming with every seat held; a game called off, or
        # one that went ahead short, puts nothing on the record of who stayed.
        whole = booking.is_booked and booking.is_whole
        if not whole or now < booking.start:
            return None
        return Keeping(at=booking.start)
    if left is None or not left.is_open:
        # Somebody took the seat (#545): whatever becomes of the game, it is
        # not because of this one.
        return None
    if left.at < booking.cut_off:
        # Free to leave — unless the game is then called off because of it.
        if not called_off:
            return None
        return Keeping(at=booking.cut_off, broken=Broken.CALLED_OFF_BY_LEAVING)
    # After the cut-off the seat was the leaver's to fill, and nobody took it:
    # a game whose hour came went ahead without them.
    if now < booking.start:
        return None
    return Keeping(at=booking.start, broken=Broken.LEFT_AFTER_THE_CUT_OFF)


def _called_off_at_the_cut_off(booking: Booking, *, now: Instant) -> bool:
    return booking.called_off is CalledOff.SHORT_AT_THE_CUT_OFF or (
        booking.short_at_the_cut_off(now=now)
    )

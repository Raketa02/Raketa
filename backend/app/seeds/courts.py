"""Which courts are claimed, and what state each claim is in.

Same rule as the two catalogs beside it: **a reservation is named for the state
it represents**, and the name is a checked claim rather than a comment. Three
plausible bookings would be one scenario — *a court is taken* — repeated three
times; what breaks a screen, and what ADR-0035 was written for, is the edges. So
this is a list of them: a block the club published and we must not pad, a court
a player bought outright, a claim that was given back and left its history
behind, and a claim wider than the game it is for.

**Two of the three holders are seeded, and the third is deliberately absent.** A
club block needs only Clubs; a booking needs a player, and players are modeled.
A **match hold** is a court the ladder is keeping aside for a match, and *when*
one is granted is the hold ladder's decision (ADR-0031,
`Raketa02/Raketa#71`) — seeding one here would decide what the ladder decides,
and the seeded match would then carry a `heldSince` nobody derived. Matches has
had an aggregate since `#66`; what it does not yet have is the ladder that grants
this. It arrives with the ticket that owns it.

**The window is a fixed absolute instant, not an offset from now.** A seed run
is idempotent, and *"next Tuesday at 18:00"* computed at run time is a different
Tuesday tomorrow — so a second run would claim a second court and the run that
creates nothing could never happen. The demo week (`Raketa02/Raketa#96`) is where
a week somebody can walk through arrives; these are the states the context has to
be able to represent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from app.kernel import MINUTES_PER_DAY, Instant, instant, minutes, shifted
from app.modules.courts.domain.reservation import HolderKind, Reservation
from app.modules.courts.domain.time_range import TimeRange, span

#: Monday, 7 September 2026, midnight UTC — the one anchor every seeded window
#: hangs off, written out rather than computed, so the same run twice is the
#: same state twice. Named for its weekday because somebody checking a screen
#: wants to know whether they are looking at a weekday evening or a Saturday.
SEED_MONDAY: Instant = instant(datetime(2026, 9, 7, tzinfo=timezone.utc))


def seed_slot(hour: int, *, day_offset: int = 0, length: int = 60) -> TimeRange:
    """A window on the seeded week, in UTC — the same one on every run.

    Offsets from `SEED_MONDAY` through the kernel's own arithmetic, so there is
    one anchor and not one per scenario, and moving the seeded week is a one-line
    edit rather than four.
    """

    return span(
        shifted(SEED_MONDAY, minutes(day_offset * MINUTES_PER_DAY + hour * 60)),
        minutes(length),
    )


@dataclass(frozen=True)
class ReservationClaim:
    """What a reservation's name promises, and how to tell whether it holds."""

    promise: str
    holds: Callable[[Reservation], bool]


@dataclass(frozen=True)
class SeedReservation:
    """One deterministic claim: which club's court, when, and held by whom.

    ``club_slug`` and ``category`` name the club catalog's own entries, so a
    reservation cannot point at a club that does not exist without the run
    stopping. ``player_slug`` is set exactly when ``held_by`` is a booking —
    a booking is a player buying a court, and there is no such thing as one
    without a buyer.
    """

    slug: str
    description: str
    claim: ReservationClaim
    club_slug: str
    category: str
    played: TimeRange
    held_by: HolderKind
    player_slug: str | None = None
    released: bool = False

    def __post_init__(self) -> None:
        if self.held_by is HolderKind.MATCH:
            raise ValueError(
                f"'{self.slug}' is match-held, and the hold ladder that grants "
                "a match its court is Raketa02/Raketa#71. Seed what is decided."
            )
        wants_player = self.held_by is HolderKind.BOOKING
        if wants_player != (self.player_slug is not None):
            raise ValueError(
                f"'{self.slug}': a booking names a buyer and nothing else does"
            )


def _claimed_exactly(reservation: Reservation) -> bool:
    return reservation.claimed == reservation.played


CLUB_BLOCK = SeedReservation(
    slug="court-the-club-blocked",
    description=(
        "A block the venue published itself — a league night, a lesson, a "
        "walk-in taken at the counter. It takes the court out of availability "
        "exactly as one of ours does, which is the property a stored counter "
        "could not have without the club console remembering to decrement it. "
        "And it is **never padded**: a club's own block is already padded "
        "however that club likes, so widening it again double-books the gap."
    ),
    claim=ReservationClaim(
        promise="a club-published block, claiming exactly the hour it plays",
        holds=lambda r: r.kind is HolderKind.CLUB and _claimed_exactly(r),
    ),
    club_slug="club-that-needs-a-turnaround",
    category="Padel · indoor",
    played=seed_slot(18),
    held_by=HolderKind.CLUB,
)

TURNAROUND_CLAIM = SeedReservation(
    slug="court-claimed-past-the-game",
    description=(
        "A claim Raketa created at a club that needs a quarter of an hour "
        "between bookings: the players get 19:00–20:00 and the court is held "
        "to 20:15. The played interval is what a reader is given; the claimed "
        "one is what the exclusion constraint enforces, and the two are "
        "different facts. It sits directly after `court-the-club-blocked` on "
        "the same court, which the half-open range is what allows."
    ),
    claim=ReservationClaim(
        promise="a claim wider than the game it is for",
        holds=lambda r: (
            r.claimed.end > r.played.end and r.claimed.start == r.played.start
        ),
    ),
    club_slug="club-that-needs-a-turnaround",
    category="Padel · indoor",
    played=seed_slot(19, length=60),
    held_by=HolderKind.BOOKING,
    player_slug="rating-well-established",
)

GIVEN_BACK = SeedReservation(
    slug="court-given-back",
    description=(
        "A claim that was released — the shape a withdrawn court hold leaves "
        "behind. The row stays, so *what happened to this court on Monday* is "
        "still answerable; the exclusion constraint is partial over the live "
        "rows, so it blocks nobody. Released, never deleted."
    ),
    claim=ReservationClaim(
        promise="a released claim that kept its row",
        holds=lambda r: not r.is_live and r.released_at is not None,
    ),
    club_slug="club-that-retired-a-court",
    category="Squash · glass back",
    played=seed_slot(20, day_offset=1),
    held_by=HolderKind.CLUB,
    released=True,
)

BOUGHT_OUTRIGHT = SeedReservation(
    slug="court-bought-outright",
    description=(
        "A player buying a court: a Booking that **holds** a reservation and "
        "is not one. The booking carries the buyer and the price they were "
        "quoted; everything about the court and the clock is read through the "
        "claim. Reassigning the court cannot move the price, because the two "
        "facts live on two records."
    ),
    claim=ReservationClaim(
        promise="a court bought outright, held by its booking",
        holds=lambda r: r.kind is HolderKind.BOOKING,
    ),
    club_slug="club-that-tightened-its-cap",
    category="Tennis · outdoor",
    played=seed_slot(17, day_offset=2, length=90),
    held_by=HolderKind.BOOKING,
    player_slug="rating-barely-established",
)

RESERVATIONS: tuple[SeedReservation, ...] = (
    CLUB_BLOCK,
    TURNAROUND_CLAIM,
    GIVEN_BACK,
    BOUGHT_OUTRIGHT,
)
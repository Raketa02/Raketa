"""A reservation: one court, one time range, claimed — and who holds it.

ADR-0035. **The only thing that can make a court unavailable**, and the reason
the double-booking defect is structurally impossible rather than merely unlikely:
two matches crossing their hold threshold in the same second cannot both take
court 3, because the second write is refused by the database.

**A record with a version, not an event-sourced stream** — ADR-0034's rule
applied one context over. A court's booking history is a query over reservations,
so there is nothing to fold.

**Two intervals, and they are different facts.**

- ``played`` is what the players get, and the only one anybody is ever shown.
- ``claimed`` is what excludes everybody else. For a reservation Raketa creates
  it is ``played`` widened by the club's ``turnaroundMin``; for one the **club**
  publishes it is ``played`` exactly, because a club's own block is already
  padded however that club likes and padding it again double-books the gap.

Whether to pad is therefore read off the **holder** rather than stored beside
it. A stored flag would be a second spelling of a fact the holder already
states, and the two can disagree; `tests/unit/test_reservation.py` says so.

**Released, never deleted.** A withdrawn court hold and a cancelled booking both
leave their row standing with ``released_at`` written on it, because *"a court's
booking history is a query over reservations"* is false the moment a row can
vanish. The exclusion constraint is therefore partial — it covers the live rows
only — exactly as the club series' unique indexes cover the open row only.

**The court is named internally at once and published late.** That is what makes
the exclusion real while keeping ADR-0035's promise that *"the category was
bought, not the court"*: ``published(now)`` hands out the category always and the
court only from ``court_named_at(start)``, fifteen minutes before play.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias, final
from uuid import UUID

from app.kernel import Instant, Minutes, court_named_at, exhaustive, minutes

from app.modules.courts.domain.errors import ReservationAlreadyReleased
from app.modules.courts.domain.time_range import TimeRange


class HolderKind(str, Enum):
    """The three things that can hold a court, and nothing else can.

    ``BOOKING`` and ``MATCH`` are ADR-0035's two named holders — *"a Booking, a
    player buying a court outright"* and *"a court hold, a match's speculative
    reservation"*. ``CLUB`` is the third the same decision implies without
    naming: `turnaroundMin` *"never pads one the club publishes"*, so a
    club-published block is a reservation whose holder is the venue itself —
    a league night, a lesson, a walk-in taken at the counter.
    """

    BOOKING = "booking"
    MATCH = "match"
    CLUB = "club"


@final
@dataclass(frozen=True)
class BookingHeld:
    """A player bought the court outright; the Booking holds this reservation."""

    booking_id: UUID


@final
@dataclass(frozen=True)
class MatchHeld:
    """A match's speculative hold, granted and withdrawn by the hold ladder.

    Nobody has bought anything. The ladder is not this context's business
    (ADR-0031, `Raketa02/Raketa#71`): what belongs here is that the court is
    claimed and by whom.
    """

    match_id: UUID


@final
@dataclass(frozen=True)
class ClubHeld:
    """The club's own block, published by the venue rather than sold by us."""


Holder: TypeAlias = BookingHeld | MatchHeld | ClubHeld


def holder_kind(holder: Holder) -> HolderKind:
    match holder:
        case BookingHeld():
            return HolderKind.BOOKING
        case MatchHeld():
            return HolderKind.MATCH
        case ClubHeld():
            return HolderKind.CLUB
        case _:  # pragma: no cover - `exhaustive` never returns
            exhaustive(holder)


def is_platform_created(holder: Holder) -> bool:
    """Did Raketa create this reservation, or did the club publish it.

    Derived from the holder rather than stored, because the holder already says
    it: a booking and a match hold are both ours, a club block is the venue's.
    A column beside them would be a second copy of one fact, and the day the two
    disagree the turnaround is applied to a block that was already padded.
    """

    return holder_kind(holder) is not HolderKind.CLUB


@final
@dataclass(frozen=True)
class PublishedCourt:
    """What a reader outside this context may be told about the court.

    ``court_id`` is ``None`` until fifteen minutes before play. The category is
    always there, because that is what was bought and what the price attaches
    to — a card that showed court 3 and then showed court 5 would have promised
    something the club never sold.
    """

    category_id: UUID
    court_id: UUID | None

    @property
    def names_a_court(self) -> bool:
        return self.court_id is not None


@final
@dataclass
class Reservation:
    """One court, one time range, claimed — with a version and a release.

    ``version`` is the **stored** row version and is not touched here: the
    repository compares it on the way out and bumps it, the same split
    ``Club`` makes. An aggregate that incremented its own would have to be told
    what the store did next, and the two counters would be one fact twice.
    """

    id: UUID
    club_id: UUID
    court_id: UUID
    category_id: UUID
    played: TimeRange
    claimed: TimeRange
    holder: Holder
    released_at: Instant | None = None
    version: int = 0

    def __post_init__(self) -> None:
        if not self.claimed.overlaps(self.played):
            raise ValueError(
                "a claimed interval that does not cover the play it is for: "
                f"{self.claimed} vs {self.played}"
            )
        if self.claimed.start > self.played.start or self.claimed.end < self.played.end:
            raise ValueError(
                "a claimed interval narrower than the play it is for: "
                f"{self.claimed} vs {self.played}"
            )

    @classmethod
    def claim(
        cls,
        *,
        reservation_id: UUID,
        club_id: UUID,
        court_id: UUID,
        category_id: UUID,
        played: TimeRange,
        holder: Holder,
        turnaround: Minutes = minutes(0),
    ) -> "Reservation":
        """Claim a court for a window, widened by the turnaround if it is ours.

        The one constructor. ``claimed`` is never passed in, so no caller can
        assemble a reservation whose claim disagrees with its holder about
        whether the club's turnaround applies.
        """

        return cls(
            id=reservation_id,
            club_id=club_id,
            court_id=court_id,
            category_id=category_id,
            played=played,
            claimed=claimed_interval(played, holder, turnaround),
            holder=holder,
        )

    @property
    def is_live(self) -> bool:
        """Live means *still claiming the court*. Only a live row excludes."""

        return self.released_at is None

    @property
    def kind(self) -> HolderKind:
        return holder_kind(self.holder)

    def published(self, *, now: Instant) -> PublishedCourt:
        """The category always; the court from fifteen minutes before play."""

        named = now >= court_named_at(self.played.start)
        return PublishedCourt(
            category_id=self.category_id,
            court_id=self.court_id if named else None,
        )

    def release(self, *, at: Instant) -> None:
        """Give the court back, keeping the row.

        Idempotent in neither direction on purpose: releasing twice would move
        the instant a claim ended, which is history rewritten rather than
        recorded, and a second release is a caller that has lost track of what
        it holds.
        """

        if self.released_at is not None:
            raise ReservationAlreadyReleased()
        self.released_at = at

    def reassign_to(self, court_id: UUID) -> None:
        """Swap which court this claim names. Ordinary, and only within a category.

        *"Reassignment — swapping which court a live reservation names — is an
        ordinary operation, legal wherever exclusion still holds"* (ADR-0035).
        Two things are therefore **not** touched: the category, because that is
        what was bought and what the price attaches to; and the two intervals,
        because moving a court does not move a game. Whether exclusion still
        holds is the database's answer, given on the write.
        """

        if self.released_at is not None:
            raise ReservationAlreadyReleased()
        self.court_id = court_id


def claimed_interval(
    played: TimeRange, holder: Holder, turnaround: Minutes
) -> TimeRange:
    """What a reservation for ``played``, held by ``holder``, takes off the court.

    Written out rather than inlined because it is the whole of ADR-0035's
    turnaround rule and `tests/unit/test_reservation.py` reads it directly: ours
    is widened, the club's is not, and the player is always shown ``played``.
    """

    if not is_platform_created(holder):
        return played
    return played.widened_by(turnaround)

"""A club's policy: exactly eight fields, versioned as one row.

ADR-0078's membership test is a single sentence — **a club decision that changes
what happens to a player inside a match**. Everything a club declares that fails
it (``alloc``, ``checkinMin``, ``slotDisc``, the three cancellation refund
tables, ``langs``, ``legal``, ``pm``) is on the club record and is not versioned,
because a row holding a facility-rules PDF makes every revision of that PDF open
a policy version and buries the one question versioning exists to answer.

**Versioned whole, not per field** (ADR-0077), so *what was this club's policy on
Friday at 16:00* is one query rather than one per field.

**Six of the eight name a live reader; two ship dark, deliberately** — see
``free_cancel_hours`` and ``counts_cash`` below.

Durations are the kernel's ``Minutes`` wherever something reads them as a
duration, so the projection onto ``HoldPolicy`` is an identity rather than a
conversion — two conversions of one threshold is the failure the kernel exists
to make unreachable. ``free_cancel_hours`` is the exception and says why.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.kernel import HoldPolicy, Minutes, hours, minutes

#: The eight field names, written out. A row that grows a ninth without a named
#: reader is the thing ADR-0078 asks the next session to refuse, and
#: `tests/unit/test_club_policy.py` is where that refusal is stated.
POLICY_FIELDS = (
    "window",
    "join_cut",
    "max_hold_age",
    "prob_hold",
    "rebooking_credit",
    "free_cancel_hours",
    "turnaround_min",
    "counts_cash",
)


@final
@dataclass(frozen=True)
class ClubPolicy:
    """The eight fields, with ADR-0078's defaults."""

    #: The club's cancellation window. `commit` is the **earlier** of
    #: `start - window` and the twelve-hour backstop, so this can only ever move
    #: commitment forwards.
    window: Minutes = hours(24)

    #: How long before the start a match stops accepting anybody.
    join_cut: Minutes = minutes(30)

    #: How long a speculative hold may sit before the club takes the court back,
    #: measured from `held_since` (ADR-0031).
    #:
    #: Three-valued, and the third value is the honest one. ``None`` — never
    #: stale, hold to the ladder floor. A positive number — honoured, **with no
    #: platform floor under it**: ADR-0078 refuses one as unenforceable against
    #: a club that simply stops publishing courts. ``0`` — *this club does not
    #: hold speculatively at all*, said plainly rather than performed by a hold
    #: that dies an hour after it is granted.
    max_hold_age: Minutes | None = None

    #: Whether the club publishes a demand model, which is what lets it extend a
    #: hold the ladder has already lapsed. `clubExtended` and `clubFill` live on
    #: the **match**, written by the club; this only gates them, and extension
    #: may only ever lengthen a hold (ADR-0031 Rule 12).
    prob_hold: bool = False

    #: Does this club offer rebooking credit when a committed match is short at
    #: the checkpoint. One boolean, replacing v37's `checkpoint` string and
    #: `CLUBS.rebooking` — two independently seeded fields encoding one fact,
    #: with nothing enforcing agreement (ADR-0078 closes GAP-C3 by deletion).
    rebooking_credit: bool = False

    #: The moment the owner's last free choice expires, as a count of **hours**
    #: before the start; ``None`` means the club offers none, which is the
    #: default because the prototype's 24 lived inside a refund table whose money
    #: meaning ADR-0047 removed.
    #:
    #: **The one field here that is not `Minutes`.** It is named for its unit
    #: because ADR-0078 names it that way, and it is the only field of the eight
    #: with no reader to want a duration — so there is nothing to convert *to*.
    #: The day a reader exists it takes `hours(free_cancel_hours)`.
    #:
    #: **Ships read by nobody (#64).** Its only two consumers are the owner
    #: messages ruled out of scope on #44 — specified and undeliverable. It ships
    #: anyway because the fact is cheap to capture while a human is entering the
    #: club and expensive to backfill across every club later. Do not read that
    #: silence as *nobody needed this*.
    free_cancel_hours: int | None = None

    #: Widens the **claimed** interval of a reservation Raketa creates, and never
    #: pads one the club publishes — those are already padded however that club
    #: likes, and padding them again double-books the gap. The player is always
    #: shown the **played** interval.
    turnaround_min: Minutes = minutes(0)

    #: Does this club take cash at its counter. Defaults **on**, because every
    #: Polish racket club does and entering nine of them as *refuses cash*
    #: describes none of them.
    #:
    #: **Ships read by nobody (#64).** Whether Raketa *offers* pay-at-the-club is
    #: a separate, platform-wide gate on a marking surface existing — and there
    #: is none, so nothing can produce a mark. ADR-0059's refusal rule for a late
    #: mark is therefore unexercised in v1. A gate is stronger than a default: a
    #: default can be overridden into the failure, a gate cannot. Building the
    #: console's mark screen silently opens this channel at every club that has
    #: it true, which is all of them.
    counts_cash: bool = True

    def __post_init__(self) -> None:
        if self.window <= 0:
            raise ValueError(f"club cancellation window: {self.window}")
        if self.join_cut < 0:
            raise ValueError(f"club join cutoff: {self.join_cut}")
        if self.max_hold_age is not None and self.max_hold_age < 0:
            raise ValueError(f"club maximum hold age: {self.max_hold_age}")
        if self.free_cancel_hours is not None and self.free_cancel_hours < 0:
            raise ValueError(f"club free cancellation window: {self.free_cancel_hours}")
        if self.turnaround_min < 0:
            raise ValueError(f"club turnaround: {self.turnaround_min}")

    @property
    def holds_speculatively(self) -> bool:
        """``maxHoldAge = 0`` is *this club does not hold speculatively at all*.

        Stated once, here, so no caller has to remember that zero is a third
        value rather than the smallest of the second kind.
        """

        return self.max_hold_age != 0

    def hold_policy(self) -> HoldPolicy:
        """The four fields the hold ladder reads, as the kernel's own type.

        An identity on all four — no floor, no clamp, no default substituted for
        a value the club chose. That is the whole content of *"no platform floor
        is applied anywhere"*: there is no arithmetic here to hide one in.

        The other four fields are read by money, by reservations and by nobody,
        and naming them in the kernel would be the aggregate shape
        ``app/kernel/matches.py`` refuses to be.
        """

        return HoldPolicy(
            window=self.window,
            join_cut=self.join_cut,
            max_hold_age=self.max_hold_age,
            prob_hold=self.prob_hold,
        )

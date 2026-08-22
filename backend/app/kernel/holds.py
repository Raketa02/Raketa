"""Is a physical court being kept aside for this match, right now, and why.

Two layers, composed, in this order — the base ladder that holds a court in
proportion to certainty, and the club's two amendments to it. A specification
written from the base alone is silently and confidently wrong: a club that caps
speculative holds takes its court back days before the ladder's own tier would
have released it.

**Rule 11 governs and Rule 12 is restated**
(``docs/adr/0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md``): a club
may hold longer than the ladder promises, and never shorter *at the same level
of certainty*. The two rules only look contradictory until it is seen that they
price one invariant on two axes — the ladder measures certainty in paid seats,
the club measures it in elapsed time, and a match that has sat at two seats for
seventy-one hours has falsified the premise the hold was granted on.

**Staleness is never latched.** It is recomputed from the current facts, so a
third payment closes the `filled < n-1` guard and the hold is live again. A card
may therefore go *back* from released to held, and any conformance suite
assuming hold state moves one way is wrong.

**Every comparison is strictly one-directional**, on instants. At exactly the
tier's release moment the hold lapses; a millisecond earlier it holds. Written
with `>=` on remaining time instead, a match sitting on the boundary flaps
between held and released on every recomputation, and re-notifies each time.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import final

from app.kernel.invariants import invariant
from app.kernel.matches import (
    MatchKind,
    MatchRecord,
    filled,
    is_full,
    seat_count,
)
from app.kernel.time import Instant, Minutes, elapsed_minutes, hours, minutes, shifted

#: The two speculative tiers, as how long before the start each one lapses.
#: `FAR` is two paid seats and `NEAR` is one seat short of full — the bar rises
#: with certainty, and so does the length of the promise.
_HOLD_FAR = hours(12)
_HOLD_NEAR = hours(4)


class HoldKind(Enum):
    """How firmly the court is held, and therefore what may still take it.

    ``HARD`` is a court nothing else can be sold; ``SOFT`` is one the ladder is
    keeping on the premise that certainty will rise; ``NONE`` is a court the
    club is still selling to anybody.
    """

    HARD = "hard"
    SOFT = "soft"
    NONE = "none"


class HoldReason(Enum):
    """Why the hold is what it is.

    Five of these reach a player's card — ``COMMITTED``, ``FAR``, ``NEAR``,
    ``STALE`` and ``EXTENDED`` — and they are the five reasons ``Raketa02/Raketa#74``
    renders as a reason plus its facts rather than as free text. The rest are
    diagnosis: a card that is not describing a court does not name one.
    """

    #: A private court belongs to whoever bought it.
    PRIVATE = "private"
    #: The club committed a court by hand, outside the ladder.
    CLUB = "club"
    #: The match is committed, so the court is pinned and cannot lapse.
    COMMITTED = "committed"
    #: Every seat is paid.
    FULL = "full"
    #: One seat short, and still more than four hours out.
    NEAR = "near"
    #: Two seats paid, and still more than twelve hours out.
    FAR = "far"
    #: One seat short, and inside four hours: the near tier has lapsed.
    NEAR_LAPSED = "nearLapsed"
    #: Two seats paid, and inside twelve hours: the far tier has lapsed.
    FAR_LAPSED = "farLapsed"
    #: Not enough paid seats to hold anything yet.
    THIN = "thin"
    #: The club caps how long a speculative hold may sit, and this one is past it.
    STALE = "stale"
    #: The club published a demand model and extended a hold the ladder lapsed.
    EXTENDED = "extended"
    #: The club does not hold speculatively at all.
    NO_SPECULATIVE_HOLD = "noSpeculativeHold"


@final
@dataclass(frozen=True)
class Hold:
    """The composed answer: how firmly, why, and the two facts a card needs."""

    kind: HoldKind
    why: HoldReason

    release_at: Instant | None = None
    """When this tier lapses, for a hold the ladder is keeping."""

    age: Minutes | None = None
    """How long the hold had actually sat, for one it has just taken back.

    The **hold's** age and never the club's threshold. A hold that has sat
    seventy-one hours under a forty-eight-hour cap says seventy-one: the card
    promising an age is the place the marketplace's promise is being weakened,
    and it is the last place to print a number that is not the one meant.
    """


def is_held(hold: Hold) -> bool:
    """Whether a court is being kept aside at all.

    Read off the ladder, never off a stored court id or a denormalised copy of
    this answer: the two disagree for the whole window between a threshold
    crossing and the next write, and the ladder is the one that is right.
    """

    return hold.kind is not HoldKind.NONE


def court_hold(record: MatchRecord, now: Instant) -> Hold:
    """The composed hold: the base ladder, then the club's two amendments."""

    base = _base_hold(record, now)

    # A private, hand-locked or committed court is never stale and never
    # extended — there is nothing speculative left about it to amend. Written
    # off the record rather than off the base hold's reason, because that is the
    # claim: these three facts put a court beyond the club's two amendments.
    if (
        record.kind is MatchKind.PRIVATE
        or record.court_locked
        or record.committed_at is not None
    ):
        return base

    stale = _staleness(record, now, base)
    if stale is not None:
        return stale

    return _extension(record, base) or base


def _base_hold(record: MatchRecord, now: Instant) -> Hold:
    """Certainty, priced in paid seats. Four hard rungs, then the two soft tiers."""

    if record.kind is MatchKind.PRIVATE:
        return Hold(HoldKind.HARD, HoldReason.PRIVATE)
    if record.court_locked:
        return Hold(HoldKind.HARD, HoldReason.CLUB)
    if record.committed_at is not None:
        # Rule 3, and the reason a committed match cannot lose its court at
        # T-4h: commitment promotes whatever was held to hard, unconditionally.
        return Hold(HoldKind.HARD, HoldReason.COMMITTED)
    if is_full(record):
        return Hold(HoldKind.HARD, HoldReason.FULL)

    seats = seat_count(record)
    paid = filled(record)

    # Two-player sports skip the soft tiers entirely: there is no *nearly full*
    # between one seat and two, so singles goes thin straight to full.
    if seats <= 2:
        return Hold(HoldKind.NONE, HoldReason.THIN)

    # Zero is a club opting out of speculative holding, not a club whose every
    # hold is instantly stale. The distinction is visible: an opted-out club
    # never grants a hold, so nothing is ever taken back from anybody.
    if record.policy.max_hold_age == 0:
        if paid >= 2:
            return Hold(HoldKind.NONE, HoldReason.NO_SPECULATIVE_HOLD)
        return Hold(HoldKind.NONE, HoldReason.THIN)

    if paid >= seats - 1:
        return _tier(record, now, _HOLD_NEAR, HoldReason.NEAR, HoldReason.NEAR_LAPSED)
    if paid >= 2:
        return _tier(record, now, _HOLD_FAR, HoldReason.FAR, HoldReason.FAR_LAPSED)

    return Hold(HoldKind.NONE, HoldReason.THIN)


def _tier(
    record: MatchRecord,
    now: Instant,
    span: Minutes,
    live: HoldReason,
    lapsed: HoldReason,
) -> Hold:
    """One soft tier, and the one-directional comparison that keeps it steady.

    `now < release` and never `<=`: at exactly the release moment the hold is
    gone, on this recomputation and on every later one.
    """

    release = shifted(record.start, minutes(-span))
    if now < release:
        return Hold(HoldKind.SOFT, live, release_at=release)
    return Hold(HoldKind.NONE, lapsed)


def _staleness(record: MatchRecord, now: Instant, base: Hold) -> Hold | None:
    """Rule 11: a club may take back a hold that has stopped earning itself.

    Three conditions, and the third is deliberate rather than accidental: a
    match **one seat short is never stale**, whatever its age, because certainty
    genuinely has risen and that is the level at which the floor binds. So
    staleness may reclaim a far-tier hold and may never touch a near-tier one —
    which also means there is no hard hold at `n-1`.

    Measured from `held_since`. A match that spent sixty hours at one paid seat
    and then earned a hold has a fresh hold and an old match; anchored to
    creation it would be stale on arrival, punishing exactly the match that just
    improved.
    """

    cap = record.policy.max_hold_age
    if base.kind is not HoldKind.SOFT or cap is None:
        return None
    if filled(record) >= seat_count(record) - 1:
        return None

    # A soft hold is a court being kept aside, so the record must say since
    # when. Reading a missing `held_since` as *no age* would silently disable
    # the club's cap for that match, which is the failure nobody would see.
    held_since = invariant(
        record.held_since,
        "a soft hold under a club cap with no held_since to age it from",
    )
    # `now >= held_since + cap`, spelled as its negation, and one-directional the
    # same way the tiers are: the hold goes stale **at** the cap and not a moment
    # after it. Written `now <= ...` instead, the change lands a minute past the
    # only instant the schedule knows about, so the wake arrives, finds the hold
    # still fresh, and re-arms nothing — the card then says *held* until the next
    # unrelated write. The wake property test in `tests/unit/test_next_wake_at.py`
    # is what found that, and it is the whole reason both halves read one list.
    if now < shifted(held_since, cap):
        return None

    return Hold(
        HoldKind.NONE,
        HoldReason.STALE,
        age=elapsed_minutes(held_since, now),
    )


def _extension(record: MatchRecord, base: Hold) -> Hold | None:
    """Rule 12: a club may hold longer than the ladder promised.

    Only ever *longer*: the extension applies to a hold the ladder has just
    lapsed, never to one it is still keeping, and never to a match too thin to
    have earned one. Both halves come from published club facts — the club has
    to have a demand model and to have said so about this match.
    """

    if base.kind is not HoldKind.NONE:
        return None
    if base.why not in (HoldReason.NEAR_LAPSED, HoldReason.FAR_LAPSED):
        return None
    if not (record.club_extended and record.policy.prob_hold):
        return None
    return Hold(HoldKind.SOFT, HoldReason.EXTENDED)


def hold_boundaries(record: MatchRecord) -> tuple[Instant, ...]:
    """Every instant *this* ladder compares the clock against, for this record.

    The hold ladder owns its own thresholds, so the wake function can ask for
    them instead of restating them. That is what makes *a threshold cannot exist
    in the ladder and be missing from the schedule* true by construction rather
    than by two lists being kept in step — and the tiers are exactly where the
    seat count decides which threshold applies, which is why the wake set has to
    be recomputed on every write.

    Empty where nothing speculative is in play: a private, hand-locked,
    committed or complete court has no tier to lapse, a two-player sport has no
    tiers at all, and a club that does not hold speculatively grants nothing to
    take back.
    """

    if (
        record.kind is MatchKind.PRIVATE
        or record.court_locked
        or record.committed_at is not None
        or is_full(record)
        or seat_count(record) <= 2
        or record.policy.max_hold_age == 0
        or filled(record) < 2
    ):
        return ()

    span = _HOLD_NEAR if filled(record) >= seat_count(record) - 1 else _HOLD_FAR
    moments = [shifted(record.start, minutes(-span))]

    cap = record.policy.max_hold_age
    if cap is not None and record.held_since is not None:
        moments.append(shifted(record.held_since, cap))

    return tuple(moments)

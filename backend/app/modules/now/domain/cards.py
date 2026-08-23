"""The facts every match card composes, whichever region it sits in.

Two regions draw a match card and they draw the same one: the enrolled strip
composes it for a match the viewer is **committed** to, and the ranked shelves
compose it for a match she is being **suggested**. What differs between them is
which facts exist — a suggestion has no departure, no score and no refund — and
never how a fact that exists is composed.

These two are the facts *every* match card carries, so they live here rather
than in one composer with the other importing a private name from it. Both are
pure functions of the record and the clock, which is the whole reason they can
be shared at all: the counting is by money and the hold is off the ladder, and
neither reads a viewer.
"""

from __future__ import annotations

from app.kernel import (
    Instant,
    MatchRecord,
    court_hold,
    filled,
    held_unpaid,
    match_end,
    seat_count,
    turned_up,
)

from app.modules.now.domain.screen import HoldNote, SeatCounts
from app.modules.now.domain.vocabulary import CARD_HOLD_REASON_OF


def counts_of(record: MatchRecord, *, now: Instant) -> SeatCounts:
    """Seats paid, seats merely held, and — once it has been played — who came.

    **Counting is by money** (ADR-0073): ``paid`` is the only count that means
    anything, and a held-and-unpaid seat is its own number beside it rather than
    folded into it. Counting people would tell four of them a match is full
    while a seat may still lapse; suppressing holds is the same lie in reverse.

    ``turned_up`` is present exactly once the court booking is behind us, which
    is a **clock** condition and not a judgement about a situation. Before that
    nobody has played and a number would be a claim about the future.
    """

    return SeatCounts(
        seats=seat_count(record),
        paid=filled(record),
        held=held_unpaid(record),
        turned_up=turned_up(record) if now >= match_end(record) else None,
    )


def hold_note(record: MatchRecord, *, now: Instant) -> HoldNote | None:
    """Why a court is being kept aside, in the five reasons a card names.

    Composed off the ladder every time and never read off ``held_since``: the
    two disagree for the whole window between a threshold crossing and the next
    write, and the ladder is the one that is right.
    """

    hold = court_hold(record, now)
    reason = CARD_HOLD_REASON_OF[hold.why]
    if reason is None:
        return None
    return HoldNote(
        reason=reason, age_minutes=None if hold.age is None else int(hold.age)
    )

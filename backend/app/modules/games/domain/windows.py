"""The three clocks, and what each of them is measured against.

**None of them is ADR-0048's number, because none of ADR-0048's has anything to
run from.** That record clocked entry from *the final point* and the result
window from *the match end*; a challenge here carries a ``Window`` — ``TODAY``,
``WEEKEND`` — and never a date, a time or a court, so there is no final point to
count from and the numbers had to be re-derived rather than copied
(``docs/adr/0137``).

**Nothing here reads a clock.** The caller says when the line-up completed and
when a score was put on the table, exactly as ``window_of`` is handed what day it
is.

**None of these is configuration.** They are what a player is promised, which is
behaviour a domain test can observe, and an environment that could select one
could select a rule that is true on a laptop and false in production.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from app.kernel import Instant, instant

#: How long a plan is allowed to become a game. **One ordinary week**, and that
#: is the only calendar this product has: the availability grid is *an ordinary
#: week*, and every ``Window`` — ``TODAY``, ``TOMORROW``, ``WEEKEND``,
#: ``THIS_WEEK``, ``ANY`` — is a statement about one. A table of one horizon per
#: window was rejected: ``ANY`` has no horizon at all, and a window is *a label
#: on the search*, never a proposed time.
PLAN_HORIZON: Final = timedelta(days=7)

#: How long after the horizon somebody may still say *we played*. **Twenty-four
#: hours, on a reason of its own.** It used to borrow the challenge's answer
#: window — *a day is what this platform already asks of a person it needs an
#: answer from* — and that window is now forty-eight hours
#: (``docs/adr/0151``). The citation goes rather than standing: an argument
#: pointing at a fact that has moved is worse than no argument, because it reads
#: as agreement between two numbers that have stopped agreeing.
#:
#: What keeps it at a day is ADR-0145 §5's interlock. ADR-0144 clamps the plan's
#: day chips at ``planned_at + PLAN_HORIZON`` once a game exists — before one,
#: the clamp runs from the challenge's send and this record has no say
#: (``docs/adr/0164`` §4) — and entry closes one grace after that, so this
#: number is exactly what makes **every plannable day leave at least
#: twenty-four hours to say *we played***. Kept as its own constant rather than
#: folded into *eight days*, because gluing the two would hide both arguments.
ENTRY_GRACE: Final = timedelta(hours=24)

#: How long a score stands before silence confirms it. ADR-0048's day, kept for
#: ADR-0048's reason: the prompt reaches nobody who has not opened the app, and
#: shortening it without a notification channel reintroduces the discarded-game
#: problem the flow was designed to remove.
#:
#: **It did not move when the challenge's answer window did, and the difference
#: is what the default does.** The two were the same twenty-four hours until
#: ``docs/adr/0151`` doubled that one for reaching nobody who has not opened the
#: app — the very coupling this constant already records. What separates them is
#: that silence on a proposed score **confirms** it, while silence on an
#: invitation **costs you the game**: a window whose default is benign can be
#: short, and one whose default takes the game away has to be long enough to
#: actually reach somebody. Written down because otherwise the next reader
#: re-aligns two numbers that have stopped being one.
PROPOSAL_WINDOW: Final = timedelta(hours=24)

#: How long an acceptance waits before it settles anything. **Six hours, not
#: thirty minutes.** ADR-0048 chose half an hour when the prompt appeared on
#: court inside a thirty-minute result window and everybody was still at the
#: club; entry now happens at home, possibly days later, and a grace that binds
#: only when both opponents are on their phones at once does not do the job it
#: exists for — *somebody is always slower to their phone*.
#:
#: An **admitted hypothesis**, with its falsifiers named: counters arriving
#: between this grace and the proposal's close are the objections it exists to
#: protect, and the share of results settled by an explicit acceptance rather
#: than by silence says whether accepting is still worth a tap.
ACCEPTANCE_GRACE: Final = timedelta(hours=6)


def entry_closes_at(planned_at: Instant) -> Instant:
    """When *we played* stops being sayable, and the game becomes a ghost.

    Past it the game reads as never played whether or not anything swept it,
    which is what makes the answer to *did this happen* the same at every
    instant.
    """

    return instant(planned_at + PLAN_HORIZON + ENTRY_GRACE)


def proposal_closes_at(proposed_at: Instant) -> Instant:
    """When the other side's silence stops being an answer they might still give.

    Dated from the proposal **or from the correction that re-dated it**: the
    other side is answering a score, and a score they have not seen has not
    started their day.
    """

    return instant(proposed_at + PROPOSAL_WINDOW)


def acceptance_settles_at(proposed_at: Instant) -> Instant:
    """When an acceptance of this proposal becomes final.

    Measured from the **proposal**, not from the acceptance: the person the grace
    protects is the opponent who has not read the score yet, and their clock
    started when the score was put in front of them.
    """

    return instant(proposed_at + ACCEPTANCE_GRACE)

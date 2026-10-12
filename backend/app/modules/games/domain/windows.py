"""The three clocks, and what each of them is measured against.

**None of them is ADR-0048's number.** That record clocked entry from *the final
point* and the result window from *the match end*; these were re-derived for
games that carried no hour (``docs/adr/0137``), and a booked game's entry now
runs from the end of its hour (#541).

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

#: How long a game **with no hour** is allowed to be played: **one ordinary
#: week** from when it was arranged. Every game a booking opens has its hour
#: (#541), so this measures only a stream written before bookings, which carries
#: none — kept so such a stream still folds to an end.
PLAN_HORIZON: Final = timedelta(days=7)

#: How long after the game somebody may still say *we played* — after its
#: booked hour's end, or after the horizon of a game with no hour. **Twenty-four
#: hours**: the day this platform asks of a person it needs an answer from, and
#: what makes **every game leave at least twenty-four hours to say *we
#: played***. Kept as its own constant rather than folded into a game's length,
#: because gluing the two would hide both arguments.
ENTRY_GRACE: Final = timedelta(hours=24)

#: How long a score stands before silence settles it — **the answer window**.
#: ADR-0048's day, kept for ADR-0048's reason: the prompt reaches nobody who has
#: not opened the app, and shortening it reintroduces the discarded-game problem
#: the flow was designed to remove.
#:
#: **A day is short enough because of what the default does**: silence on a
#: proposed score **settles** it, and a window whose default is benign can be
#: short. An agreement settles at once and waits on nothing (#654;
#: ``docs/adr/0195`` §5): the six-hour grace an acceptance once ran out is
#: retired, and with it the counter that could still beat one.
PROPOSAL_WINDOW: Final = timedelta(hours=24)

#: How long a **booked** game lasts: one hour, every sport (the mechanics §2).
#: A booking opens a game with its hour on it (#541), and that game's entry
#: window runs from the hour's end rather than from a week of not knowing when.
A_BOOKED_GAME: Final = timedelta(hours=1)

#: How long a player reported as not turning up has to say they did (#547; the
#: mechanics §15.3, §18). **A day, the result's own day**: silence on a score
#: confirms it after twenty-four hours, and silence on a report does the same —
#: the same reach to somebody who has not opened the app, for the same reason.
NO_SHOW_DISPUTE_WINDOW: Final = timedelta(hours=24)

#: How long after a **booked** game's hour starts it can still ask anything of
#: its players — **unless a score is put on its table again** (#613): its hour,
#: the day to say *we played*, and then the day a score made at the last moment
#: waits for its answer, or a report made then for its dispute. Every term is a
#: clock above, so lengthening one moves this with it.
#:
#: **A score put on the table again reaches past it.** A correction re-dates its
#: side's score, and that side may correct it again while the other side has
#: not answered — so a score can wait on a player for as long as its side keeps
#: correcting it, and a counter made meanwhile waits a day of its own. A reader
#: bounding its read by this looks for those apart
#: (``scores_still_waiting_since``).
A_BOOKED_GAME_NEEDS_ITS_PLAYERS_FOR: Final = (
    A_BOOKED_GAME + ENTRY_GRACE + max(PROPOSAL_WINDOW, NO_SHOW_DISPUTE_WINDOW)
)


def entry_closes_at(
    planned_at: Instant, *, starts_at: Instant | None = None
) -> Instant:
    """When *we played* stops being sayable, and a full court nobody recorded
    reads *Played · no score* (#655).

    Past it the game reads so whether or not anything swept it, which is what
    makes the answer to *did this happen* the same at every instant.

    **A booked game knows its hour** (``starts_at``, #541): it is played then,
    so the grace runs from that hour's end. A booking may be a fortnight ahead,
    and a week from the moment it was booked would end a game before it was
    played. A game with no hour — a stream written before bookings — has its
    week; a reader holding a ``Game`` asks ``Game.entry_closes_at``, which
    passes it.
    """

    if starts_at is not None:
        return instant(starts_at + A_BOOKED_GAME + ENTRY_GRACE)
    return instant(planned_at + PLAN_HORIZON + ENTRY_GRACE)


def proposal_closes_at(proposed_at: Instant) -> Instant:
    """When the other side's silence stops being an answer they might still give.

    Dated from the proposal **or from the correction that re-dated it**: the
    other side is answering a score, and a score they have not seen has not
    started their day.
    """

    return instant(proposed_at + PROPOSAL_WINDOW)


def scores_still_waiting_since(now: Instant) -> Instant:
    """The earliest a score can have been put on the table — proposed,
    corrected or countered — and still wait for an answer at ``now`` (#613).

    A lone score waits a day from when it was last put there, two scores a day
    from the later, and an agreement settles at once — so **every score still
    waiting was put on the table inside the last day**, however long ago its
    game was played.
    """

    return instant(now - PROPOSAL_WINDOW)


def dispute_closes_at(reported_at: Instant) -> Instant:
    """When a player reported as not turning up can no longer dispute it, and
    the report stands (#547)."""

    return instant(reported_at + NO_SHOW_DISPUTE_WINDOW)

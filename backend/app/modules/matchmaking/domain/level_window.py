"""The level window, and the newcomer window that tightens it.

**Two people are close enough to play when ``|Δμ| < LEVEL_TOL``**, at the
tolerance the curve itself saturates at — the same number, so the window and
the forecast cannot drift apart (``docs/adr/0103``). The new games ask it
of every pair they would seat together: the proposer and the fill through
``proposals``' ``MatcherPlayerFit``, and a post's window around its poster
(#546).

**Newness changes the window, never anything else** (``docs/adr/0113``). While
**either side** of a pairing is inside its newcomer window the tolerance is the
competitive one whatever the game — it binds the *pairing*, so the bad first
game cannot arrive through the veteran's side of it. No constant is introduced:
the tighter number is the one the competitive kind already carries.

Moved here from the search's gates and its context when the searches went
(#579); the two windows were the parts the new games call.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import Ruleset

#: How long a player is new for. **A date, never a flag** — the window is clocked
#: from the profile commit and computed where it is read, because a stored
#: ``is_newcomer`` boolean goes stale hourly and a date never does
#: (``the-newcomer-path.md`` §1).
#:
#: It lives here rather than in the ruleset because it is not a weight: it says
#: who counts as new, which is a fact about the product's shape.
NEWCOMER_WINDOW = timedelta(days=14)


def is_new_at(profile_created_at: datetime, now: datetime) -> bool:
    """Whether a profile committed then is still inside its newcomer window.

    **A date, never a flag**, and one reading of it, so a change to what *new*
    means cannot land on one side of a pairing and not the other.

    *Never longer than fourteen days* is a ceiling, and it is deliberately not a
    definition: a player fourteen days in who has played nothing still leaves
    the window. A window that extended while unused would be a permanent subsidy
    for the players the platform knows least about.
    """

    return now - profile_created_at < NEWCOMER_WINDOW


def level_close_enough(
    *,
    mu_a: float,
    mu_b: float,
    a_created_at: datetime,
    b_created_at: datetime,
    mode: SearchMode,
    ruleset: Ruleset,
    now: datetime,
) -> bool:
    """``|Δμ| < LEVEL_TOL`` for one pair, at :func:`level_tolerance`.

    **It takes two people**, which is what makes the rule survive into a four:
    every pair on a court is asked, and every pair containing a newcomer takes
    the competitive tolerance, whoever else is on it.
    """

    tolerance = level_tolerance(
        mode=mode, ruleset=ruleset, now=now, created_at=(a_created_at, b_created_at)
    )
    return abs(mu_a - mu_b) < tolerance


def level_tolerance(
    *,
    mode: SearchMode,
    ruleset: Ruleset,
    now: datetime,
    created_at: Iterable[datetime],
) -> float:
    """The level window's tolerance for a pairing of people made at
    ``created_at`` — the mode's, or the competitive one while **any** of them
    is new (``docs/adr/0113``). One answer for :func:`level_close_enough` and
    for a post's window around its poster (#546), which asks it of one."""

    tolerance = ruleset.modes[mode].level_tolerance
    if any(is_new_at(at, now) for at in created_at):
        tolerance = min(
            tolerance, ruleset.modes[SearchMode.COMPETITIVE].level_tolerance
        )
    return tolerance


__all__ = [
    "NEWCOMER_WINDOW",
    "is_new_at",
    "level_close_enough",
    "level_tolerance",
]

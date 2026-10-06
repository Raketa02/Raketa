"""What a ruleset is, and what makes one malformed.

**Every number the forecast and the level window use, in one versioned, dated,
frozen dataset.** A ruleset is *named* (``2026.09.15-a``), *dated*, and
**immutable once released**: a new set is a new name, never an edit to an old
one (``docs/adr/0093``). Changing a number is a ruleset release and a deploy —
not a code change and never an environment variable.

**It ships embedded with the code**, so a release is a deploy. Validated on
load: a malformed ruleset refuses to load and the process does not start, so the
deploy fails and the previous one keeps serving because the old pods are still
up (``docs/adr/0119`` §6). It never falls back to defaults.

**Two sections are left** (#580, PRD #569): the balance rules the forecast reads
and each kind of game's level tolerance. The ranking's weights, tags, floors,
liveness, interest, intent, distance, relaxation, telemetry, reliability,
modifier, group, shape and explanation sections went with the ranking — the new
games never read them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.engines.matchfit.core import SearchMode
from app.kernel import invariant


@dataclass(frozen=True)
class ModeRules:
    """One kind of game's level tolerance.

    **``level_tolerance`` is the level window** (``docs/adr/0103``): two people
    are close enough to play when ``|Δμ| < level_tolerance``. It is absolute on
    μ and never reads a band: the shipped bands are deliberately uneven because
    *evidence* is unevenly available down the scale, not because a tenth of a
    point means less at the top.
    """

    level_tolerance: float


@dataclass(frozen=True)
class BalanceRules:
    """The forecast: two coefficients, the clamp, and how a side is weighed.

    ``pct = clamp(100 − gap·mu_coefficient − σ·sigma_coefficient, min, max)``.

    ``σ`` is the core's ``combine_sigma``, never re-derived here: *the single
    place any engine is allowed to combine two standard deviations*.

    **The most directly falsifiable numbers in the engine.** The coefficients are
    a forecast, and a forecast is checkable against confirmed results.
    """

    mu_coefficient: float
    sigma_coefficient: float
    pct_min: int
    pct_max: int
    #: How much of a doubles side's strength the **stronger** partner sets —
    #: ``the-group-objective.md`` §3.1's ``TEAM_STRENGTH_SHARE``. One number and
    #: not two, because the pair's shares are one fact: two fields could be
    #: released summing to something other than a whole side.
    #:
    #: Under a half, which is the claim: *the weaker partner sets more of a
    #: side*, because a doubles pair is attacked at its weaker half all evening.
    #: It reads only in a four — a singles side has nobody to share with.
    stronger_partner_share: float


@dataclass(frozen=True)
class Ruleset:
    """A named, dated, frozen dataset of every number the engine uses.

    **Immutable once released.** A change is a new name and a new release, never
    an edit to this one.

    **The version stamp is never selected by the environment.** ``local``,
    ``development``, ``staging`` and ``production`` run the same numbers unless
    somebody deliberately releases a different named ruleset. A tolerance is not
    a setting — who may be put on a court together is behaviour a domain test can
    observe (``docs/adr/0028``).
    """

    version: str
    released_on: str
    modes: Mapping[SearchMode, ModeRules]
    balance: BalanceRules


def validate_ruleset(ruleset: Ruleset) -> Ruleset:
    """Refuse a ruleset that cannot be believed. Returns it when it can.

    Raises ``InvariantViolated``, which nothing catches — a malformed ruleset is
    a bug that shipped, and the only correct response is that the process does
    not start. **There is deliberately no fallback to defaults.**
    """

    _validate_stamp(ruleset)
    invariant(
        set(ruleset.modes) == set(SearchMode),
        f"a ruleset must set a tolerance for every kind of game: "
        f"{sorted(m.value for m in ruleset.modes)}",
    )
    for mode, rules in ruleset.modes.items():
        invariant(
            rules.level_tolerance > 0,
            f"{mode.value} level tolerance: {rules.level_tolerance}",
        )
    _validate_balance(ruleset.balance)
    return ruleset


def _validate_stamp(ruleset: Ruleset) -> None:
    """The name carries the date, and the date must agree with it.

    ``2026.09.15-a`` is a date and a letter, and the letter is what makes a
    second release on one day a different dataset rather than an edit to the
    first. Two spellings of one fact can disagree, so the pair is checked rather
    than trusted.
    """

    parts = ruleset.version.split("-")
    invariant(
        len(parts) == 2 and parts[1].isalpha() and parts[1].islower(),
        f"a ruleset version is a date and a lower-case letter: {ruleset.version!r}",
    )
    dotted = parts[0].split(".")
    invariant(
        len(dotted) == 3
        and len(dotted[0]) == 4
        and len(dotted[1]) == 2
        and len(dotted[2]) == 2
        and all(piece.isdigit() for piece in dotted),
        f"a ruleset version opens with YYYY.MM.DD: {ruleset.version!r}",
    )
    invariant(
        ruleset.released_on == "-".join(dotted),
        f"a ruleset's date disagrees with its name: "
        f"{ruleset.released_on!r} against {ruleset.version!r}",
    )


def _validate_balance(balance: BalanceRules) -> None:
    invariant(
        balance.pct_min < balance.pct_max,
        f"balance clamp: {balance.pct_min}–{balance.pct_max}",
    )
    invariant(
        balance.mu_coefficient > 0 and balance.sigma_coefficient > 0,
        f"balance coefficients: {balance.mu_coefficient}, {balance.sigma_coefficient}",
    )
    invariant(
        0.0 < balance.stronger_partner_share < 0.5,
        "the stronger partner sets less than half a side, or the claim the "
        f"share exists to make is not being made: {balance.stronger_partner_share}",
    )


__all__ = ["BalanceRules", "ModeRules", "Ruleset", "validate_ruleset"]

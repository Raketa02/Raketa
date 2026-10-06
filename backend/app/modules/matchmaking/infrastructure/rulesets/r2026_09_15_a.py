"""Ruleset ``2026.09.15-a`` — the balance rules and each kind of game's level
tolerance.

**What is left of a release that once held every number the ranking used.**
The "who fits whom" ranking went (#580, PRD #569) and took its sections with it
— the weights, the tag matrix, the floors, liveness, interest and the deck's
cool-off, intent, distance, relaxation, telemetry, reliability, the modifiers,
the group objective, the shape and the explanation bar. The two releases before
this one went too: nothing records which ruleset a result ran under any more,
and they carried these same numbers unchanged. **The numbers below did not move
in that cut**; the version stamp is the one they were released under.

**This file is frozen.** A number moves in a *new* dataset with a *new* name, and
the pull request carries one line per changed constant: the hypothesis, and what
would falsify it.

Owner: ``RobertConstantin02``.
"""

from __future__ import annotations

from types import MappingProxyType

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import BalanceRules, ModeRules, Ruleset

VERSION = "2026.09.15-a"

RULESET = Ruleset(
    version=VERSION,
    released_on="2026-09-15",
    modes=MappingProxyType(
        {
            # Two people are close enough for a competitive game inside 0.55 of
            # a point, and for a friendly inside 0.90 — the newcomer window
            # narrows a friendly to the competitive number while either side is
            # new (``docs/adr/0113``).
            SearchMode.COMPETITIVE: ModeRules(level_tolerance=0.55),
            SearchMode.FOR_FUN: ModeRules(level_tolerance=0.90),
        }
    ),
    # The forecast goes blind at Δμ ≈ 0.34 for a typical σ_pair of 0.495 — that
    # is where `pct` reaches its floor and stops discriminating, which is what
    # the level window exists to cover.
    balance=BalanceRules(
        mu_coefficient=145.0,
        sigma_coefficient=32.0,
        pct_min=35,
        pct_max=96,
        # A doubles side is attacked at its weaker half all evening, so the
        # weaker partner sets 0.55 of it against the stronger's 0.45. It reads
        # only in a four, and it is the whole reason the three ways of splitting
        # one four differ: at 0.50 every split of the same people would
        # forecast the same game.
        stronger_partner_share=0.45,
    ),
)

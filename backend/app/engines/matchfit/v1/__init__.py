"""Match Fit, version 1 — what the new games kept of it.

**This directory is the arithmetic and nothing else.** ``group`` is the forecast
between two sides and the hours a court shares. Every *shape* — the forecast,
the split, the ruleset — lives one directory up, because a shape outlives a
version (``docs/adr/0015``).

**The ranking that gave this directory its name is gone** (#580, PRD #569): the
eight terms, the renormalised Fit, the modifiers, the floor, Liveness, the
line-up enumeration and the group objective. None of them was called by the
Games deck, the fill, rescues, posting or the booked game.
"""

from app.engines.matchfit.v1.group import (
    forecast,
    forecast_and_split,
    forecast_pct,
    group_availability,
)

__all__ = [
    "forecast",
    "forecast_and_split",
    "forecast_pct",
    "group_availability",
]

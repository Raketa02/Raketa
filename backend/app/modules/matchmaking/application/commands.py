"""What a client may ask for. **Asks only, never a fact about the searcher.**

The backend reads the profile, the grid, the radius, the tags, the rating, the
intent and the gender preference itself, at request time, and *that* read is what
travels inward. A stale radius supplied by a phone is a gate evaluated on a lie,
so there is no field here for one to arrive through — **there is no per-search
radius input at all**, and widening happens only by taking a rung offer.

``trace_id`` is not a client fact either: it is the request's own
``X-Request-ID``, assigned by this application's middleware, and it is here
because *"it showed me somebody strange"* has to reach the exact log line a year
later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport


@final
@dataclass(frozen=True, slots=True)
class RunShortlistSearchCommand:
    """*Find me a game.* One tap, one search, and two taps are two searches."""

    searcher_id: UUID
    sport: Sport
    #: Which evening this one search is for. A ``SearchMode`` and never a
    #: ``PlayIntent``: the searcher's setting has two values and the candidate's
    #: declaration has three, and the distinct types are what make the collision
    #: a type error rather than a paragraph in a document.
    mode: SearchMode
    trace_id: str

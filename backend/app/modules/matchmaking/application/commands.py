"""What a client may ask for. **Asks only, never a fact about the searcher.**

The backend reads the profile, the grid, the radius, the tags, the rating, the
intent and the gender preference itself, at request time, and *that* read is what
travels inward. A stale radius supplied by a phone is a gate evaluated on a lie,
so there is no field here for one to arrive through — **there is no per-search
radius input at all**, and widening happens only by taking a rung offer.

**Taking a rung offer is a new search citing the one that offered it**, so two
of these fields arrive together and mean *this is that search*. The widening
itself is **not** sent: the radius a rung widens to is read off the offering
search's own record, because a radius a client could name would be the per-search
radius input this contract does not have.

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
from app.modules.matchmaking.domain.relaxation import Rung


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
    #: The grid to run **this one search** on, as the boundary spells a cell —
    #: ``(weekday, part)`` pairs, turned into a grid by the domain. ``None`` is
    #: *use the profile's own*, and it is emphatically not an empty grid.
    #:
    #: **The one ask that looks like a fact and is not.** A player editing the
    #: week on the search screen is asking about a different evening, not
    #: correcting the record — nothing here writes the profile, and the app
    #: offers to save it afterwards (``docs/adr/0099`` §3).
    availability_override: tuple[tuple[int, str], ...] | None
    #: The search whose offer this one accepts, and which rung of it. They travel
    #: together or not at all: a rung with nothing to cite would be a widening
    #: the engine never offered, and a citation with no rung would be a search
    #: claiming a lineage it does not use.
    offered_by_search_id: UUID | None
    rung: Rung | None
    trace_id: str


@final
@dataclass(frozen=True, slots=True)
class ExpressInterestCommand:
    """*Let's play.* One tap, costing nothing, that cites where it came from.

    **``search_id`` is required and non-nullable.** It is the origin key, and an
    interest citing a search that is unknown, that belongs to somebody else or
    that never showed this person is **refused, never linked as null**
    (``search-telemetry.md`` §4).

    **The position is not here**, and that is the same rule the rest of this file
    is written under: a client sends the ask and the backend reads the fact. The
    position is looked up on the cited search's own returned rows, so the origin
    key is true by construction rather than by a client being honest about where
    it was scrolled to.
    """

    from_player_id: UUID
    to_player_id: UUID
    sport: Sport
    search_id: UUID


@final
@dataclass(frozen=True, slots=True)
class ReadInterestCommand:
    """*What have I got out, and who said yes back?*

    One field, because there is exactly one person whose interest anybody may
    read: their own. **Outgoing and mutuals only** — incoming-and-not-mutual
    never crosses in any shape, and there is no field here that could ask for it
    (``docs/adr/0109``).
    """

    player_id: UUID

"""Where a search record goes, and the only shape anybody may read one back in.

**This is not a sixth outward demand.** ``ports.py`` holds what the matcher asks
of contexts it does not build; this is the matcher's *own* store, and the
distinction is the same one between a repository and a consumer-driven contract
everywhere else in this backend.

**Every method a route reaches through carries the authorization rule in its
signature.** ``search-telemetry.md`` §3: *the searcher may read their own
``RETURNED`` rows and nothing else.* Expressed as a filter inside an adapter,
that rule is one ``WHERE`` clause somebody can drop; expressed here, there is no
method that could return a near-miss row and no argument that could omit the
searcher. **Layer 3 is engine-internal and no route ever returns it, to anyone**
— a player may ask why somebody was shown; nobody may ask who was withheld.

**``modes_since`` is the one exception, and it is fenced by its return type
rather than by its arguments.** It answers about every searcher, because the
drift loop is about every searcher; what keeps that safe is that it can only
answer :class:`SearchModeReading` — four columns, no candidate rows, no near
misses, nothing a response could carry. A method that took a ``searcher_id`` it
did not need would be authorization theatre; a method that could return a record
would be the hole. It has no route and it never gets one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.matchmaking.domain.searches import SearchRecord


@final
@dataclass(frozen=True, slots=True)
class SearchModeReading:
    """One search, reduced to the four columns the drift loop reads.

    A type of its own rather than a whole :class:`SearchRecord`, because the loop
    walks a day of searches and a record carries every row each of them returned.
    It is also the fence: *what the drift detector may see* is four columns and a
    reader cannot widen it by accident.
    """

    searcher_id: UUID
    sport: Sport
    #: ``None`` on the deck, which has no mode and cannot disagree with a
    #: declaration in the way §6.3 means.
    mode: SearchMode | None
    at: datetime


@runtime_checkable
class SearchStore(Protocol):
    """The durable, unexpiring record of every engine invocation.

    **Nothing here deletes.** Erasure is the only path that ever removes a row
    (``docs/adr/0104`` §3) and it is a platform-wide obligation that does not
    exist yet, so there is no method for it to arrive through by accident — which
    is also what makes ``n_returned`` a redaction detector rather than a
    redundant column.
    """

    async def record(self, search: SearchRecord) -> None:
        """Write one search and all its candidate rows.

        **In the caller's own transaction, and committed before the response
        returns.** If this raises, the search fails: the ``search_id`` *is* the
        answer's identity, and an answer with no record is a permanently missing
        row of the denominator the engine is judged by.

        It takes the whole record rather than a search and then its rows, because
        two calls are two chances for the second to be skipped.
        """
        ...

    async def find(
        self, *, search_id: UUID, searcher_id: UUID
    ) -> SearchRecord | None:
        """This searcher's own search, with its ``RETURNED`` rows in position order.

        **The whole record and not the rows alone**, because the read-back
        renders an envelope as well as a list, and a second method for the search
        row would be a second chance to fetch one search's counters beside
        another's candidates.

        ``None`` for a search that is unknown *and* for one that belongs to
        somebody else — **the two are deliberately indistinguishable**, because
        an answer that separated them would tell a caller whether a stranger's
        ``search_id`` exists. A search that returned nobody is a record with no
        candidates, which is an answer and not an absence.

        The near-miss band is never loaded. It is not filtered out downstream and
        there is no argument here that could ask for it: *a player may ask why
        somebody was shown; nobody may ask who was withheld.*
        """
        ...

    async def widenings_taken(
        self, *, searcher_id: UUID, sport: Sport, radius_km: int
    ) -> int:
        """How often this searcher has already taken a widening to this radius.

        The input to *make a repeatedly-taken widening permanent*, and it counts
        **this radius** rather than any widening: a player who took 15 km twice
        and 20 km once has not asked for 20 km twice, and offering to save the
        wrong number is worse than not offering.

        It reads the search rows, which is the only place a taken rung is
        recorded — the profile is deliberately untouched by a widen, so there is
        nothing else that remembers one.
        """
        ...

    async def dealt_since(
        self, *, searcher_id: UUID, sport: Sport, since: datetime
    ) -> frozenset[UUID]:
        """Everybody this player has been **dealt** since a moment, in this sport.

        What makes **a spent deal deal again**: a new deal carries the same
        exclusions plus everybody already dealt, and without this a second tap
        would deal the same ten people — the order is deterministic and nothing
        about them has moved (``the-engine.md`` §10.3).

        **It reads the record and not a cache**, which is the same split the pass
        is written under: the deal is a durable row and the courtesy derived from
        it must not be able to outlive it or fall short of it. The window is the
        caller's — the store holds every deal ever dealt — and it is
        :data:`~app.modules.matchmaking.domain.deck.DEALT_MEMORY`.

        It answers ids and never rows. A deal needs a set to hold people out
        with, and a method that returned records would be a second way to read
        one — this time without the band predicate that keeps layer 3 inside the
        building.
        """
        ...

    async def modes_since(
        self, *, since: datetime, limit: int
    ) -> tuple["SearchModeReading", ...]:
        """Every search run since a moment, newest first, for the drift loop.

        **Not a route's read, and it never becomes one.** It answers about every
        searcher, which is why it takes no ``searcher_id`` and returns nothing a
        response could carry: four columns, no candidate rows, no near misses.
        The loop it feeds raises a prompt and changes no value.

        ``limit`` is a bound on one tick's work rather than a page: a loop that
        could read an unbounded day is a loop that falls over on the first busy
        one, and a prompt missed today is raised again tomorrow.
        """
        ...

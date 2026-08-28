"""Where a search record goes, and the only shape anybody may read one back in.

**This is not a sixth outward demand.** ``ports.py`` holds what the matcher asks
of contexts it does not build; this is the matcher's *own* store, and the
distinction is the same one between a repository and a consumer-driven contract
everywhere else in this backend.

**Two methods, and the second one's signature is the authorization rule.**
``search-telemetry.md`` §3: *the searcher may read their own ``RETURNED`` rows
and nothing else.* Expressed as a filter inside an adapter, that rule is one
``WHERE`` clause somebody can drop; expressed here, there is no method that could
return a near-miss row and no argument that could omit the searcher. **Layer 3 is
engine-internal and no route ever returns it, to anyone** — a player may ask why
somebody was shown; nobody may ask who was withheld.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from app.modules.matchmaking.domain.searches import SearchRecord


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

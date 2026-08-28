"""Which re-sorts the client may draw. **Server-driven, and never a lie.**

``the-play-screens.md`` §4: a control that would reorder nothing **is not
drawn**, because a visible control that does nothing is the product lying
quietly. And the list is decided here rather than by the client, because a client
deriving offerability from ``degraded_terms`` would be encoding a sort-to-term
mapping — which is the objection that promoted ``distance_km`` out of the
distance evidence in the first place.

**Re-sorting costs no round trip.** Every sort below reads a field the response
already carried, which is why the whole breakdown ships with the search: the
client sorts rows it holds, and the backend's only job is saying which controls
are honest.

**Offerability is computed, never asserted.** A sort is available exactly when
applying it produces an order different from the one returned — so a shortlist of
one row offers nothing, a shortlist already in Fit order does not offer *Best
fit*, and neither of those is a special case anybody has to remember.
"""

from __future__ import annotations

from typing import Callable, Iterable, Sequence

from app.engines.matchfit.core import Term
from app.modules.matchmaking.domain.searches import SortOption
from app.modules.matchmaking.domain.shortlist import Scored

#: What a row with nothing to sort on is worth. Larger than any real distance and
#: any real position, so a **stood-down** reading sorts **last** rather than as a
#: zero — which is the whole reason ``distance_km`` is omitted rather than sent
#: as ``0`` when the term stands down.
_LAST = float("inf")


def sorts_available(returned: Sequence[Scored]) -> tuple[SortOption, ...]:
    """The controls this answer can honestly draw, in the vocabulary's own order.

    ``EVENEST`` is absent from every shortlist and present in the vocabulary on
    purpose: it reads ``would_be_forecast``, which the engine precomputes only
    when a line-up has exactly one seat open. A singles shortlist has no seats,
    so there is nothing for it to reorder and the control is not drawn.

    ``MOST_RELIABLE`` is absent for as long as the reliability term stands down
    for everybody — which is a fact about the platform, re-derived per search
    rather than hardcoded, so the control appears by itself on the day
    ``player_score`` ships.
    """

    return tuple(
        option
        for option, key in (
            (SortOption.BEST_FIT, _by_fit),
            (SortOption.CLOSEST, _by_distance),
            (SortOption.MOST_RELIABLE, _by_reliability),
        )
        if _reorders(returned, key)
    )


def _reorders(
    returned: Sequence[Scored], key: Callable[[Scored], tuple[float, str]]
) -> bool:
    """Whether this sort would put the rows in a different order."""

    if len(returned) < 2:
        return False
    resorted = sorted(returned, key=key)
    return [row.player_id for row in resorted] != [row.player_id for row in returned]


def _by_fit(row: Scored) -> tuple[float, str]:
    """*Best fit* — the printed number, descending. Ties break on the player id,
    exactly as the returned order's do, so a tie is never what makes a sort look
    offerable."""

    return (-row.modified.points, row.player_id)


def _by_distance(row: Scored) -> tuple[float, str]:
    """*Closest* — whole kilometres ascending, a stood-down reading last."""

    return (_reading(row, Term.DISTANCE, row.generated.distance_km), row.player_id)


def _by_reliability(row: Scored) -> tuple[float, str]:
    """*Most reliable* — the published Player Score, descending.

    It reads the **published** figure and not the matcher's blend, because the
    control's promise is *these are the people your own screens call reliable*.
    A row whose reliability term stood down sorts last rather than at zero.
    """

    record = row.fenced.reliability
    published = _LAST if record is None else -float(record.published_score)
    return (published, row.player_id)


def _reading(row: Scored, term: Term, value: float) -> float:
    """``value`` when the term fired for this row, and *last* when it stood down."""

    return value if term not in _degraded(row) else _LAST


def _degraded(row: Scored) -> Iterable[Term]:
    return row.fit.degraded_terms

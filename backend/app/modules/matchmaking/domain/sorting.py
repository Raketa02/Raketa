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

**Offerability is computed, never asserted**, and it takes two things to be
offerable: the readings must **tell the rows apart**, and applying them must
produce a different order from the one returned. Both halves are load-bearing.

The first is the one that is easy to miss. Every sort ends on the player id, so a
sort whose readings are all equal — three candidates at one address, or a term
that stood down for everybody — resorts the list into **id order** and looks like
a reorder while carrying no information at all. That is exactly how *Most
reliable* is drawn wrongly, and the spec is explicit that it must not be: on a
search where nobody has a record the reliability term stands down for all twenty,
so the control **is not drawn**.

The second keeps the rest honest: a shortlist of one row offers nothing, and a
shortlist already in Fit order does not offer *Best fit*.

**It reads a reading and never a candidate.** :class:`Sortable` is the whole of
what a sort needs, and it exists so that the search that just ran and the search
read back an hour later reach one implementation rather than two — a second
answer to *which controls are honest* is exactly the drift this module was
written to prevent. It is also the reason ``distance_km`` is on the recorded row:
a sort whose reading the record does not hold cannot be offered on a read-back,
and the honest failure is a control **not drawn** rather than one that lies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence, final

from app.modules.matchmaking.domain.searches import (
    SearchCandidateRecord,
    SearchSurface,
    SortOption,
)
from app.modules.matchmaking.domain.shortlist import Scored

#: What a row with nothing to sort on is worth. Larger than any real distance and
#: any real position, so a **stood-down** reading sorts **last** rather than as a
#: zero — which is the whole reason ``distance_km`` is omitted rather than sent
#: as ``0`` when the term stands down.
_LAST = float("inf")


@final
@dataclass(frozen=True, slots=True)
class Sortable:
    """One returned row, as a sort sees it. **Three readings and an id.**

    Deliberately not a candidate. A sort has no business with a card, a
    breakdown or a band, and a type that carried them would be a type the next
    sort could reach into — which is how *Closest* would end up reading the
    distance evidence again.

    ``None`` is *this row has no reading for that sort*, and it sorts **last**.
    It is not a zero: a candidate whose distance term stood down is not next
    door.
    """

    player_id: str
    fit: float
    #: **Whole kilometres, as the wire carries them** — not the measurement.
    #: Offerability is a claim about what the *client* could do with the rows it
    #: holds, and the client holds an integer: two candidates 3.2 km and 3.4 km
    #: away are one distance to it, so a control promising to tell them apart
    #: would reorder nothing it could show. It is also what makes the read-back
    #: agree with the search, which records the same integer.
    distance_km: int | None
    #: The **published** Player Score, not the matcher's blend, because *Most
    #: reliable*'s promise is *these are the people your own screens call
    #: reliable*.
    reliability: float | None


def of_scored(row: Scored) -> Sortable:
    """What the search that just ran reads its own rows as.

    The distance is ``Scored``'s own — the whole kilometres the wire carries,
    absent when the term stood down — rather than the measurement, so a
    stood-down row sorts last here exactly as it does on the wire.
    """

    return Sortable(
        player_id=row.player_id,
        fit=row.modified.points,
        distance_km=row.shown_distance_km,
        reliability=(
            None
            if row.fenced.reliability is None
            else float(row.fenced.reliability.published_score)
        ),
    )


def of_record(row: SearchCandidateRecord) -> Sortable:
    """What a search read back reads its own rows as.

    Beside :func:`of_scored` rather than in the read-back, because the two are
    one decision — *what a sort is allowed to see* — and a mapping written in
    another layer is a second answer to it.

    ``reliability`` is **the score the card recorded**, and never one this route
    goes and asks for. That is the same rule the distance keeps one line up: a
    read-back reproduces the answer that was given, so a control it draws has to
    be orderable by a reading the row itself holds. A row written before the
    card carried one has ``None`` there and sorts last, which is the honest
    reading of a search nothing recorded a Player Score for — and a whole
    shortlist of them draws no control at all, because a reading that tells no
    two rows apart is not offerable.
    """

    return Sortable(
        player_id=str(row.player_id),
        fit=row.fit,
        distance_km=row.distance_km,
        reliability=(
            None
            if row.card is None or row.card.player_score is None
            else float(row.card.player_score)
        ),
    )


def sorts_available(
    returned: Sequence[Sortable], *, surface: SearchSurface
) -> tuple[SortOption, ...]:
    """The controls this answer can honestly draw, in the vocabulary's own order.

    ``EVENEST`` is absent from every shortlist and present in the vocabulary on
    purpose: it reads ``would_be_forecast``, which the engine precomputes only
    when a line-up has exactly one seat open. A singles shortlist has no seats,
    so there is nothing for it to reorder and the control is not drawn.

    ``MOST_RELIABLE`` is absent for as long as the reliability term stands down
    for everybody — which is a fact about **this search**, re-derived per search
    rather than hardcoded, so the control appears by itself on a search whose
    candidates have a record. ``player_score`` ships (``docs/adr/0140``); most
    people have no record yet, so on most searches it is still absent, and that
    is the derivation working rather than a gap.

    **Neither the deck nor a line-up draws any of them**, and that is the same
    rule rather than an exception to it. A line-up returns **seats** and not a
    list: the four are chosen together by one objective, and a control that
    reordered them would be offering to undo the choice the surface exists to
    make — *Even it out* is a selection among three arrangements, which is a
    different control and rides on the line-up itself.

    For the deck: a deck is one card at a time, so there is no list in the
    player's hand for a control to reorder, and its **order is its whole
    variety** — three bands plus ``PASS_SUPPRESS`` (``the-two-contracts.md`` §6).
    A control that resorted a deal would be offering to undo the one thing the
    surface does. The surface decides it here rather than at each caller, because
    the search that has just run and the same deal read back a month later must
    reach one answer.
    """

    if surface is not SearchSurface.SHORTLIST:
        return ()
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
    returned: Sequence[Sortable], key: Callable[[Sortable], tuple[float, str]]
) -> bool:
    """Whether this sort would tell the rows apart **and** put them in a
    different order."""

    if len(returned) < 2:
        return False
    if len({key(row)[0] for row in returned}) < 2:
        # Every row reads the same, so the only thing left to sort on is the
        # tie-break the returned order already used. Drawing that control would
        # offer the player a reshuffle by player id.
        return False
    resorted = sorted(returned, key=key)
    return [row.player_id for row in resorted] != [row.player_id for row in returned]


def _by_fit(row: Sortable) -> tuple[float, str]:
    """*Best fit* — the printed number, descending. Ties break on the player id,
    exactly as the returned order's do, so a tie is never what makes a sort look
    offerable."""

    return (-row.fit, row.player_id)


def _by_distance(row: Sortable) -> tuple[float, str]:
    """*Closest* — kilometres ascending, a stood-down reading last."""

    return (
        _LAST if row.distance_km is None else float(row.distance_km),
        row.player_id,
    )


def _by_reliability(row: Sortable) -> tuple[float, str]:
    """*Most reliable* — the published Player Score, descending.

    A row whose reliability term stood down sorts last rather than at zero.
    """

    return (_LAST if row.reliability is None else -row.reliability, row.player_id)

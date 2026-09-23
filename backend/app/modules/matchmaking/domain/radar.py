"""The reading — the radar's terminal stage, and the two facts only it serves.

Stages 1 to 6 are the shortlist's, unchanged (``shortlist.py``), and the ruler
is the deck's (``deck.py``): every pairing scores under the fun vector with the
intent term stood down, so one pair prints one Fit on both panes of Players.
What is here is stage 7 for a surface that **draws a map** rather than dealing
a hand (``docs/adr/0174`` §1, §3).

**Five gates asked, and no judgement after them.** Generation walks the box and
the exact circle on the viewer's own radius asking the five gates ``gates.py``
names for this surface — the four it does not ask are not relaxed, they are not
asked — and then *everyone* admitted is scored and *everyone* scored is drawn.
There is no quality floor here: the floor's verdict is still computed, because
``admits`` is where the evidence is priced and a Fit without it is a different
number, but nothing is withheld on it and the record's near-miss band is empty.
Karol with a court, Magda passed on, Marek matched, a Level the deck would never
deal — all drawn, each with a Fit the card prints as served.

**The order is the drawn distance and then the player id, and nothing else.**
No rank key, no bands, no Liveness in the order: a radar has no order to make a
promise findable with, and the position exists so that an Origin key means
something. The distance it sorts on is the one the row **prints** — one
decimal, spot to spot — rather than the unrounded measurement, so the order is
reproducible off the recorded row alone and two people who print the same
number sit by id. Stage 6 still runs, for every row — the reciprocal, the
signals, the inclusion reason — because the row crosses with its
``liveness_reasons`` and the sheet reads ``INTEREST_LIFT`` off it; it moves
nobody.

**Two facts are the radar's alone.** The **bearing** from the viewer's drawn
spot to the player's, beside the distance on the row and never inside the card
(ADR-0107's rule: its value depends on who is looking). And the **sport
chips** — every sport the player is rated in, with the Level held there — read
off the index's partitions in the sport registry's own order, because the
card's own Level comes off the same index row and two sources for one number
is how a card and its chips come to disagree.

**A reading is not a deal.** Nothing here reads the dealt memory, the pass
suppression, the cool-off or the outstanding yeses, and nothing it writes is
read by a deal: the memory is fed by ``DECK`` rows and by nothing else. The one
number the deck's rule *does* decide on the envelope — *N want to play you* —
is computed by the deck's own function over the deck's own gates, in the use
case, so that the chip on either pane is one number (``docs/adr/0174`` §5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, final
from uuid import UUID

from app.engines.matchfit.scoring import MatchFit
from app.kernel import Sport
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.fence import area_of, searcher_of
from app.modules.matchmaking.domain.geography import bearing_deg, drawn_spot
from app.modules.matchmaking.domain.search_context import SearchContext
from app.modules.matchmaking.domain.searches import RatedSportRecord, StagedCounts
from app.modules.matchmaking.domain.shortlist import (
    Scored,
    generate,
    score_all,
    viewer_spot_of,
    with_liveness,
)


@final
@dataclass(frozen=True, slots=True)
class DrawnRow:
    """One player on the radar: the pairing, and where they are from here."""

    scored: Scored
    #: North ``0``, clockwise, a whole degree — from the viewer's drawn spot to
    #: theirs, which is the same measurement ``drawn_distance_km`` is.
    bearing_deg: int


@final
@dataclass(frozen=True, slots=True)
class Reading:
    """One reading: every row the radar may draw, in the order it draws them."""

    rows: tuple[DrawnRow, ...]
    counts: StagedCounts

    @property
    def near_misses(self) -> tuple[Scored, ...]:
        """Always empty: nothing was withheld, so there is nothing to record
        under layer 3. A property rather than a field so that no caller can
        build a reading that claims otherwise."""

        return ()

    @property
    def best_withheld_fit(self) -> float | None:
        """Always ``None`` — *nothing was withheld*, which is not the same as
        ``0`` and is the only honest value on a surface with no floor."""

        return None


def read(context: SearchContext, engine: MatchFit) -> Reading:
    """The whole radar pipeline, from a bound snapshot to an ordered reading."""

    generation = generate(context)
    scored = score_all(generation, context, engine)
    searcher = searcher_of(context)
    moved = tuple(with_liveness(row, context, engine, searcher) for row in scored)
    ordered = tuple(sorted(moved, key=_from_here))
    viewer = viewer_spot_of(context)
    rows = tuple(
        DrawnRow(
            scored=row,
            bearing_deg=bearing_deg(
                viewer,
                drawn_spot(row.generated.player_uuid, area_of(row.generated.row)),
            ),
        )
        for row in ordered
    )
    return Reading(
        rows=rows,
        counts=StagedCounts(
            n_generated=generation.n_generated,
            excluded_by_gate=generation.excluded_by_gate,
            n_scored=len(scored),
            # The floor was computed and not applied, so *cleared* is everyone:
            # the bar this surface holds nobody to is one nobody fails.
            n_cleared_floor=len(scored),
            n_returned=len(rows),
            n_near_miss_recorded=0,
        ),
    )


def _from_here(row: Scored) -> tuple[bool, float, str]:
    """The sort key: the printed distance, then the id — **a total order**.

    A row whose distance term stood down prints no distance and sorts last, on
    the shortlist's own reading of that absence; the id closes the order so a
    set is never its source (``docs/adr/0105``).
    """

    printed = row.shown_distance_km
    return (printed is None, printed if printed is not None else 0.0, row.player_id)


def ratings_across(
    snapshots: Mapping[Sport, CandidateSnapshot], player_ids: tuple[UUID, ...]
) -> Mapping[UUID, tuple[RatedSportRecord, ...]]:
    """Every sport each of these players is rated in, with the Level held there.

    Read off the index's partitions — the same rows the card's own Level comes
    off — and walked in **the sport registry's own order**, never a mapping's,
    so the chips are drawn in the same order on every worker
    (``docs/adr/0105``). A player in no partition answers an empty tuple, which
    the ``NOT_RATED`` gate makes unreachable on a reading and the type does not
    forbid. Each partition is indexed once, so the walk is linear in the
    partitions' rows rather than in rows times players.
    """

    levels_by_sport: list[tuple[Sport, Mapping[str, float]]] = []
    for sport in Sport:
        snapshot = snapshots.get(sport)
        if snapshot is None:
            continue
        levels_by_sport.append(
            (
                sport,
                {row.player_id: row.mu for row in snapshot.rows if row.rating_status},
            )
        )
    chips: dict[UUID, tuple[RatedSportRecord, ...]] = {}
    for player_id in player_ids:
        key = str(player_id)
        chips[player_id] = tuple(
            RatedSportRecord(sport=sport, level=levels[key])
            for sport, levels in levels_by_sport
            if key in levels
        )
    return chips

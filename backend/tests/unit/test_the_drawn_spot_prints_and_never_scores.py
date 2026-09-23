"""The drawn spot reaches the print and nothing else (``docs/adr/0174`` §2).

One field on every candidate changed type — ``distance_km``, whole kilometres to
one decimal — and the claim that makes the change safe is that **the Fit does
not move**: the distance term and the radius gate keep measuring cell to cell,
and the spot inside the cell reaches no score, no gate and no evidence. Every
test here is one side of that fence.

The seams are ``Scored.shown_distance_km`` (the print), ``ScorableCandidate
.distance_km`` (the term's input) and ``gate_of``'s ``distance_km`` argument (the
gate's), driven through ``generate`` and ``score_all`` so the assertion is about
the stages as composed rather than about any one of them.
"""

from __future__ import annotations

from pathlib import Path

from dataclasses import replace

from app.engines.matchfit.core import DegradedReason, Term
from app.engines.matchfit.evidence import DistanceEvidence
from app.engines.matchfit.scoring import StoodDown
from app.engines.matchfit.v1 import MatchFitV1
from app.modules.matchmaking.domain.fence import area_of
from app.modules.matchmaking.domain.geography import (
    Point,
    distance_km,
    drawn_spot,
    shown_kilometres,
)
from app.modules.matchmaking.domain.shortlist import generate, score_all
from tests.unit import matchmaking_builders as build

ENGINE = MatchFitV1()

ROOT = Path(__file__).resolve().parents[2]


def _scored(rows):
    """Stages 2 to 5 — generation, the fence, the Fit — over everybody the box
    admits, uncapped, so a claim here is about every row and not the top twenty."""

    context = build.context(rows)
    return score_all(generate(context), context, ENGINE)


def _cell_distance(row) -> float:
    return distance_km(build.CENTRE, area_of(row))


def _spot_distance(row) -> float:
    viewer = drawn_spot(build.SEARCHER_ID, build.CENTRE)
    return distance_km(
        viewer, drawn_spot(row.generated.player_uuid, area_of(row.generated.row))
    )


def test_the_print_is_one_decimal_spot_to_spot_and_the_term_reads_the_cell():
    """Three people in three cells. What each card prints is measured between
    two drawn spots; what the term was handed is measured between two cells."""

    rows = (
        build.row(1, latitude=51.55),
        build.row(2, latitude=51.51),
        build.row(3, latitude=51.53, longitude=-0.10),
    )

    for row in _scored(rows):
        assert row.shown_distance_km == shown_kilometres(_spot_distance(row))
        assert row.shown_distance_km == round(row.shown_distance_km, 1)
        assert row.shown_distance_km >= 0.1
        assert row.fenced.distance_km == _cell_distance(row.generated.row)
        evidence = next(
            scored.evidence for scored in row.fit.terms if scored.term is Term.DISTANCE
        )
        assert isinstance(evidence, DistanceEvidence)
        assert evidence.km == int(round(_cell_distance(row.generated.row)))


def test_two_people_in_one_cell_print_two_distances_and_score_one_fit():
    """The spot tells them apart on the card and nowhere else: same cell, same
    facts, one Fit, one evidence line — two prints."""

    alike = tuple(build.row(n) for n in range(1, 21))

    scored = _scored(alike)
    fits = {row.modified.points for row in scored}
    evidence = {
        next(s.evidence for s in row.fit.terms if s.term is Term.DISTANCE)
        for row in scored
    }
    prints = {row.shown_distance_km for row in scored}

    assert len(scored) == 20
    assert len(fits) == 1, "the spot moved a Fit"
    assert len(evidence) == 1, "the spot reached the distance evidence"
    assert len(prints) > 1, "the print is not spot to spot"
    assert min(prints) >= 0.1


def test_somebody_at_the_very_edge_may_print_past_the_reach_and_is_still_dealt():
    """The named cost of keeping the two measurements different: the gate reads
    the cell, so a player 9,9 km away by cell is inside a 10 km reach whatever
    their card prints — and some of them print *10,x km*."""

    latitude, longitude = _the_nearest_cell_inside(10.0)
    rows = tuple(
        build.row(n, latitude=latitude, longitude=longitude) for n in range(1, 121)
    )

    scored = _scored(rows)
    over = [row for row in scored if row.shown_distance_km > 10.0]

    assert len(scored) == len(rows), "the gate read a spot"
    assert over, "nobody printed past the reach, so nothing here was asserted"
    assert all(row.fenced.distance_km < 10.0 for row in over)


def _the_nearest_cell_inside(radius_km: float) -> tuple[float, float]:
    """The coarse cell whose centre is furthest from the searcher's while still
    inside the ring — found on the platform's own grid, because the index
    refuses a latitude finer than it keeps."""

    cells = (
        (
            round(build.CENTRE.latitude + n / 100, 2),
            round(build.CENTRE.longitude + e / 100, 2),
        )
        for n in range(0, 12)
        for e in range(0, 18)
    )
    inside = [
        (distance_km(build.CENTRE, Point(latitude=lat, longitude=lon)), lat, lon)
        for lat, lon in cells
        if distance_km(build.CENTRE, Point(latitude=lat, longitude=lon)) < radius_km
    ]
    _, lat, lon = max(inside)
    return lat, lon


def test_a_stood_down_distance_is_still_omitted_and_never_the_floor():
    """The floor is for a measured *near*. A term that stood down measured
    nothing, and the print says so by absence — ``None``, which the wire omits
    — rather than by printing *0,1 km* about somebody it could not place.

    No live surface stands the distance term down today, so the row is
    re-fitted by hand with that one term in the basis; the property is the
    print's and not the engine's.
    """

    row = _scored((build.row(1, latitude=51.53),))[0]
    assert row.shown_distance_km is not None, "the fixture stood nothing down"

    stood_down = replace(
        row,
        fit=replace(
            row.fit,
            terms=tuple(s for s in row.fit.terms if s.term is not Term.DISTANCE),
            degraded_terms=(
                *row.fit.degraded_terms,
                StoodDown(term=Term.DISTANCE, reason=DegradedReason.NOTHING_FROM_THEM),
            ),
        ),
    )

    assert stood_down.shown_distance_km is None


def test_no_engine_gate_or_fence_names_the_spot():
    """The structural half. A term, a gate or the crossing that reached for
    ``drawn_spot`` would go green on every Fit test whose fixture happened to
    keep the spot near the centre."""

    fenced = [
        *sorted((ROOT / "app" / "engines").rglob("*.py")),
        ROOT / "app" / "modules" / "matchmaking" / "domain" / "gates.py",
        ROOT / "app" / "modules" / "matchmaking" / "domain" / "fence.py",
    ]

    reaching = [
        str(path.relative_to(ROOT))
        for path in fenced
        if "drawn_spot" in path.read_text()
    ]

    assert reaching == []

"""The walkthroughs, as **golden files** at the pure seam.

``the-engine.md`` §17.1: each is *a fixed population, a fixed clock, a fixed
ruleset and the complete expected response*, and **a diff is a design change that
must be argued for in the pull request** — which is precisely the point, because
it makes a weight change visible instead of quiet.

**The seam is the pure one.** ``run(context, engine)`` takes a bound snapshot and
returns an ordered answer with no I/O in between, so a walkthrough is reproducible
for ever: no clock, no database, no ledger, no network. The HTTP shape around it
is asserted in ``tests/api/test_searches.py``, where it belongs.

**What each walkthrough asserts, and what this build defers.** The three are
§17.1's, narrowed to the surface this ticket builds — the shortlist. Each claim
that needs a context nobody has written is named here rather than quietly
dropped:

**A — competitive singles.** A held account **absent**; a reliability-floor
breach printed and the candidate still **shown, low**; a candidate with an
asymmetric view of the pairing **docked** rather than gated; an opposed intent
reading **0.00**; and a candidate who said *Let's play* **lifted to the top with
the reason printed and their Fit unchanged by the lift**.

**B — the same city, for fun.** The weights **invert**; the opposed-intent
candidate takes **no further modifier**, and their `PLAYS_TO_WIN` tag moves the
**playing-style term and nothing else**. *Deferred:* the four, the group
objective and the forecast (#212, #213).

**C — a newcomer's first search.** The tightened level gate binds **both** sides
of the pairing, and the newcomer lift **prints**. *Deferred:* the provisional
forecast (#213).

To regenerate after a deliberate change: ``make gen-walkthroughs``. The diff it
produces is the argument.
"""

from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping

import pytest

from app.engines.matchfit.core import SearchMode, Term
from app.engines.matchfit.v1 import MatchFitV1
from app.modules.matchmaking.domain.ports import (
    PlayerScoreReading,
    RatioStrand,
    SportsmanshipStrand,
)
from app.modules.matchmaking.domain.search_context import NEWCOMER_WINDOW
from app.modules.matchmaking.domain.shortlist import Scored, Shortlist, run
from app.modules.player_profile.domain.weekly_hours import HOURS_OF_THE_DAY
from app.engines.matchfit.core import ReliabilityStrand
from app.kernel import Instant
from tests.unit import matchmaking_builders as build

GOLDEN = Path(__file__).resolve().parents[1] / "golden" / "matchmaking"

#: Where a stored figure is compared. Six places is far finer than any weight
#: this ruleset moves and far coarser than the last-bit noise two C libraries
#: disagree about, so a diff here is a decision and never a platform.
PLACES = 6

#: The name of the environment variable that rewrites the files. It is a
#: **variable and not a flag on pytest**, so that regenerating is a deliberate
#: command somebody typed rather than something a watch mode does by itself.
REWRITE = "UPDATE_GOLDEN"


# ---------------------------------------------------------------------------
# The city
# ---------------------------------------------------------------------------

#: A player under a hold. **Absent from every walkthrough**, and the assertion is
#: that no answer mentions them at all — not as a row, not as a count.
HELD = 1

#: A published Player Score under the bar, so the reliability floor docks them
#: `budget + 1` — outside the budget, allowed to dominate, and **a dock rather
#: than an exclusion**.
UNRELIABLE = 2

#: The pairing looks materially worse from their side than from yours: their own
#: ring is smaller than the distance between you, and their week is wide where
#: yours is four cells, so your grid covers little of theirs. That is a
#: **Liveness dock and never a gate** — somebody who set a small radius is not
#: refusing to be found, and the searcher is shown the fact rather than having
#: the person removed.
ASYMMETRIC = 3

#: A week wide enough that four shared cells are a small fraction of it. It is
#: the *reverse* reading that this moves: forward, the searcher's own grid is the
#: denominator and the overlap is total.
A_WIDE_WEEK = tuple(f"{day}:{hour}" for day in range(1, 8) for hour in HOURS_OF_THE_DAY)

#: Declared the opposite kind of evening. In competitive their intent reads
#: `0.00`; in for fun the same pairing reads the table's other cell — and in
#: neither does anything charge them a second time for it.
OPPOSED = 4

#: The ordinary good pairing the others are read against.
ORDINARY = 5

#: Said *Let's play* to the searcher two days ago, and is a **worse** pairing
#: than ``ORDINARY`` on the numbers. That gap is the whole point: the lift has to
#: be visible in the order and invisible in the Fit, and a candidate who was
#: already top would show neither.
SAID_LETS_PLAY = 6

#: How long ago the yes was sent. It crosses as evidence and is recorded as the
#: signal's raw input; it is **not** priced — ``docs/adr/0127`` made the ``+14``
#: flat, so a two-day-old yes and a twenty-day-old one lift by the same amount.
DAYS_AGO = 2


def _population():
    return (
        build.row(HELD),
        build.row(UNRELIABLE),
        build.row(ASYMMETRIC, radius_km=2, latitude=51.55, slots=A_WIDE_WEEK),
        build.row(OPPOSED, declared_intent="FOR_FUN", tags=("PLAYS_TO_WIN",)),
        build.row(ORDINARY),
        build.row(SAID_LETS_PLAY, mu=build.SEARCHER_MU + 0.12),
    )


def _player_scores() -> Mapping[Any, PlayerScoreReading]:
    """One published Player Score, under the bar.

    Its presence makes reliability a **live** term for this walkthrough, which is
    the point: the floor's dock cannot be exercised on a platform where the term
    stands down for everybody, and the evidence gate has to be seen counting a
    person-specific gap rather than a platform-wide one.
    """

    observed = Instant(build.NOW - timedelta(days=3))
    return {
        build.player(UNRELIABLE): PlayerScoreReading(
            strands={
                ReliabilityStrand.SHOWS_UP: RatioStrand(
                    value=40, numerator=4, denominator=10, observed_at=observed
                ),
                ReliabilityStrand.SPORTSMANSHIP: SportsmanshipStrand(
                    mean=2.0, rating_count=6, observed_at=observed
                ),
            },
            published_score=30,
        )
    }


#: The one live yes in the city. It is a fact about the **pair** and not about
#: the evening, so it is the same in A and in B — the two walkthroughs are one
#: city read under two weight vectors, and a yes that appeared in one of them
#: would make them two cities.
def _yeses():
    return {build.player(SAID_LETS_PLAY): DAYS_AGO}


def walkthrough_a():
    """Competitive singles, in a city with one held account in it."""

    return build.context(
        _population(),
        facts=build.searcher(mode=SearchMode.COMPETITIVE),
        held=frozenset({str(build.player(HELD))}),
        player_scores=_player_scores(),
        interest_days_ago=_yeses(),
        absent_terms=frozenset(),
    )


def walkthrough_b():
    """The same city, the same evening, **for fun** — and the list inverts."""

    return build.context(
        _population(),
        facts=build.searcher(mode=SearchMode.FOR_FUN),
        held=frozenset({str(build.player(HELD))}),
        player_scores=_player_scores(),
        interest_days_ago=_yeses(),
        absent_terms=frozenset(),
    )


def walkthrough_c():
    """A newcomer's first search: the gate tightens on **both** sides."""

    newly = build.NOW - NEWCOMER_WINDOW + timedelta(days=2)
    return build.context(
        (
            # Inside for-fun's own tolerance and outside the competitive one, so
            # the tightening is what decides them — and it decides them because
            # the *searcher* is new, not because they are.
            build.row(6, mu=build.SEARCHER_MU + 0.70),
            build.row(7, mu=build.SEARCHER_MU + 0.10),
            # New themselves, so the tightening binds from their side too, and
            # the lift prints for them.
            build.row(8, mu=build.SEARCHER_MU + 0.05, profile_created_at=newly),
        ),
        facts=build.searcher(mode=SearchMode.FOR_FUN, profile_created_at=newly),
    )


WALKTHROUGHS = {
    "a_competitive_singles": walkthrough_a,
    "b_the_same_city_for_fun": walkthrough_b,
    "c_a_newcomers_first_search": walkthrough_c,
}


# ---------------------------------------------------------------------------
# The complete expected answer
# ---------------------------------------------------------------------------


def _number(value: float | None) -> float | None:
    return None if value is None else round(value, PLACES)


def _evidence(value: object) -> dict[str, Any]:
    from app.modules.matchmaking.application.record_rows import evidence_payload

    payload = dict(evidence_payload(value))
    return {
        key: _number(item) if isinstance(item, float) else item
        for key, item in payload.items()
    }


def _row(row: Scored) -> dict[str, Any]:
    return {
        "player_id": row.player_id,
        "fit": _number(row.modified.points),
        "rank_key": _number(row.rank_key),
        "terms": [
            {
                "term": scored.term.value,
                "weight": _number(scored.weight),
                "value": _number(scored.value),
                "contribution": _number(scored.contribution),
                "evidence": _evidence(scored.evidence),
            }
            for scored in row.fit.terms
        ],
        "degraded_terms": [
            {"term": stood.term.value, "reason": stood.reason.value}
            for stood in row.fit.degraded_terms
        ],
        "concerns": [term.value for term in row.fit.concerns],
        "modifiers": [
            {"code": entry.modifier.value, "points": _number(entry.points)}
            for entry in row.modified.modifiers.fired
        ]
        + (
            []
            if row.modified.modifiers.floor_breach is None
            else [
                {
                    "code": row.modified.modifiers.floor_breach.modifier.value,
                    "points": _number(row.modified.modifiers.floor_breach.points),
                }
            ]
        ),
        "liveness_reasons": [
            {
                "signal": move.signal.value,
                "points": move.points,
                "load": move.load.value if move.load else None,
            }
            for move in (row.liveness.reasons if row.liveness else ())
        ],
        "inclusion_reason": (
            row.inclusion_reason.value if row.inclusion_reason else None
        ),
        "withheld_reason": (
            row.withheld_reason.value if row.withheld_reason else None
        ),
        "missing_terms": list(row.missing_terms),
    }


def answer(shortlist: Shortlist) -> dict[str, Any]:
    return {
        "returned": [_row(row) for row in shortlist.returned],
        "near_misses": [_row(row) for row in shortlist.near_misses],
        "counts": {
            "n_generated": shortlist.counts.n_generated,
            "excluded_by_gate": dict(shortlist.counts.excluded_by_gate),
            "n_scored": shortlist.counts.n_scored,
            "n_cleared_floor": shortlist.counts.n_cleared_floor,
            "n_returned": shortlist.counts.n_returned,
            "n_near_miss_recorded": shortlist.counts.n_near_miss_recorded,
        },
        "best_withheld_fit": _number(shortlist.best_withheld_fit),
        "players_in_range": shortlist.players_in_range,
    }


def produce(name: str) -> dict[str, Any]:
    return answer(run(WALKTHROUGHS[name](), MatchFitV1()))


# ---------------------------------------------------------------------------
# The golden files
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(WALKTHROUGHS))
def test_the_walkthrough_matches_its_golden_file(name: str):
    """**A diff here is a design change and must be argued for in the pull
    request.** That is what the file is for: it makes a weight change visible."""

    produced = produce(name)
    path = GOLDEN / f"{name}.json"

    if os.environ.get(REWRITE):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(produced, indent=2, sort_keys=True) + "\n")

    assert path.exists(), "missing golden file: run `make gen-walkthroughs`"
    assert produced == json.loads(path.read_text()), (
        f"walkthrough {name} moved. If that was deliberate, regenerate with "
        "`make gen-walkthroughs` and argue for the diff in the pull request."
    )


# ---------------------------------------------------------------------------
# What each walkthrough is *about*, asserted beside the file it is pinned in
# ---------------------------------------------------------------------------


def test_a_held_account_is_absent_and_no_answer_counts_them():
    """A hold fails **closed** and is told to nobody — so the row is gone and the
    only trace is one tick in a histogram no client ever sees."""

    produced = produce("a_competitive_singles")
    shown = {row["player_id"] for row in produced["returned"]}
    withheld = {row["player_id"] for row in produced["near_misses"]}

    assert str(build.player(HELD)) not in shown | withheld
    assert produced["counts"]["excluded_by_gate"]["HELD_ACCOUNT"] == 1


def test_a_reliability_floor_breach_prints_and_the_candidate_is_still_shown():
    """**A dock, not an exclusion.** The floor breach is outside the budget and
    is allowed to dominate — but it is a penalty, and a penalised player who
    still clears the quality floor is still somebody worth meeting."""

    produced = produce("a_competitive_singles")
    row = _find(produced["returned"], UNRELIABLE)

    assert row is not None, "the docked candidate was excluded rather than docked"
    codes = {entry["code"] for entry in row["modifiers"]}
    assert "RELIABILITY_FLOOR_BREACH" in codes
    dock = next(
        entry
        for entry in row["modifiers"]
        if entry["code"] == "RELIABILITY_FLOOR_BREACH"
    )
    assert dock["points"] < 0
    assert row["fit"] < max(other["fit"] for other in produced["returned"])


def test_a_candidates_own_small_ring_docks_them_and_never_gates_them():
    """Somebody who set a small radius is not refusing to be found: the searcher
    is shown the fact rather than having the person removed."""

    produced = produce("a_competitive_singles")
    row = _find(produced["returned"], ASYMMETRIC)

    assert row is not None, "an asymmetric pairing was removed rather than docked"
    assert produced["counts"]["excluded_by_gate"]["OUTSIDE_RADIUS"] == 0

    distance = next(
        term for term in row["terms"] if term["term"] == Term.DISTANCE.value
    )
    assert distance["evidence"]["outside_their_radius"] is True, (
        "the fact is printed, which is the whole of what the searcher is owed"
    )

    dock = next(
        reason
        for reason in row["liveness_reasons"]
        if reason["signal"] == "RECIPROCAL_ASYMMETRY"
    )
    assert dock["points"] < 0, "the shortfall is priced proportionately, not flat"


def test_an_opposed_intent_reads_the_tables_own_cell_and_is_charged_once():
    """The intent term prices it, and **nothing else does.** A second charge for
    an opposite intent would be a gate wearing a modifier's clothes, which is why
    that modifier is struck rather than deferred."""

    competitive = _find(produce("a_competitive_singles")["returned"], OPPOSED)
    if competitive is None:
        competitive = _find(produce("a_competitive_singles")["near_misses"], OPPOSED)

    assert competitive is not None
    intent = next(
        term
        for term in competitive["terms"]
        if term["term"] == Term.INTENT_ALIGNMENT.value
    )
    assert intent["value"] == 0.0
    assert {entry["code"] for entry in competitive["modifiers"]} <= {
        "CALIBRATION_VALUE"
    }


def test_a_tag_moves_the_playing_style_term_and_nothing_else():
    """§6.5's trap is that a tag leaks into intent. It is asserted explicitly
    because the two read the same declaration and are one lookup apart."""

    for_fun = produce("b_the_same_city_for_fun")
    row = _find(for_fun["returned"], OPPOSED) or _find(for_fun["near_misses"], OPPOSED)

    assert row is not None
    read = {term["term"] for term in row["terms"]}
    assert Term.PLAYING_STYLE.value in read
    intent = next(
        term for term in row["terms"] if term["term"] == Term.INTENT_ALIGNMENT.value
    )
    # The intent value is the table's own cell for this pairing, and the tag is
    # nowhere in it: a `PLAYS_TO_WIN` tag beside a `FOR_FUN` declaration must not
    # move the intent reading in either direction.
    assert intent["evidence"]["their_intent"] == "FOR_FUN"


def test_the_list_inverts_between_the_two_modes():
    """The weights invert, and **that inversion is what *for fun* means.**"""

    competitive = [
        row["player_id"] for row in produce("a_competitive_singles")["returned"]
    ]
    for_fun = [
        row["player_id"] for row in produce("b_the_same_city_for_fun")["returned"]
    ]

    assert competitive and for_fun
    assert competitive != for_fun


def test_the_tightened_gate_binds_both_sides_of_the_pairing():
    """**Newness changes the gate, never the weights.** Gating only the
    newcomer's own search would leave the bad first game arriving through the
    veteran's list, so the tolerance binds the pairing."""

    produced = produce("c_a_newcomers_first_search")
    shown = {row["player_id"] for row in produced["returned"]}

    assert str(build.player(6)) not in shown, (
        "a pairing outside the competitive tolerance was admitted to a for-fun "
        "search a newcomer ran"
    )
    assert produced["counts"]["excluded_by_gate"]["LEVEL"] == 1


def test_the_newcomer_lift_prints():
    """*They're new* is a sentence the product owes a searcher, so the signal is
    printable and the reason crosses as a code."""

    produced = produce("c_a_newcomers_first_search")
    row = _find(produced["returned"], 8)

    assert row is not None
    assert "NEWCOMER_LIFT" in {
        reason["signal"] for reason in row["liveness_reasons"]
    }


def _find(rows: list[dict[str, Any]], number: int) -> dict[str, Any] | None:
    wanted = str(build.player(number))
    return next((row for row in rows if row["player_id"] == wanted), None)


def test_a_lets_play_candidate_is_lifted_to_the_top_with_the_reason_printed():
    """*Lifted to the top, with the reason printed — and the Fit unchanged.*

    Three claims in one row, and they are three because separating them is what
    the whole design turns on. The **order** moves, by ``+14`` on ``rank_key``.
    The **number** does not, because Liveness never enters Fit — so *Why 78?*
    still adds up for somebody who is only near the top because a human said yes.
    And the **reason prints**, twice and differently: a liveness reason saying
    *they moved for this*, and an inclusion reason saying *this is why they are
    here at all*.
    """

    produced = produce("a_competitive_singles")
    lifted = _find(produced["returned"], SAID_LETS_PLAY)
    ordinary = _find(produced["returned"], ORDINARY)

    assert lifted is not None and ordinary is not None
    assert produced["returned"][0]["player_id"] == lifted["player_id"], (
        "the yes did not reach the top of the list"
    )
    assert lifted["fit"] < ordinary["fit"], (
        "the fixture stopped being the worse pairing, so the lift proves nothing"
    )
    assert lifted["rank_key"] > ordinary["rank_key"], (
        "the order did not move, which is the only thing the lift may move"
    )
    printed = next(
        reason
        for reason in lifted["liveness_reasons"]
        if reason["signal"] == "INTEREST_RECEIVED"
    )
    assert printed["points"] == 14, (
        "the lift is flat at +14 for the whole life of the yes — no taper"
    )
    assert lifted["inclusion_reason"] == "INTEREST_LIFT"

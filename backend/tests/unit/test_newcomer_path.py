"""The newcomer path — the window, the tightening, the lift, and the refusals.

Three claims of #175 have no home in any one stage's suite, because each is
about something the engine **does not** have. They are asserted here, together,
so that a reader looking for *where is the no-beginners switch refused* finds one
file rather than three absences.

**The window is a predicate over a date.** ``the-newcomer-path.md`` §1 struck
§14.5's hourly sweeper on the argument that a stored ``is_newcomer`` boolean goes
stale and a date does not, so the assertion worth making is that no such column
exists — the loop's absence is invisible, and the flag's presence is what would
bring it back.

**No setting declines a newcomer** (``docs/adr/0114``). This one is a fence and
not a behaviour: the switch would be a field on a profile, a body or a released
ruleset, and none of those three has a test that would notice a new one.

**The tightening binds a pair.** ``docs/adr/0116`` binds every gate across all
six pairs of a four, and three of those pairs contain no searcher — so the
tolerance is asserted here on a pair neither side of which ran the search, which
is the only shape a line-up can reuse. The line-up itself is #212's.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import timedelta
from pathlib import Path

import pytest

from app.engines.matchfit import ruleset as ruleset_module
from app.engines.matchfit.core import LivenessSignal, Modifier, SearchMode
from app.engines.matchfit.v1 import MatchFitV1, Refusal
from app.modules.matchmaking.domain.candidate_index import CandidateRow
from app.modules.matchmaking.domain.gates import GateCode, level_close_enough
from app.modules.matchmaking.domain.search_context import NEWCOMER_WINDOW
from app.modules.matchmaking.domain.searches import InclusionReason, WithheldReason
from app.modules.matchmaking.domain.shortlist import run
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.matchmaking.presentation.schemas import RunSearchRequest
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_profile.presentation.schemas import (
    CommitPlayerProfileRequest,
    ProposalsOptInRequest,
)
from tests.unit import matchmaking_builders as build
from tests.unit.matchfit_builders import capped_at

ENGINE = MatchFitV1()
BACKEND = Path(__file__).resolve().parents[2]

#: A profile committed two days ago — inside the window with twelve days to run.
NEWLY = build.NOW - NEWCOMER_WINDOW + timedelta(days=2)

#: The live ruleset with the one integer it refuses, supplied.
CAPPED_AT_ONE = capped_at(1)


# ---------------------------------------------------------------------------
# A date, never a flag
# ---------------------------------------------------------------------------


def test_the_window_is_a_date_and_the_index_holds_no_flag() -> None:
    """§14.5's newcomer-window loop is struck, and this is what keeps it struck.

    A stored *is this player new* would need a writer, and a writer on a fact
    that changes with the clock is the hourly sweeper arriving back under a
    different name. What the row holds is the moment the profile was committed;
    *new* is computed where it is read.
    """

    columns = {field.name for field in fields(CandidateRow)}

    assert "profile_created_at" in columns
    assert not {name for name in columns if "newcomer" in name or "is_new" in name}
    assert NEWCOMER_WINDOW == timedelta(days=14)


# ---------------------------------------------------------------------------
# The tightening binds a pair, and the pair may contain no searcher
# ---------------------------------------------------------------------------


def _tolerance(mode: SearchMode) -> float:
    return LIVE_RULESET.modes[mode].level_tolerance


def test_the_tightening_binds_a_pair_neither_side_of_which_searched() -> None:
    """The three cross pairs of a four contain no searcher at all.

    A gate written against a ``SearchContext`` could only answer for the three
    pairs the searcher is in, which is the hole ADR-0113 closed reopened one
    enumeration later. So the argument is two people, and the newcomer here is
    neither of the two the shortlist would have compared.
    """

    apart = (_tolerance(SearchMode.COMPETITIVE) + _tolerance(SearchMode.FOR_FUN)) / 2
    pair = dict(
        mu_a=2.80,
        mu_b=2.80 + apart,
        mode=SearchMode.FOR_FUN,
        ruleset=LIVE_RULESET,
        now=build.NOW,
    )

    assert level_close_enough(
        a_created_at=build.SETTLED, b_created_at=build.SETTLED, **pair
    ), "the pair is inside the for-fun tolerance, so this asserts nothing"
    assert not level_close_enough(
        a_created_at=NEWLY, b_created_at=build.SETTLED, **pair
    )
    assert not level_close_enough(
        a_created_at=build.SETTLED, b_created_at=NEWLY, **pair
    )


def test_the_tightening_introduces_no_constant() -> None:
    """*A first game is judged on the stricter of the two bars the product
    already has.* Nothing is introduced, so nothing is owed a falsifier."""

    assert level_close_enough(
        mu_a=2.80,
        mu_b=2.80 + _tolerance(SearchMode.COMPETITIVE) - 0.01,
        a_created_at=NEWLY,
        b_created_at=build.SETTLED,
        mode=SearchMode.FOR_FUN,
        ruleset=LIVE_RULESET,
        now=build.NOW,
    )


# ---------------------------------------------------------------------------
# No setting declines a newcomer
# ---------------------------------------------------------------------------

#: What a *no beginners* switch would have to be spelled with. A blocklist over
#: names rather than a positive enumeration, because the claim is about a field
#: that does not exist and there is nothing positive to enumerate.
REFUSAL_STEMS = ("newcomer", "beginner", "novice", "experienc", "counted_games")

#: The one name on that list that is allowed, and why. It **bounds the ask** —
#: past it the engine stops preferring somebody, and nobody is withheld or told
#: (``docs/adr/0114``) — which is the opposite of a preference over people.
ALLOWED = {"newcomer_absorption_cap"}


def _ruleset_field_names() -> set[str]:
    """Every field of every released-ruleset shape, walked rather than listed.

    A hand-kept list is a list somebody adds a shape beside; the module is the
    roster, so a new ``…Rules`` dataclass is inside this fence the day it exists.
    """

    held = [getattr(ruleset_module, name) for name in dir(ruleset_module)]
    shapes = [one for one in held if isinstance(one, type) and is_dataclass(one)]
    return {field.name for shape in shapes for field in fields(shape)}


@pytest.mark.parametrize(
    "names",
    [
        pytest.param(
            {field.name for field in fields(PlayerProfile)}, id="the-profile"
        ),
        pytest.param(set(CommitPlayerProfileRequest.model_fields), id="the-commit"),
        pytest.param(set(ProposalsOptInRequest.model_fields), id="the-opt-in"),
        pytest.param(set(RunSearchRequest.model_fields), id="the-search-request"),
        pytest.param(_ruleset_field_names(), id="the-ruleset"),
    ],
)
def test_no_no_beginners_switch_exists(names: set[str]) -> None:
    """**There is no setting that declines newcomers.** Not a toggle, not a
    search-scoped narrowing, not a preference with a default.

    It cannot be mutual — a newcomer declining veterans is incoherent — so it
    could only ever be the one-directional preference over people
    ``docs/adr/0096`` refused by name, and it protects nobody: the cost of a
    newcomer is a worse evening, not a risk.
    """

    offending = {
        name
        for name in names - ALLOWED
        if any(stem in name.lower() for stem in REFUSAL_STEMS)
    }

    assert not offending


def test_a_newcomer_is_never_refused_in_a_vocabulary_a_player_can_see() -> None:
    """A gate excludes, a withheld reason states a refusal, and neither may say
    *because they are new*. The window's only power is the evidence exemption."""

    codes = (
        {code.value for code in GateCode}
        | {reason.value for reason in WithheldReason}
        | {refusal.value for refusal in Refusal}
    )

    assert not {
        code for code in codes if any(stem in code.lower() for stem in REFUSAL_STEMS)
    }


def test_the_absorption_cap_cannot_reach_a_gate() -> None:
    """It **lowers a lift rather than withholding them**, and that is structural.

    The tally is read by stage 4 and stage 6; stage 1 has no argument that could
    carry it and no code to count it under. Asserted over the source because the
    failure mode is somebody adding the read, not somebody adding a gate code.
    """

    gates = (
        BACKEND / "app" / "modules" / "matchmaking" / "domain" / "gates.py"
    ).read_text()

    assert "absorption" not in gates
    assert "newcomer_appearances" not in gates


# ---------------------------------------------------------------------------
# The lift reorders; it never admits
# ---------------------------------------------------------------------------


def _just_under_the_floor(number: int) -> CandidateRow:
    """A candidate a newcomer's search scores **just** below the bar.

    Half a band apart, eight kilometres away and holding none of the searcher's
    tags — the terms live for everybody are what put them there, rather than a
    modifier or a dock, either of which would make this a test about stage 4.
    Close enough underneath that the lift would carry them over if it were ever
    allowed to, which is the whole of what the test needs from the fixture.
    """

    return build.row(
        number,
        mu=build.SEARCHER_MU + 0.50,
        tags=(),
        latitude=51.58,
        profile_created_at=NEWLY,
    )


def test_the_lift_reorders_and_never_admits_below_the_floor() -> None:
    """Stage 6 runs **after** the floor, so ``+8`` cannot buy anybody a place.

    That ordering is the whole reason the lift is affordable at eight points
    while the exposure adjustment is held to six: a signal that could admit
    somebody would be a floor with a second value.
    """

    sunk = _just_under_the_floor(1)
    shortlist = run(
        build.context((sunk,), facts=build.searcher(profile_created_at=NEWLY)),
        ENGINE,
    )

    assert [row.player_id for row in shortlist.near_misses] == [sunk.player_id]
    assert shortlist.returned == ()

    withheld = shortlist.near_misses[0]
    assert withheld.withheld_reason is WithheldReason.BELOW_FLOOR
    assert withheld.liveness is None, (
        "stage 6 ran on a candidate the floor had already refused"
    )
    lift = LIVE_RULESET.liveness.signals[LivenessSignal.NEWCOMER_LIFT].points.maximum
    assert withheld.modified.points + lift >= LIVE_RULESET.floors.quality_floor, (
        "the lift could not have carried this pairing over the bar anyway, so "
        "the ordering of stage 5 and stage 6 is not what this asserts"
    )


def test_the_newcomer_window_is_recorded_and_never_crosses_as_an_inclusion() -> None:
    """A printable reorder, not an admission (``the-newcomer-path.md`` §5).

    The store keeps ``NEWCOMER_WINDOW`` because a replay has to be able to say
    why a row sat where it did; the wire carries the reason as a **liveness
    code**, which is the honest shape — the lift moved them and admitted nobody.
    """

    lifted = build.row(1, profile_created_at=NEWLY)
    shortlist = run(
        build.context((lifted,), facts=build.searcher(profile_created_at=NEWLY)),
        ENGINE,
    )

    row = shortlist.returned[0]
    assert row.inclusion_reason is InclusionReason.NEWCOMER_WINDOW
    assert row.liveness is not None
    assert LivenessSignal.NEWCOMER_LIFT in {
        move.signal for move in row.liveness.printable
    }


# ---------------------------------------------------------------------------
# The cap bounds the ask and removes nobody
# ---------------------------------------------------------------------------


def test_the_cap_drops_the_lift_and_leaves_the_player_in_the_pool() -> None:
    """**Never withheld from generation.** Withholding would make a thin pool
    thinner for the person who can least afford it, on a fact about the engine
    rather than about them (``docs/adr/0125``, ``docs/adr/0114``)."""

    absorbed = build.row(1, profile_created_at=NEWLY)
    beside = build.row(2, profile_created_at=build.SETTLED)
    newcomer = build.searcher(profile_created_at=NEWLY)

    shortlist = run(
        build.context(
            (absorbed, beside),
            facts=newcomer,
            newcomer_appearances={build.player(1): 1},
            ruleset=CAPPED_AT_ONE,
        ),
        ENGINE,
    )

    shown = {row.player_id: row for row in shortlist.returned}
    assert absorbed.player_id in shown
    lifted = shown[absorbed.player_id].liveness
    assert lifted is not None
    assert LivenessSignal.NEWCOMER_LIFT not in {
        move.signal for move in lifted.printable
    }


def test_a_search_that_is_not_a_newcomers_never_binds_the_cap() -> None:
    """The tally is not read at all, so the same row keeps its lift. The bound is
    on the ask, and this search is not one."""

    absorbed = build.row(1, profile_created_at=NEWLY)
    shortlist = run(
        build.context(
            (absorbed,),
            facts=build.searcher(profile_created_at=build.SETTLED),
            newcomer_appearances={build.player(1): 99},
            ruleset=CAPPED_AT_ONE,
        ),
        ENGINE,
    )

    lifted = shortlist.returned[0].liveness
    assert lifted is not None
    assert LivenessSignal.NEWCOMER_LIFT in {move.signal for move in lifted.printable}


def test_nobody_is_told_the_cap_bound() -> None:
    """*Nothing has happened to them.* Their list is unchanged, their inbox is
    unchanged, and the only thing that moved is how often the engine volunteers
    them — so there is no code for it in either printed vocabulary."""

    assert Modifier.WELCOMING_RECORD in set(Modifier)
    assert not {
        code.value
        for code in list(LivenessSignal) + list(Modifier)
        if "absorption" in code.value.lower() or "cap" in code.value.lower()
    }

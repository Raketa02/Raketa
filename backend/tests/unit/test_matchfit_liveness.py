"""Stage 6 — Liveness: the offset, the budget, and the number that never crosses.

``docs/adr/0123`` names what is a type and what is a test, and this file is the
second half. The type enforces the **separation** — a silent move carries no code
to print — and the **funnel**, since the offset is a derived property and there is
no constructor that takes an already-summed number. The arithmetic is three
property tests: the silent net inside its budget over every signal at every
bound; ``|offset| > MOVE_NOTICE ⟹ reasons ≠ ∅``; and Liveness moving no printed
Fit.

**The roster test lives with the ruleset**, in ``test_matchfit_ruleset.py``, and
that is deliberate: pinning the silent set at exactly two is a claim about the
dataset, and a third silent signal has to fail where it is added rather than
where it is read.
"""

from __future__ import annotations

from itertools import product

import pytest

from app.engines.matchfit.core import ChallengeLoad, LivenessSignal, SearchMode
from app.engines.matchfit.ranking import (
    Liveness,
    ModifiedFit,
    Printable,
    Reciprocal,
    Silent,
    rank_key,
)
from app.engines.matchfit.scoring import Fit, ScoredTerm
from app.engines.matchfit.v1 import (
    challenge_load,
    modify,
    read_signals,
    reciprocal_asymmetry,
    reverse_mode,
    score,
)
from app.engines.matchfit.v1.liveness import SignalReading
from app.kernel import InvariantViolated
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.weekly_hours import HOURS_OF_THE_DAY
from tests.unit.matchfit_builders import (
    candidate,
    capped_at,
    cells,
    liveness_facts,
    modifier_facts,
    searcher,
)

RULES = LIVE_RULESET.liveness
NOTICE = RULES.move_notice


def bound(signal: LivenessSignal) -> tuple[int, int]:
    points = RULES.signals[signal].points
    return points.minimum, points.maximum


def built(*moves: Printable | Silent) -> Liveness:
    """A ``Liveness`` assembled from moves directly, for the property tests.

    The offset is a property either way — there is no path around the clamp — so
    a property test may state the moves it wants rather than reverse-engineering
    facts that produce them.
    """

    return Liveness(
        printable=tuple(move for move in moves if isinstance(move, Printable)),
        silent=tuple(move for move in moves if isinstance(move, Silent)),
        rules=RULES,
    )


# ---------------------------------------------------------------------------
# The roster, and the two it does not have
# ---------------------------------------------------------------------------


def test_every_signal_is_read_and_the_offset_stays_inside_its_bounds() -> None:
    """Ten signals, all firing hard, and the offset still lands in ``[−25, +25]``."""

    everything = read_signals(
        liveness_facts(
            interest_days_ago=1,
            newcomer=True,
            previously_accepted=True,
            previously_declined=True,
            answer_rate=1.0,
            recent_activity=1.0,
            overlap_proximity=1.0,
            open_challenges=0,
            exposure=1.0,
        ),
        LIVE_RULESET,
    )
    assert RULES.offset_minimum <= everything.offset <= RULES.offset_maximum
    assert everything.offset == RULES.offset_maximum


@pytest.mark.parametrize("struck", ["RADIUS_ASYMMETRY", "DIVERSITY", "SPREAD"])
def test_radius_asymmetry_is_not_in_the_vocabulary(struck: str) -> None:
    """It is struck as a double charge: ``fit_ba`` already contains the
    candidate's own distance term against the candidate's own radius."""

    assert struck not in {signal.name for signal in LivenessSignal}


def test_a_signal_that_did_not_fire_is_absent_rather_than_zero() -> None:
    """A candidate nothing is known about carries no moves at all — which is a
    different statement from ten signals that all measured nothing."""

    nothing = read_signals(liveness_facts(), LIVE_RULESET)
    assert nothing.printable == () and nothing.silent == ()
    assert nothing.offset == 0 and nothing.reasons == () and nothing.dominant is None


# ---------------------------------------------------------------------------
# The funnel and the separation
# ---------------------------------------------------------------------------


def test_the_funnel_routes_by_the_rulesets_own_printable_flag() -> None:
    """The newcomer lift speaks; the exposure adjustment does not.

    #175 split one row into two signals with opposite printability arguments:
    *they're new — this game does most of its work for them* is a sentence the
    product wants said, and *nobody has been shown them all week* is a third
    party's unpopularity the searcher is owed no version of.
    """

    both = read_signals(liveness_facts(newcomer=True, exposure=1.0), LIVE_RULESET)
    assert [move.signal for move in both.printable] == [LivenessSignal.NEWCOMER_LIFT]
    assert both.silent == (Silent(points=bound(LivenessSignal.EXPOSURE_ADJUSTMENT)[1]),)


def test_a_silent_move_carries_points_and_no_code() -> None:
    """``docs/adr/0123``'s type verbatim, and the whole of the separation: a
    signal that never prints cannot be named, because there is no name on it."""

    assert not hasattr(Silent(points=-6), "signal")
    assert set(Silent.__dataclass_fields__) == {"points"}


def test_only_the_full_inbox_may_carry_a_coarse_code() -> None:
    """A second signal borrowing the field would be a second thing printed as a
    band nobody argued for."""

    with pytest.raises(InvariantViolated):
        Printable(
            signal=LivenessSignal.NEWCOMER_LIFT, points=8, load=ChallengeLoad.FULL
        )
    with pytest.raises(InvariantViolated):
        Printable(signal=LivenessSignal.CHALLENGE_LOAD, points=-4)


def test_dominant_narrows_to_the_largest_printable_contributor() -> None:
    """A silent signal can never be the reason anybody is given, so naming one
    would be the promise broken in the one place it is kept."""

    moves = built(
        Printable(signal=LivenessSignal.PREVIOUS_ACCEPT, points=6),
        Printable(signal=LivenessSignal.RECENT_ACTIVITY, points=-5),
        Silent(points=-6),
    )
    assert moves.dominant == Printable(signal=LivenessSignal.PREVIOUS_ACCEPT, points=6)
    assert [move.points for move in moves.reasons] == [6, -5]


def test_reasons_break_ties_on_a_declaration_and_never_on_a_set() -> None:
    """``docs/adr/0105``: two signals at the same magnitude come back in the same
    order on every process, whatever ``PYTHONHASHSEED`` is."""

    ranked = built(
        Printable(signal=LivenessSignal.OVERLAP_PROXIMITY, points=4),
        Printable(signal=LivenessSignal.RECENT_ACTIVITY, points=4),
    ).reasons
    assert [move.signal for move in ranked] == [
        LivenessSignal.RECENT_ACTIVITY,
        LivenessSignal.OVERLAP_PROXIMITY,
    ]


# ---------------------------------------------------------------------------
# The three property tests ADR-0123 asks for
# ---------------------------------------------------------------------------


SILENT_CORNERS = list(
    product(
        *(
            sorted({bound(signal)[0], 0, bound(signal)[1]})
            for signal in RULES.silent_signals()
        )
    )
)


@pytest.mark.parametrize(
    "corners", SILENT_CORNERS, ids=[",".join(map(str, c)) for c in SILENT_CORNERS]
)
def test_the_applied_silent_net_never_leaves_its_budget(
    corners: tuple[int, ...],
) -> None:
    """Every silent signal at every bound, and the applied net still holds.

    The bound is on the **signed net**, because the only thing a searcher can
    observe is position and position is the net: a −6 decline beside a +6 exposure
    adjustment nets to zero and there is nothing to explain.
    """

    moves = built(*(Silent(points=points) for points in corners if points != 0))
    assert abs(moves.applied_silent) <= NOTICE
    assert moves.silent_net == sum(corners)


def test_the_clamp_only_ever_cuts_a_bury_today() -> None:
    """A property of the **roster**, not of the rule — which is what the roster
    test in ``test_matchfit_ruleset.py`` exists to make break loudly."""

    reachable = RULES.reachable_silent_net()
    assert reachable.maximum <= NOTICE
    assert reachable.minimum < -NOTICE
    buried = built(*(Silent(points=-6) for _ in range(2)))
    assert buried.budget_bound and buried.applied_silent == -NOTICE


PRINTABLE_CORNERS = list(
    product(
        *(
            sorted({bound(signal)[0], 0, bound(signal)[1]})
            for signal in (
                LivenessSignal.INTEREST_RECEIVED,
                LivenessSignal.CHALLENGE_LOAD,
                LivenessSignal.RECENT_ACTIVITY,
            )
        )
    )
)


@pytest.mark.parametrize(
    "printable",
    PRINTABLE_CORNERS,
    ids=[",".join(map(str, c)) for c in PRINTABLE_CORNERS],
)
@pytest.mark.parametrize("silent", [(-6, -6), (-6, 6), (0, 6), (0, 0)])
def test_anybody_moved_more_than_the_notice_has_a_reason_to_print(
    printable: tuple[int, ...], silent: tuple[int, ...]
) -> None:
    """``|offset| > MOVE_NOTICE ⟹ reasons ≠ ∅``.

    The promise stops being a rule to police and becomes arithmetic: with the
    silent net inside the budget, any player moved past the threshold necessarily
    has a printable contributor to name.
    """

    moves = built(
        *(
            Printable(
                signal=signal,
                points=points,
                load=(
                    ChallengeLoad.FULL
                    if signal is LivenessSignal.CHALLENGE_LOAD
                    else None
                ),
            )
            for signal, points in zip(
                (
                    LivenessSignal.INTEREST_RECEIVED,
                    LivenessSignal.CHALLENGE_LOAD,
                    LivenessSignal.RECENT_ACTIVITY,
                ),
                printable,
                strict=True,
            )
            if points != 0
        ),
        *(Silent(points=points) for points in silent if points != 0),
    )
    if abs(moves.offset) > NOTICE:
        assert moves.reasons != ()
        assert moves.dominant is not None


def test_a_candidate_can_still_be_buried_by_six_with_nothing_printed() -> None:
    """Deliberate, and the ``≤`` is the statement rather than a rounding
    convenience: six is the movement §9.5 already decided owes no explanation."""

    quiet = built(Silent(points=-6))
    assert quiet.offset == -NOTICE and quiet.reasons == ()


@pytest.mark.parametrize(
    "offset", list(range(RULES.offset_minimum, RULES.offset_maximum + 1))
)
def test_liveness_never_changes_the_printed_fit(offset: int) -> None:
    """Over every reachable offset: the printed number does not move, and the
    ordering does.

    ``Fit`` has no field an offset could be written to and no arithmetic on it,
    so there is nothing to add to — and ``rank_key`` produces a third quantity
    that is neither a ``Fit`` nor serialised.
    """

    modified = _modified()
    printed = modified.points
    moves = built(Printable(signal=LivenessSignal.ANSWER_RATE_AND_SPEED, points=offset))
    assert moves.offset == offset
    assert modified.points == printed == modified.fit.points
    assert rank_key(modified, moves) == pytest.approx(printed + offset)


def test_no_shape_on_the_scored_side_can_hold_a_liveness_number() -> None:
    """The type boundary §12.2 makes, asserted over the fields rather than read.

    A ``Fit`` that gained an ``offset`` — or a ``Liveness`` that gained a
    ``fit`` — is how the two would start meeting somewhere that is not
    :func:`rank_key`, and it is the edit a review would wave through.
    """

    scored = set(Fit.__dataclass_fields__) | set(ScoredTerm.__dataclass_fields__)
    assert not scored & {"offset", "rank_key", "liveness", "liveness_offset"}
    assert not set(Liveness.__dataclass_fields__) & {"fit", "points"}


def test_rank_key_is_the_only_place_the_two_meet_and_it_returns_a_bare_float() -> None:
    """A quantity with no shape has no field it could be written to."""

    modified = _modified()
    moves = built(Printable(signal=LivenessSignal.PREVIOUS_ACCEPT, points=6))
    key = rank_key(modified, moves)
    assert type(key) is float
    assert key == pytest.approx(modified.points + 6)


def _modified() -> ModifiedFit:
    """One scored candidate, through stage 4, with nothing firing.

    Day one, so the stack is empty and the modified number is the Fit — which is
    what makes the assertions above about Liveness and nothing else.
    """

    return ModifiedFit(
        fit=score(searcher(), candidate(), LIVE_RULESET),
        modifiers=modify(searcher(), candidate(), modifier_facts(), LIVE_RULESET),
    )


# ---------------------------------------------------------------------------
# The printable signals, one by one
# ---------------------------------------------------------------------------


def test_the_interest_lift_is_flat_and_then_absent() -> None:
    """It does not taper. The age of the yes already crosses as evidence, so a
    decay charges one fact twice — once visibly and once not — and prints the
    same sentence at day 2 and day 20 from two different positions."""

    day_two = read_signals(liveness_facts(interest_days_ago=2), LIVE_RULESET)
    day_twenty = read_signals(liveness_facts(interest_days_ago=20), LIVE_RULESET)
    assert day_two.offset == day_twenty.offset == 14
    assert read_signals(liveness_facts(), LIVE_RULESET).offset == 0


def test_the_newcomer_lift_reclaims_its_points_by_speaking() -> None:
    lifted = read_signals(liveness_facts(newcomer=True), LIVE_RULESET)
    assert lifted.offset == 8
    assert lifted.dominant is not None
    assert lifted.dominant.signal is LivenessSignal.NEWCOMER_LIFT


def test_the_absorption_cap_does_not_reach_this_stage() -> None:
    """The cap bounds an **experienced** player's welcoming record, one stage
    back. This lift fires only for a candidate who is themselves inside the
    window, so capping it would take the subsidy from the population the cap
    exists to keep from being leaned on (``docs/adr/0114``, amended).

    Asserted through a ruleset whose cap is supplied, because a ``None`` cap
    would make this pass against a stage that *did* read one.
    """

    facts = liveness_facts(newcomer=True)

    assert read_signals(facts, capped_at(1)).offset == 8
    assert read_signals(facts, LIVE_RULESET).offset == 8
    assert "newcomer_appearances" not in {
        field for field in facts.__slots__
    }, "stage 6 carries the cap's tally it has no business reading" 


@pytest.mark.parametrize(
    ("reading", "points"),
    [(0.0, -6), (0.5, 0), (1.0, 6)],
)
def test_a_ramp_is_priced_linearly_across_its_own_bound(
    reading: float, points: int
) -> None:
    """No curve is invented on this side of the fence. What the product may tune
    is the bound, which is ruleset data and carries a falsifier."""

    moves = read_signals(liveness_facts(answer_rate=reading), LIVE_RULESET)
    assert moves.offset == points


def test_a_ramp_that_prices_to_nothing_is_absent_from_the_reasons() -> None:
    """A signal that moved nobody is not a reason anybody is owed — and *we did
    not look* against *we looked and it was neutral* is separated in the recorded
    signal values, on the other side of the fence."""

    neutral = read_signals(liveness_facts(answer_rate=0.5), LIVE_RULESET)
    assert neutral.printable == () and neutral.offset == 0


# ---------------------------------------------------------------------------
# The full inbox
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("open_challenges", "points", "code"),
    [
        (0, None, None),
        (2, None, None),
        (3, -4, ChallengeLoad.SOME),
        (4, -4, ChallengeLoad.SOME),
        (5, -8, ChallengeLoad.BUSY),
        (7, -8, ChallengeLoad.BUSY),
        (8, -12, ChallengeLoad.FULL),
        (40, -12, ChallengeLoad.FULL),
    ],
)
def test_the_three_thresholds_are_adopted_whole(
    open_challenges: int, points: int | None, code: ChallengeLoad | None
) -> None:
    """§14.4's rungs at ``≥3 → −4``, ``≥5 → −8``, ``≥8 → −12``.

    ``docs/adr/0125`` deleted the third's withholding — an exclusion is a gate,
    and the gate roster is enumerated and closed — and changed nothing else about
    them.
    """

    outcome = challenge_load(open_challenges, RULES)
    if points is None:
        assert outcome is None
    else:
        assert outcome == SignalReading(
            signal=LivenessSignal.CHALLENGE_LOAD, points=points, prints=code
        )


def test_the_inbox_prints_a_coarse_code_and_never_the_number() -> None:
    """Their inbox depth is theirs. What a searcher is owed is *they have a lot
    on*, and forty and eight are the same sentence."""

    for count in (8, 40):
        printed = read_signals(
            liveness_facts(open_challenges=count), LIVE_RULESET
        ).dominant
        assert printed is not None
        assert printed.load is ChallengeLoad.FULL
        assert count not in (abs(printed.points), printed.points)


def test_a_full_inbox_never_sinks_a_candidate_past_their_own_lets_play() -> None:
    """``−12`` is anchored strictly below the ``+14`` lift, so a player who said
    *Let's play* to you still surfaces at ``+2`` however full their inbox is: a
    human's own ask outranks the engine's opinion of that human's popularity."""

    asked = read_signals(
        liveness_facts(interest_days_ago=1, open_challenges=40), LIVE_RULESET
    )
    assert asked.offset == 2


def test_the_deepest_rung_reaches_the_signals_own_bound() -> None:
    assert (
        RULES.challenge_load_rungs[-1].points == bound(LivenessSignal.CHALLENGE_LOAD)[0]
    )


# ---------------------------------------------------------------------------
# Reciprocal fit
# ---------------------------------------------------------------------------


def test_a_shortfall_inside_the_tolerance_costs_nothing() -> None:
    """The head start. The two directions never agree exactly — availability's
    denominator is the searcher's grid and distance runs against the searcher's
    ring — so ordinary asymmetry is not a dock."""

    inside = Reciprocal(fit_ab=80.0, fit_ba=70.0, mode=SearchMode.COMPETITIVE)
    assert reciprocal_asymmetry(inside, RULES) is None


def test_a_shortfall_past_the_tolerance_is_priced_proportionately() -> None:
    """``dock = −min(12, (fit_ab − fit_ba − 12) × 0.5)`` — not a flat charge,
    which is what the struck radius dock was."""

    past = Reciprocal(fit_ab=80.0, fit_ba=50.0, mode=SearchMode.COMPETITIVE)
    assert reciprocal_asymmetry(past, RULES) == SignalReading(
        signal=LivenessSignal.RECIPROCAL_ASYMMETRY, points=-9
    )


def test_the_dock_saturates_at_its_own_bound() -> None:
    buried = Reciprocal(fit_ab=95.0, fit_ba=5.0, mode=SearchMode.COMPETITIVE)
    assert reciprocal_asymmetry(buried, RULES) == SignalReading(
        signal=LivenessSignal.RECIPROCAL_ASYMMETRY,
        points=bound(LivenessSignal.RECIPROCAL_ASYMMETRY)[0],
    )


def test_reciprocal_fit_is_absent_off_the_shortlist() -> None:
    """It runs over the shortlist only, after the floor — so everywhere else the
    signal has nothing to read and does not fire."""

    assert reciprocal_asymmetry(None, RULES) is None
    assert read_signals(liveness_facts(), LIVE_RULESET, None).printable == ()


@pytest.mark.parametrize("mode", list(SearchMode))
def test_no_preference_never_selects_a_weight_vector_it_inherits_one(
    mode: SearchMode,
) -> None:
    """A candidate indifferent about the kind of evening is judging the game
    being proposed, so the reverse fit runs under the **searcher's** mode."""

    assert (
        reverse_mode(mode, PlayIntent.NO_PREFERENCE.value, LIVE_RULESET.intent) is mode
    )
    assert reverse_mode(mode, None, LIVE_RULESET.intent) is mode


@pytest.mark.parametrize(
    ("declared", "expected"),
    [
        (PlayIntent.COMPETITIVE.value, SearchMode.COMPETITIVE),
        (PlayIntent.FOR_FUN.value, SearchMode.FOR_FUN),
    ],
)
def test_a_declared_evening_selects_that_modes_vector(
    declared: str, expected: SearchMode
) -> None:
    """Read off ``same_evening`` rather than off two enums' spellings, which are
    deliberately different types and agree only by coincidence."""

    assert reverse_mode(SearchMode.FOR_FUN, declared, LIVE_RULESET.intent) is expected


#: A full week against a single evening. The only terms that read the pairing
#: asymmetrically are availability — whose denominator is *the searcher's* grid —
#: and distance, against *the searcher's* ring; everything else is symmetric. So
#: this is the whole of the asymmetry the reciprocal dock exists to price, and
#: for fun is the mode that prices it hardest (17.6 of 100 on availability).
WHOLE_WEEK = cells(*[(day, hour) for day in range(1, 8) for hour in HOURS_OF_THE_DAY])
ONE_EVENING = cells((3, 19))


def test_the_reverse_fit_the_module_assembles_produces_a_real_dock() -> None:
    """The three pieces composed the way the shortlist will compose them.

    ``fit_ba`` is ``score()`` with the two sides swapped — assembled by the
    module, because swapping them needs the searcher's own id, declaration,
    Player Score and area, none of which cross into a ``ScorableCandidate``. What
    this asserts is the half that *is* engine vocabulary: the reverse runs under
    the vector :func:`reverse_mode` picks, and the shortfall past the tolerance is
    priced by :func:`reciprocal_asymmetry`.

    The candidate is free all week — all 112 hours — and the searcher one hour of
    one evening, so the pairing reads 94.45 forwards and 61.42 back: a shortfall
    of 21.03 past the twelve-point head start, docked at half a point each —
    **−11, and not the −12 bound**, which is what makes this a test of the slope
    rather than of the saturation beside it.
    """

    lonely = searcher(mode=SearchMode.FOR_FUN, grid=ONE_EVENING, radius_km=10.0)
    busy = candidate(
        declared_intent=PlayIntent.NO_PREFERENCE.value, grid=WHOLE_WEEK, radius_km=10.0
    )
    forwards = score(lonely, busy, LIVE_RULESET)

    # The swap, as the module will do it. `NO_PREFERENCE` selects no vector, so
    # the reverse inherits the searcher's — the assertion below is that rule.
    inherited = reverse_mode(lonely.mode, busy.declared_intent, LIVE_RULESET.intent)
    assert inherited is lonely.mode
    backwards = score(
        searcher(mode=inherited, grid=busy.grid, radius_km=busy.radius_km),
        candidate(
            player_id="the-searcher", grid=lonely.grid, radius_km=lonely.radius_km
        ),
        LIVE_RULESET,
    )

    reciprocal = Reciprocal(
        fit_ab=forwards.points, fit_ba=backwards.points, mode=inherited
    )
    shortfall = forwards.points - backwards.points - RULES.asymmetry_tolerance
    assert shortfall == pytest.approx(21.03, abs=0.01)
    assert reciprocal_asymmetry(reciprocal, RULES) == SignalReading(
        signal=LivenessSignal.RECIPROCAL_ASYMMETRY, points=-11
    )
    assert -11 > bound(LivenessSignal.RECIPROCAL_ASYMMETRY)[0]


def test_the_reverse_direction_is_what_makes_the_shortfall() -> None:
    """The control the test above needs: a symmetric pairing docks nothing.

    Without it, *the dock fired* is consistent with a dock that fires on
    everything — and the signal exists to separate the candidate who would say no
    from the one who would say yes.
    """

    both_free = searcher(mode=SearchMode.FOR_FUN, grid=WHOLE_WEEK, radius_km=10.0)
    mirror = candidate(grid=WHOLE_WEEK, radius_km=10.0)
    forwards = score(both_free, mirror, LIVE_RULESET)
    backwards = score(
        searcher(mode=SearchMode.FOR_FUN, grid=mirror.grid, radius_km=mirror.radius_km),
        candidate(
            player_id="the-searcher",
            grid=both_free.grid,
            radius_km=both_free.radius_km,
        ),
        LIVE_RULESET,
    )
    assert forwards.points == pytest.approx(backwards.points)
    assert (
        reciprocal_asymmetry(
            Reciprocal(
                fit_ab=forwards.points,
                fit_ba=backwards.points,
                mode=SearchMode.FOR_FUN,
            ),
            RULES,
        )
        is None
    )

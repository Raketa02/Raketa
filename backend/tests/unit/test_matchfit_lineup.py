"""The enumeration: which four, how many were refused, and the honest partial.

``test_matchfit_group.py`` asserts *how good is this four*; this asserts *which
four*, which is the cubic half and the one the ``K × K`` mask exists for.

**The mask arrives as a callable and the gates that built it do not.** Every test
here supplies its own admissibility, because the engine's whole claim is that it
enforces whatever it is handed. The line-up search that built the mask from the
three gates went with the searches (#579).
"""

from __future__ import annotations

from itertools import combinations

import pytest

from app.engines.matchfit.core import GroupReason, SearchMode
from app.engines.matchfit.grouping import Arrangement, Seated
from app.engines.matchfit.v1 import GUESTS, arranged, best, seat
from app.engines.matchfit.v1.group import objective
from app.kernel import InvariantViolated
from app.modules.matchmaking.domain.balance import combine_group_sigma
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from tests.unit.matchfit_builders import searcher, seated

COMBINE = combine_group_sigma
FLOOR = LIVE_RULESET.floors.quality_floor


def _pool(*specs: tuple[str, float, float]) -> tuple[Seated, ...]:
    """A pool, in Fit order, each seat stating only its id, Level and Fit."""

    return tuple(
        seated(player_id=player_id, mu=mu, fit=fit) for player_id, mu, fit in specs
    )


def _seat(pool, *, admissible=None, **kwargs):
    """Seat a four. **The mask is required**, so a test names the one it means.

    The default here is the mask that refuses nothing, spelled out at the seam a
    test controls rather than as a default on ``seat`` itself: a fail-closed gate
    with a permissive default is one a caller can forget to pass.
    """

    return seat(
        searcher(),
        pool,
        LIVE_RULESET,
        COMBINE,
        _refuse() if admissible is None else admissible,
        **kwargs,
    )


def _refuse(*pairs: tuple[str, str]):
    """A mask refusing exactly these pairs, in either order."""

    refused = {frozenset(pair) for pair in pairs}

    def admits(one: str, other: str) -> bool:
        return frozenset((one, other)) not in refused

    return admits


# ---------------------------------------------------------------------------
# The winner, and what it beat
# ---------------------------------------------------------------------------


def test_the_winner_is_argmax_G_over_every_admissible_combination() -> None:
    """Brute-forced against the enumeration, because *which four* is the whole
    job and an argmax that agreed with itself would prove nothing."""

    pool = _pool(
        ("a", 2.80, 80.0),
        ("b", 2.82, 78.0),
        ("c", 2.78, 76.0),
        ("d", 3.05, 60.0),
        ("e", 2.60, 58.0),
    )
    viewer = searcher()

    seating = _seat(pool)

    every = [
        best(
            tuple(
                objective(viewer, one, LIVE_RULESET, COMBINE)
                for one in Arrangement.all_of(four)
            )
        )
        for four in combinations(pool, GUESTS)
    ]
    assert seating.winner is not None
    assert seating.winner.objective == pytest.approx(
        max(one.objective for one in every)
    )
    assert seating.counts.combinations == len(every)


def test_the_runner_up_is_the_second_combination_and_never_a_second_way_round(
) -> None:
    """The margin ``docs/adr/0117`` asks for is *why these four*, not *why this
    way round* — and the two have different answers whenever balance decides the
    arrangement."""

    pool = _pool(
        ("a", 2.80, 80.0), ("b", 2.82, 78.0), ("c", 2.78, 76.0), ("d", 2.79, 70.0)
    )

    seating = _seat(pool)

    assert seating.winner is not None and seating.runner_up is not None
    winners = {one.player_id for one in seating.winner.arrangement.seated}
    seconds = {one.player_id for one in seating.runner_up.arrangement.seated}
    assert winners != seconds
    assert isinstance(seating.reason, GroupReason)


def test_one_admissible_four_names_no_deciding_term() -> None:
    """**Nothing was beaten.** Naming the term with the largest margin over
    nobody would be the engine explaining an argument it never had."""

    seating = _seat(_pool(("a", 2.80, 80.0), ("b", 2.82, 78.0), ("c", 2.78, 76.0)))

    assert seating.reason is None
    assert seating.runner_up is None
    assert len(seating.arrangements) == 3


# ---------------------------------------------------------------------------
# The mask, and the floor
# ---------------------------------------------------------------------------


def test_a_refused_pair_takes_its_whole_family_of_combinations_with_it() -> None:
    """Every pairwise exclusion removes a **family** of fours, which is why the
    gate compounds and why the count of what it refused is worth recording."""

    pool = _pool(
        ("a", 2.80, 80.0), ("b", 2.82, 78.0), ("c", 2.78, 76.0), ("d", 2.79, 70.0)
    )

    seating = _seat(pool, admissible=_refuse(("a", "b")))

    assert seating.counts.refused_by_gate == 2, "C(4,3) = 4, and two contain a·b"
    seated = {one.player_id for one in seating.seated}
    assert not {"a", "b"} <= seated


def test_a_seat_is_never_filled_below_the_floor_to_complete_a_four() -> None:
    """``docs/adr/0099``, and the count says so rather than the absence.

    An interest lift is the one thing that may put somebody below the floor on a
    shortlist; it is a reason to **show** them, never a reason to seat them
    beside three others who did not ask.
    """

    pool = _pool(
        ("a", 2.80, 80.0),
        ("b", 2.82, 78.0),
        ("lifted", 2.80, float(FLOOR - 10)),
    )

    seating = _seat(pool)

    assert seating.counts.refused_by_floor == 1
    assert {one.player_id for one in seating.seated} == {"a", "b"}


def test_a_locked_seat_is_exempt_from_the_floor_because_it_was_not_filled() -> None:
    """The rule is that a seat is never **filled** below the floor, and
    hand-seating is not filling: the searcher put that person there."""

    pool = _pool(("a", 2.80, 80.0), ("b", 2.82, 78.0))
    low = seated(player_id="mine", mu=2.80, fit=float(FLOOR - 20), locked=True)

    seating = _seat(pool, locked=(low,))

    assert {one.player_id for one in seating.seated} == {"mine", "a", "b"}


def test_every_combination_contains_every_locked_seat() -> None:
    """**⚡ after hand-seating somebody is the same shape as ⚡ on an empty
    court**, and this is the whole of what makes that true."""

    pool = _pool(
        ("a", 2.80, 80.0), ("b", 2.82, 78.0), ("c", 2.78, 76.0), ("d", 2.79, 70.0)
    )
    mine = seated(player_id="mine", mu=2.81, fit=50.0, locked=True)

    seating = _seat(pool, locked=(mine,))

    assert "mine" in {one.player_id for one in seating.seated}
    assert seating.counts.combinations == 6, "C(4,2), because one seat is taken"


# ---------------------------------------------------------------------------
# The honest partial
# ---------------------------------------------------------------------------


def test_three_of_four_is_arranged_and_forecast_rather_than_refused() -> None:
    """A four can be impossible where candidates are plentiful, and the answer is
    a partial line-up with a **provisional** forecast on it.

    Three arrangements again, because the open seat is itself one of the three
    positions: beside the searcher, or across the net.
    """

    pool = _pool(("a", 2.80, 80.0), ("b", 2.82, 78.0), ("c", 2.78, 76.0))

    seating = _seat(pool, admissible=_refuse(("a", "b"), ("a", "c"), ("b", "c")))

    assert len(seating.seated) == 1
    assert len(seating.arrangements) == 1
    assert seating.arrangements[0].forecast.provisional is True
    assert seating.winner is None, "an incomplete four has no objective"
    assert seating.reason is None


def test_a_line_up_with_one_open_seat_still_offers_three_ways_round() -> None:
    """The open seat can be the searcher's partner or either opponent, so *three
    of four* is the same shape as four and not a narrower one."""

    pool = _pool(("a", 2.80, 80.0), ("b", 2.82, 78.0), ("c", 2.78, 76.0))

    seating = _seat(pool, admissible=_refuse(("a", "c"), ("b", "c")))

    assert len(seating.seated) == 2
    assert len(seating.arrangements) == 3
    assert {one.arrangement.partner_id for one in seating.arrangements} == {
        "a",
        "b",
        "",
    }
    assert all(one.forecast.provisional for one in seating.arrangements)


def test_while_a_seat_is_open_there_is_no_best_arrangement_at_all() -> None:
    """There is no objective to read — no cross pairs, no seat delta, no mean
    over three Fits — so there is nothing to be best **by**.

    Naming the min-gap arrangement *best* would give one word a second meaning on
    exactly the responses where the builder needs the first. *Even it out* still
    selects, and it is then the only selection there is.
    """

    pool = _pool(("a", 2.60, 80.0), ("b", 3.00, 78.0), ("c", 2.78, 76.0))

    seating = _seat(pool, admissible=_refuse(("a", "c"), ("b", "c")))

    assert seating.best is None
    assert seating.evenest is not None


def test_a_line_up_of_nobody_is_a_shape_and_never_an_error() -> None:
    """***Nobody* is not a different shape from *three of four*.**"""

    seating = _seat(())

    assert seating.seated == ()
    assert seating.arrangements == ()
    assert seating.best is None and seating.evenest is None


# ---------------------------------------------------------------------------
# The provisional figure, and the final one
# ---------------------------------------------------------------------------


def test_the_provisional_figure_is_exactly_the_figure_the_arrival_produces(
) -> None:
    """§9.9's equality, as a property of **one** implementation.

    A half-empty side is read as if the missing player matched the one already
    there, so seating that player's twin fills the seat without the number
    moving, and the caveat lifts on its own.
    """

    viewer = searcher()
    partner = seated(player_id="a", mu=2.80)
    lone = seated(player_id="b", mu=2.95)
    twin = seated(player_id="c", mu=2.95)

    half = arranged(
        viewer,
        Arrangement(partner=partner, opponents=(lone,)),
        LIVE_RULESET,
        COMBINE,
    )
    full = arranged(
        viewer,
        Arrangement(partner=partner, opponents=(lone, twin)),
        LIVE_RULESET,
        COMBINE,
    )

    assert half.forecast.provisional is True
    assert full.forecast.provisional is False
    assert half.forecast.pct == full.forecast.pct
    assert half.side_gap == pytest.approx(full.side_gap)


def test_a_singles_side_is_full_at_one_and_nothing_is_assumed() -> None:
    """Marking a singles forecast provisional would caveat a number nothing was
    assumed about — the one lie a caveat can tell."""

    only = arranged(
        searcher(),
        Arrangement(partner=None, opponents=(seated(player_id="a", mu=2.95),)),
        LIVE_RULESET,
        COMBINE,
        seats_per_side=1,
    )

    assert only.forecast.provisional is False
    assert only.forecast.assumption is None


# ---------------------------------------------------------------------------
# Determinism, and the arity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", list(SearchMode))
def test_the_same_pool_seats_the_same_four_every_time(mode) -> None:
    """A tie breaks on a fact and never on a set (``docs/adr/0105``), and the
    fact it breaks on is the partner's id ascending."""

    pool = _pool(
        ("a", 2.80, 70.0), ("b", 2.80, 70.0), ("c", 2.80, 70.0), ("d", 2.80, 70.0)
    )
    viewer = searcher(mode=mode)

    once = seat(viewer, pool, LIVE_RULESET, COMBINE, _refuse())
    twice = seat(viewer, tuple(reversed(pool)), LIVE_RULESET, COMBINE, _refuse())

    assert {one.player_id for one in once.seated} == {
        one.player_id for one in twice.seated
    }
    assert once.best is not None and twice.best is not None
    assert once.best.arrangement.partner_id == twice.best.arrangement.partner_id


def test_more_locked_seats_than_the_court_has_is_refused() -> None:
    """A four seats three people beside the searcher, and a request for a fourth
    is a shape rather than a preference."""

    with pytest.raises(InvariantViolated):
        _seat((), locked=tuple(seated(player_id=one) for one in "abcd"))


def test_hand_seating_is_not_a_way_past_the_six_pair_gate() -> None:
    """**A locked seat is held to the mask like every other.**

    The hole this closes is the partial line-up: with no admissible four the fill
    starts from the locked seats, and before this it never tested them against
    each other — so two people who may not share a court could be seated by
    having been named in the request.
    """

    locked = (
        seated(player_id="x", locked=True),
        seated(player_id="y", locked=True),
    )

    with pytest.raises(InvariantViolated):
        _seat(
            _pool(("a", 2.80, 80.0)),
            locked=locked,
            admissible=_refuse(("x", "y")),
        )

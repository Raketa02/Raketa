"""The line-up's own half: the pool, the ``K × K`` mask, and the six pairs.

**A four contains six pairs and the searcher is in three of them.** Every
assertion here is ultimately about the other three — the ones no shortlist ever
gated, because on a shortlist the searcher is one half of every pair on the
screen (``docs/adr/0116``).

The property test at the bottom is the one this whole file exists for: over every
combination the enumeration can reach, **no pair of the seated four fails a gate**
— and it is checked by re-evaluating the three gates from scratch rather than by
consulting the mask, so a mask that agreed with itself would still fail.
"""

from __future__ import annotations

from itertools import combinations

import pytest

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.v1 import MatchFitV1, seat
from app.modules.matchmaking.domain.fence import (
    combine_group_sigma,
    searcher_of,
)
from app.modules.matchmaking.domain.gates import (
    gender_satisfied_between,
    level_close_enough,
)
from app.modules.matchmaking.domain.lineups import (
    UnfilledReason,
    guests_for,
    mask_over,
    pool_for,
    seated_from,
    seats_per_side,
    unfilled_reason,
)
from app.kernel import Sport
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from tests.unit import matchmaking_builders as build

ENGINE = MatchFitV1()

#: Four levels a metre apart, so every pair clears the tolerance and the mask's
#: refusals are the ones a test actually asked for.
LEVELS = (2.80, 2.85, 2.75, 2.90)


def _city(**overrides):
    """Four candidates the searcher can see, and a context holding them."""

    rows = tuple(
        build.row(number, mu=mu)
        for number, mu in enumerate(LEVELS, start=1)
    )
    return rows, build.context(rows, **overrides)


def _seated(context, *, blocked_pairs=frozenset(), locked=()):
    """Run the pool, build the mask, seat. ``locked`` names ids from the pool."""

    pool = pool_for(context, ENGINE)
    hand_seated = tuple(
        row for row in pool.rows if row.player_id in {str(one) for one in locked}
    )
    return pool, seat(
        searcher_of(context),
        seated_from(pool.rows),
        context.ruleset,
        combine_group_sigma,
        mask_over(pool.rows, context, blocked_pairs),
        locked=seated_from(hand_seated, locked=True),
    )


# ---------------------------------------------------------------------------
# The pool
# ---------------------------------------------------------------------------


def test_the_pool_is_ordered_by_fit_and_never_by_the_rank_key():
    """Liveness reorders a list somebody reads; it does not decide eligibility.

    The number the card prints is the number a seat is chosen on, and the cap the
    enumeration truncates to is a ruleset row rather than a shortlist's twenty.
    """

    _, context = _city()

    pool = pool_for(context, ENGINE)

    fits = [row.modified.points for row in pool.rows]
    assert fits == sorted(fits, reverse=True)
    assert len(pool.rows) <= LIVE_RULESET.group.k
    assert pool.fit_rank[pool.rows[0].player_id] == 1


# ---------------------------------------------------------------------------
# The three gates, over the three pairs no Fit could see
# ---------------------------------------------------------------------------


def test_a_block_between_two_candidates_keeps_them_off_the_same_court():
    """``docs/adr/0095`` gives a block a **symmetric effect** and says it reaches
    every surface that shows one player to another.

    A line-up shows `a` to `b`, and before this the engine would have put them on
    a court together for ninety minutes because neither had blocked *the
    searcher*.
    """

    rows, context = _city()
    one, other = build.player(1), build.player(2)

    _, seating = _seated(
        context, blocked_pairs=frozenset({frozenset({one, other})})
    )

    seated = {member.player_id for member in seating.seated}
    assert not {str(one), str(other)} <= seated


def test_a_womens_only_candidate_is_not_seated_beside_a_man_by_a_third_party():
    """ADR-0096 chose **mutuality** so a one-directional filter would not leave a
    woman open to every man who searched ``ANY``.

    Under a searcher-only gate she is open to every man a third party seats
    beside her, which is the hole this closes.
    """

    rows = (
        build.row(1, gender="WOMAN", gender_preference="WOMEN_ONLY"),
        build.row(2, gender="MAN", gender_preference="ANY"),
        build.row(3, gender="WOMAN", gender_preference="ANY"),
        build.row(4, gender="WOMAN", gender_preference="ANY"),
    )
    context = build.context(rows)

    _, seating = _seated(context)

    seated = {member.player_id for member in seating.seated}
    assert not {str(build.player(1)), str(build.player(2))} <= seated


def test_a_newcomer_tightens_every_pair_they_are_in_whoever_searched():
    """``docs/adr/0113`` binds **the pairing and not the search**.

    Gating only the newcomer's own searches leaves the bad first game arriving
    through somebody else's list — and in a four, through a pair the searcher is
    not even in.
    """

    fun = build.searcher(mode=SearchMode.FOR_FUN)
    spread = LIVE_RULESET.modes[SearchMode.FOR_FUN].level_tolerance
    tight = LIVE_RULESET.modes[SearchMode.COMPETITIVE].level_tolerance
    assert tight < spread, "the two tolerances are the same; this proves nothing"
    rows = (
        build.row(1, mu=fun.mu),
        build.row(2, mu=fun.mu + (tight + spread) / 2, profile_created_at=build.NOW),
        build.row(3, mu=fun.mu),
        build.row(4, mu=fun.mu),
    )
    context = build.context(rows, facts=fun)

    _, seating = _seated(context)

    seated = {member.player_id for member in seating.seated}
    assert str(build.player(2)) not in seated


# ---------------------------------------------------------------------------
# What comes back when a four is impossible
# ---------------------------------------------------------------------------


def test_no_admissible_combination_is_told_apart_from_a_thin_pool():
    """The code ``docs/adr/0116`` added, and it is load-bearing.

    Without it the six-pair gate is indistinguishable from a thin pool, on the
    screen and in the telemetry — and after ADR-0113 it is also how a screen says
    *nobody at their level yet* about a newcomer's first four rather than
    *nobody*.

    Three candidates the searcher can see, spread so that the **outer two** are
    within tolerance of her and not of each other: every candidate passes every
    gate against the searcher, and the only triple there is fails.
    """

    tolerance = LIVE_RULESET.modes[SearchMode.COMPETITIVE].level_tolerance
    reach = tolerance * 0.6
    rows = (
        build.row(1, mu=build.SEARCHER_MU - reach),
        build.row(2, mu=build.SEARCHER_MU),
        build.row(3, mu=build.SEARCHER_MU + reach),
    )
    context = build.context(rows)

    pool, seating = _seated(context)

    assert len(pool.rows) == 3, "the searcher's own gates removed one of them"
    assert len(seating.seated) < guests_for(Sport.PADEL)
    assert (
        unfilled_reason(pool, seating, context, guests=guests_for(Sport.PADEL))
        is UnfilledReason.NO_ADMISSIBLE_COMBINATION
    )


def test_an_empty_city_reads_as_the_pool_and_never_as_a_gate():
    """*There was nobody* and *nobody could share a court* are different findings,
    and a screen that could not tell them apart would say the wrong thing about
    both."""

    context = build.context(())

    pool, seating = _seated(context)

    assert seating.seated == ()
    assert (
        unfilled_reason(pool, seating, context, guests=3)
        is UnfilledReason.POOL_EXHAUSTED
    )


# ---------------------------------------------------------------------------
# The sport decides the court, never a request
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sport,guests,per_side",
    [
        (Sport.PADEL, 3, 2),
        (Sport.BADMINTON, 3, 2),
        (Sport.TENNIS, 1, 1),
        (Sport.SQUASH, 1, 1),
    ],
)
def test_the_seat_count_is_the_sports_own_fact(sport, guests, per_side):
    """A singles side is **full at one**, and that is what keeps a singles
    forecast from being marked provisional about nothing."""

    assert guests_for(sport) == guests
    assert seats_per_side(sport) == per_side


# ---------------------------------------------------------------------------
# The property this whole file exists for
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", list(SearchMode))
def test_no_gated_player_appears_in_a_four_in_any_of_the_six_pairs(mode):
    """**Every gate binds all six pairs**, over every combination reachable.

    A city built so that every kind of refusal is present at once — a block
    between two candidates, a women-only preference facing a man, a level outside
    the tolerance and a newcomer tightening the pairs they are in — and then the
    seated four is checked against the three gates **re-evaluated from scratch**,
    never against the mask. A mask that agreed with itself would still fail this.

    It is exhaustive rather than sampled: the assertion is made over every
    combination the enumeration can reach, so *no gated player appears in a four*
    is a statement about the whole search space and not about the draws a
    generator happened to take.
    """

    rows = (
        build.row(1, mu=2.80, gender="WOMAN", gender_preference="WOMEN_ONLY"),
        build.row(2, mu=2.85, gender="MAN", gender_preference="ANY"),
        build.row(3, mu=2.75, gender="WOMAN", gender_preference="ANY"),
        build.row(4, mu=2.90, gender="WOMAN", gender_preference="ANY"),
        build.row(5, mu=2.82, gender="WOMAN", gender_preference="ANY"),
        build.row(
            6, mu=2.84, gender="WOMAN", gender_preference="ANY",
            profile_created_at=build.NOW,
        ),
        build.row(7, mu=3.30, gender="WOMAN", gender_preference="ANY"),
    )
    blocked = frozenset({frozenset({build.player(3), build.player(4)})})
    context = build.context(rows, facts=build.searcher(mode=mode))

    # **Locked, too.** Hand-seating is not a way past a gate, and the partial
    # line-up — which starts from the locked seats — is where it could have
    # become one.
    pool, seating = _seated(
        context,
        blocked_pairs=blocked,
        locked=(build.player(5),),
    )
    by_id = {row.player_id: row for row in pool.rows}

    for one, other in combinations(seating.seated, 2):
        mine, theirs = by_id[one.player_id].generated.row, by_id[
            other.player_id
        ].generated.row
        pair = frozenset({one.player_id, other.player_id})
        assert pair not in {
            frozenset(str(member) for member in edge) for edge in blocked
        }, f"{pair} share a court with a block between them"
        assert gender_satisfied_between(mine, theirs), (
            f"{pair} share a court and their preferences do not agree"
        )
        assert level_close_enough(
            mu_a=mine.mu,
            mu_b=theirs.mu,
            a_created_at=mine.profile_created_at,
            b_created_at=theirs.profile_created_at,
            mode=mode,
            ruleset=context.ruleset,
            now=context.now,
        ), f"{pair} share a court and their Levels are too far apart"

"""The Player Score's arithmetic — the part of this context that is a decision.

Everything else ``player_score`` does is somebody else's fact read through a
port. What is *this* context's own is here: what counts as an opportunity, how a
ratio becomes the figure a player is shown, and how the strands blend into the
one number on their profile.

**These are unit tests over a pure module and they are not a duplicate of
``tests/demands/test_player_score_demands.py``.** That suite proves the folds
against real streams; this one proves the arithmetic against cases the streams
cannot easily be made to produce — a half-way rounding, a blend of three, a
reading with a strand no provider has yet.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.engines.matchfit.core import ReliabilityStrand
from app.kernel import Instant, InvariantViolated, instant
from app.modules.player_score.domain.strands import (
    PUBLISHED_WEIGHTS,
    PlayerScore,
    StrandRatio,
    out_of_a_hundred,
)

_AT = instant(datetime(2026, 9, 1, tzinfo=timezone.utc))


def _ratio(good: int, opportunities: int, at: Instant = _AT) -> StrandRatio:
    return StrandRatio(good=good, opportunities=opportunities, last_at=at)


# ---------------------------------------------------------------------------
# One strand
# ---------------------------------------------------------------------------


def test_a_strand_with_no_opportunity_behind_it_is_refused() -> None:
    """A ``0/0`` is the shape of an invented zero, so it cannot be built.

    Absence is spelled by the player not being in the answer. A strand that could
    carry no denominator would give *we have nothing* a second spelling, which is
    how a measured nothing and an unasked question start being confused.
    """

    with pytest.raises(InvariantViolated):
        _ratio(0, 0)


def test_a_strand_cannot_claim_more_good_outcomes_than_opportunities() -> None:
    with pytest.raises(InvariantViolated):
        _ratio(3, 2)


def test_the_published_figure_rounds_a_half_up_and_never_to_even() -> None:
    """Twelve and a half per cent is thirteen, and Python's ``round`` says twelve.

    Banker's rounding is deterministic and surprising, and this figure is read by
    a person: two players either side of a half would be shown the same number
    one week and different numbers the next, for a reason nobody could see.
    """

    assert _ratio(1, 8).value == 13
    assert round(100 * 1 / 8) == 12


def test_a_strand_publishes_its_figure_and_keeps_its_counts() -> None:
    """One no-show out of one game is not thirty-five out of thirty-eight.

    Both readings are 'bad'; only one of them is evidence. The counts travel so
    the matcher can stand a thin strand down without re-deriving the figure.
    """

    thin, thick = _ratio(0, 1), _ratio(35, 38)

    assert (thin.value, thin.opportunities) == (0, 1)
    assert (thick.value, thick.opportunities) == (92, 38)


# ---------------------------------------------------------------------------
# The blend over them
# ---------------------------------------------------------------------------


def test_a_score_with_no_strand_in_it_is_refused() -> None:
    """An empty reading is not a reading — the same invariant the matcher makes.

    It is stated on both sides of the wire on purpose: an adapter that first
    noticed would be noticing in the place where the fix is hardest to argue.
    """

    with pytest.raises(InvariantViolated):
        PlayerScore(strands={})


def test_the_blend_renormalises_over_the_strands_that_are_there() -> None:
    """35 and 20 over a basis of 55, never over a hundred.

    This is what makes the three standing-down names cost the number nothing —
    and it is why two players with different strands are still comparable.
    """

    score = PlayerScore(
        strands={
            ReliabilityStrand.SHOWS_UP: _ratio(9, 10),
            ReliabilityStrand.ANSWERS_CHALLENGES: _ratio(1, 2),
        }
    )

    assert score.published == round((35 * 90 + 20 * 50) / 55)


def test_a_player_perfect_on_what_the_platform_can_see_is_published_at_a_hundred(
) -> None:
    """The proof the basis is the strands present rather than the whole vector.

    A blend over a hundred would cap somebody with two strands at 55, which reads
    as a bad record and is really *we cannot see the rest of you*.
    """

    score = PlayerScore(
        strands={
            ReliabilityStrand.SHOWS_UP: _ratio(4, 4),
            ReliabilityStrand.ANSWERS_CHALLENGES: _ratio(7, 7),
        }
    )

    assert score.published == 100


def test_one_strand_alone_publishes_that_strand_s_own_figure() -> None:
    """A basis of one weight cancels, whichever weight it is.

    Which is the honest answer while two of the five have a provider and most
    people have one of them: the number on the profile is what the platform has
    actually watched, and no weight can make a single observation say more.
    """

    for strand in (ReliabilityStrand.SHOWS_UP, ReliabilityStrand.ANSWERS_CHALLENGES):
        assert PlayerScore(strands={strand: _ratio(3, 4)}).published == 75


def test_the_horizon_reads_the_freshest_moment_across_the_strands() -> None:
    """One age over the whole score, because the strands share one cause."""

    older = instant(_AT - timedelta(days=30))
    score = PlayerScore(
        strands={
            ReliabilityStrand.SHOWS_UP: _ratio(1, 1, older),
            ReliabilityStrand.ANSWERS_CHALLENGES: _ratio(1, 1, _AT),
        }
    )

    assert score.last_at == _AT


# ---------------------------------------------------------------------------
# The vector itself
# ---------------------------------------------------------------------------


def test_every_strand_the_platform_has_a_word_for_carries_a_published_weight(
) -> None:
    """Exhaustive over the engine's closed vocabulary, and checked rather than
    assumed.

    A strand with no weight here would raise a ``KeyError`` inside the blend the
    day its provider landed — a runtime failure in a read, discovered by a player
    rather than by a build. Three of the five have no provider and every one of
    them is weighted, which is the point: the vector is written for the platform
    this will be, not the one it is.
    """

    assert set(PUBLISHED_WEIGHTS) == set(ReliabilityStrand)


def test_the_published_weights_are_not_the_matchers_weights() -> None:
    """Two vectors over one vocabulary, and confusing them is a live risk.

    The matcher weighs the strands **per mode** and the two mode vectors order
    people oppositely; this one is what a player reads about themselves on their
    own screen. If these ever became the same numbers it would be a coincidence,
    and a reader would be entitled to assume it was a rule.
    """

    from app.engines.matchfit.core import SearchMode
    from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET

    for mode in SearchMode:
        assert dict(LIVE_RULESET.modes[mode].strand_weights) != dict(PUBLISHED_WEIGHTS)


def test_the_struck_strand_has_no_weight_because_it_has_no_name() -> None:
    """*Confirms results* was withdrawn, not deferred (``docs/adr/0137``).

    A withdrawn demand leaves nothing behind — no enum member, no ruleset weight,
    no published weight — because a row nobody reads is a row nobody notices
    going wrong. Asserted by name so the sentence is checkable.
    """

    assert not hasattr(ReliabilityStrand, "CONFIRMS_RESULTS")
    assert "CONFIRMS_RESULTS" not in {strand.value for strand in PUBLISHED_WEIGHTS}


def test_a_blend_and_a_strand_round_through_the_same_function() -> None:
    """One rounding, so a card and a profile cannot print two figures for one
    record."""

    assert out_of_a_hundred(1, 8) == _ratio(1, 8).value

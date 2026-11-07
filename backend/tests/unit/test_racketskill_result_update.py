"""The result-update rule — the arithmetic the marketplace's honesty rests on.

**Hand-worked pairings, not a golden file.** Every number below was derived from
``docs/adr/0139``'s stated definition and checked by hand before the module
existed; a retune that moves one of them is a design change and has to be argued
for, exactly as a judged pairing is.

The properties are the opposite: nothing in ``test_the_shape_of_every_pairing``
should move when a constant is retuned. A retune that breaks one of those has
broken the model rather than the baseline — which is the same split
``test_racketskill_properties.py`` draws for the questionnaire.
"""

from __future__ import annotations

import math

import pytest

from app.engines.racketskill.core import (
    STATUS_CALIBRATING,
    STATUS_INITIAL_ESTIMATE,
    STATUS_STABLE,
    SkillEstimate,
    band_for,
    confidence_percent,
)
from app.engines.racketskill.update_v1 import (
    RESULT_MOVE_CEILING,
    SETTLED_SIGMA_FLOOR,
    SHARED_COURT_SHARE,
    STABLE_SIGMA,
    even_win,
    expected_score,
    information_share,
    one_side,
    rating_after,
    stakes,
)
from app.engines.racketskill.v3.engine import SIGMA_FLOOR
from app.kernel import InvariantViolated, Sport

#: A rating fresh out of onboarding: everybody leaves at the σ floor.
FRESH = SkillEstimate(mu=3.00, sigma=SIGMA_FLOOR)
#: Somebody the platform has watched for a season.
SETTLED = SkillEstimate(mu=3.00, sigma=0.15)


def a_rating(mu: float, sigma: float) -> SkillEstimate:
    return SkillEstimate(mu=mu, sigma=sigma)


# ---------------------------------------------------------------------------
# Expected score — how decisive a Level gap is
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "gap, favourite_percent",
    [
        (0.0, 50.0),
        (0.2, 56.7),
        (0.5, 66.3),
        (1.0, 79.5),
        (1.7, 90.9),
    ],
)
def test_a_level_gap_makes_the_stronger_player_this_much_of_a_favourite(
    gap, favourite_percent
):
    """One Level of daylight is four to one; one odds-decade is ten to one.

    Against an opponent the platform knows cold, so the attenuation is out of
    the way and this is the curve itself.
    """

    known = a_rating(3.00 - gap, 0.02)
    expected = expected_score(a_rating(3.00, 0.02), known)

    assert expected * 100 == pytest.approx(favourite_percent, abs=0.1)


def test_an_opponent_nobody_is_sure_of_flattens_the_expectation():
    """A gap against a stranger proves less, so it is expected less strongly."""

    gap = 1.0
    against_known = expected_score(FRESH, a_rating(3.00 - gap, 0.02))
    against_stranger = expected_score(FRESH, a_rating(3.00 - gap, SIGMA_FLOOR))

    assert 0.5 < against_stranger < against_known


# ---------------------------------------------------------------------------
# The pair of deltas — what the card prints, and what actually happens
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name, player, opposition, win, loss",
    [
        # A fresh player, an even game: the ceiling brakes both sides equally.
        ("fresh, even", FRESH, SETTLED, +0.1500, -0.1500),
        # A fresh player against somebody a Level above: the win is worth the
        # whole ceiling and the loss costs almost nothing, because losing to
        # them was the expected outcome.
        ("fresh, upset", FRESH, a_rating(4.00, 0.15), +0.1500, -0.0390),
        # The mirror of it. Beating somebody a Level below proves little.
        ("fresh, favourite", FRESH, a_rating(2.00, 0.15), +0.0390, -0.1500),
        # A season in: the brake is off and the rule speaks for itself.
        ("settled, even", a_rating(3.00, 0.2802), SETTLED, +0.0510, -0.0510),
        (
            "settled, upset",
            a_rating(3.00, 0.2802),
            a_rating(4.00, 0.15),
            +0.0819,
            -0.0213,
        ),
    ],
)
def test_what_a_counted_game_is_worth(name, player, opposition, win, loss):
    at_stake = stakes(player=player, opposition=opposition)

    assert at_stake.win == pytest.approx(win, abs=0.0001)
    assert at_stake.loss == pytest.approx(loss, abs=0.0001)


def test_a_four_is_worth_half_of_what_a_singles_game_is_worth():
    """You were half of what happened, so it is half the evidence about you.

    Asserted for a **fresh** player as well as a settled one, because that is
    where an absolute ceiling would have quietly undone it: both would have hit
    the same cap, and the share would have been true of everybody except the
    provisional padel players it was decided for.
    """

    for player in (FRESH, a_rating(3.00, 0.2802)):
        singles = stakes(player=player, opposition=SETTLED, share=1.0)
        doubles = stakes(player=player, opposition=SETTLED, share=SHARED_COURT_SHARE)

        assert doubles.win == pytest.approx(singles.win / 2, rel=0.15)
        assert doubles.loss == pytest.approx(singles.loss / 2, rel=0.15)


def test_the_share_comes_from_how_the_sport_is_played():
    assert information_share(Sport.TENNIS) == 1.0
    assert information_share(Sport.SQUASH) == 1.0
    assert information_share(Sport.PADEL) == SHARED_COURT_SHARE
    assert information_share(Sport.BADMINTON) == SHARED_COURT_SHARE


# ---------------------------------------------------------------------------
# An even game — how far the ranking's gap line says one win moves a Level
# (docs/adr/0203 §6)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sport", list(Sport))
def test_one_even_win_is_the_rules_own_move(sport):
    """The rule itself, asked of a game nobody is favourite in: every other
    player on court at this player's Level and uncertainty, each side folded
    the way a result folds it, the sport's share — and the Level the win
    leaves, on the scale's own resolution."""

    player = a_rating(2.71, 0.30)
    per_side = 2 if information_share(sport) == SHARED_COURT_SHARE else 1
    side = one_side([player] * per_side)
    moved = rating_after(
        player=player,
        own_side=side,
        opposition=side,
        won=True,
        results_so_far=1,
        share=information_share(sport),
    )

    assert even_win(player, sport=sport) == round(moved.mu - player.mu, 2)


@pytest.mark.parametrize(
    "sport, player, move",
    [
        # A season in, a four: the stake is 0,0149 — the pair is better known
        # than either partner (σ/√2) and half the evidence — and the Level it
        # leaves is a hundredth up.
        (Sport.PADEL, a_rating(2.71, 0.30), 0.01),
        # The same player in singles: 0,0572 on their own σ, six hundredths.
        (Sport.TENNIS, a_rating(2.71, 0.30), 0.06),
    ],
)
def test_what_one_even_win_moves_a_level(sport, player, move):
    assert even_win(player, sport=sport) == move


def test_an_even_win_too_small_to_show_moves_nothing():
    """A settled padel player's even win is under half a hundredth, and the
    Level is carried at two decimals: it never moves. No count of such wins
    closes a gap, which is what the gap line is told."""

    settled = a_rating(2.71, 0.15)

    assert 0 < stakes(
        player=one_side([settled, settled]),
        opposition=one_side([settled, settled]),
        share=SHARED_COURT_SHARE,
    ).win < 0.005
    assert even_win(settled, sport=Sport.PADEL) == 0.0


def test_no_single_evening_moves_a_level_further_than_the_ceiling():
    """A score nobody bothered to counter is worth this much and never more."""

    for opponent_mu in (1.0, 2.0, 3.0, 4.0, 5.0):
        at_stake = stakes(
            player=a_rating(3.00, SIGMA_FLOOR),
            opposition=a_rating(opponent_mu, 0.02),
        )
        assert abs(at_stake.win) <= RESULT_MOVE_CEILING + 1e-9
        assert abs(at_stake.loss) <= RESULT_MOVE_CEILING + 1e-9


def test_the_brake_holds_back_the_shape_and_never_flattens_it():
    """Both sides are scaled by one factor, so an upset stays an upset.

    Capping each delta on its own would make losing to somebody far above you
    cost exactly what losing to an equal costs, which is the opposite of what
    the pairing said.
    """

    braked = stakes(player=FRESH, opposition=a_rating(4.20, 0.15))

    assert braked.win == pytest.approx(RESULT_MOVE_CEILING, abs=1e-9)
    assert abs(braked.loss) < abs(braked.win) / 3


# ---------------------------------------------------------------------------
# The shape of every pairing — retune-proof
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("player_mu", [1.0, 1.8, 2.6, 3.4, 4.2, 5.0])
@pytest.mark.parametrize("player_sigma", [SIGMA_FLOOR, 0.40, 0.20, SETTLED_SIGMA_FLOOR])
@pytest.mark.parametrize("opponent_mu", [1.0, 2.6, 3.4, 5.0])
@pytest.mark.parametrize("opponent_sigma", [SIGMA_FLOOR, 0.20])
@pytest.mark.parametrize("share", [1.0, SHARED_COURT_SHARE])
def test_the_shape_of_every_pairing(
    player_mu, player_sigma, opponent_mu, opponent_sigma, share
):
    """A win always pays and a loss always costs, and neither is ever zero.

    This is ``AtStake``'s invariant proved over the whole scale rather than
    asserted at one pairing: *a zero would claim a counted game against this
    opponent moves the searcher's Level by nothing, which is false about every
    opponent.*
    """

    player = a_rating(player_mu, player_sigma)
    opposition = a_rating(opponent_mu, opponent_sigma)

    at_stake = stakes(player=player, opposition=opposition, share=share)

    assert at_stake.win > 0 > at_stake.loss
    # Rounded as the port publishes them, because a delta that survives the
    # arithmetic and dies in the rounding would break the contract on the wire
    # rather than in the domain.
    assert round(at_stake.win, 4) > 0 > round(at_stake.loss, 4)

    won = rating_after(
        player=player, opposition=opposition, share=share, won=True, results_so_far=4
    )
    lost = rating_after(
        player=player, opposition=opposition, share=share, won=False, results_so_far=4
    )

    # A confirmed result tightens σ whichever way it went: what we learned is
    # that these two played, and that does not depend on who won.
    assert won.sigma <= player.sigma
    assert lost.sigma == pytest.approx(won.sigma, abs=1e-12)
    # Strictly, when there was something to learn. A pairing that was a foregone
    # conclusion teaches nothing and tightens nothing — the same sentence as *a
    # result is informative exactly to the degree it was in doubt*, and the
    # reason this is a condition rather than an unconditional assertion.
    in_doubt = 0.05 < expected_score(player, opposition) < 0.95
    if player.sigma > SETTLED_SIGMA_FLOOR and in_doubt:
        assert won.sigma < player.sigma
    # And it never claims more certainty than the platform allows itself.
    assert won.sigma >= SETTLED_SIGMA_FLOOR
    assert won.confidence == confidence_percent(won.sigma)
    # The Level stays on the scale, and the band travels on the estimate rather
    # than being looked up beside it.
    assert 1.0 <= won.mu <= 5.0
    assert 1.0 <= lost.mu <= 5.0
    assert won.band.name == band_for(won.mu).label


def test_a_result_moves_the_level_the_way_the_card_said_it_would():
    """*At stake* is not a preview of the rule; it **is** the rule, read forward.

    A card promising ``+0,07`` and an update delivering something else would be
    the explainability failure the whole port exists to prevent.
    """

    player = a_rating(2.90, 0.42)
    opposition = a_rating(3.30, 0.22)

    at_stake = stakes(player=player, opposition=opposition)
    won = rating_after(
        player=player, opposition=opposition, won=True, results_so_far=6
    )
    lost = rating_after(
        player=player, opposition=opposition, won=False, results_so_far=6
    )

    assert won.mu == pytest.approx(round(player.mu + at_stake.win, 2), abs=1e-9)
    assert lost.mu == pytest.approx(round(player.mu + at_stake.loss, 2), abs=1e-9)


def test_a_level_never_leaves_the_scale():
    at_the_top = rating_after(
        player=a_rating(5.00, SIGMA_FLOOR),
        opposition=a_rating(1.00, 0.02),
        won=True,
        results_so_far=0,
    )
    at_the_bottom = rating_after(
        player=a_rating(1.00, SIGMA_FLOOR),
        opposition=a_rating(5.00, 0.02),
        won=False,
        results_so_far=0,
    )

    assert at_the_top.mu == 5.00
    assert at_the_bottom.mu == 1.00


# ---------------------------------------------------------------------------
# Status — what drives Initial Estimate → Calibrating → Stable
# ---------------------------------------------------------------------------


def test_the_first_counted_result_leaves_initial_estimate():
    first = rating_after(
        player=FRESH, opposition=SETTLED, won=True, results_so_far=0
    )

    assert first.status == STATUS_CALIBRATING


def test_a_rating_the_platform_is_sure_of_is_stable():
    """The bar is crossed by the σ the result leaves, not by the game count."""

    across = rating_after(
        player=a_rating(3.00, STABLE_SIGMA + 0.001),
        opposition=SETTLED,
        won=True,
        results_so_far=30,
    )
    short_of_it = rating_after(
        player=a_rating(3.00, STABLE_SIGMA + 0.05),
        opposition=SETTLED,
        won=True,
        results_so_far=30,
    )

    assert across.sigma <= STABLE_SIGMA
    assert across.status == STATUS_STABLE
    assert short_of_it.sigma > STABLE_SIGMA
    assert short_of_it.status == STATUS_CALIBRATING


def test_stable_is_the_bar_the_glossary_names_and_not_a_count():
    """Twenty games against people we know nothing about is not certainty."""

    still_unsure = rating_after(
        player=a_rating(3.00, 0.55),
        opposition=a_rating(3.00, SIGMA_FLOOR),
        won=True,
        results_so_far=40,
    )

    assert still_unsure.sigma > STABLE_SIGMA
    assert still_unsure.status == STATUS_CALIBRATING


def test_initial_estimate_is_what_a_rating_that_has_played_nothing_says():
    """The status is asked of the rule, so nothing else may author one."""

    from app.engines.racketskill.update_v1 import status_for

    assert status_for(sigma=SIGMA_FLOOR, results=0) == STATUS_INITIAL_ESTIMATE
    assert status_for(sigma=SIGMA_FLOOR, results=1) == STATUS_CALIBRATING
    assert status_for(sigma=STABLE_SIGMA, results=1) == STATUS_STABLE
    # A rating that has never played is an Initial Estimate whatever σ says:
    # onboarding cannot reach the Stable bar, and if a retune ever let it, the
    # word would still be a lie.
    assert status_for(sigma=0.05, results=0) == STATUS_INITIAL_ESTIMATE


# ---------------------------------------------------------------------------
# The two sides of a four
# ---------------------------------------------------------------------------


def test_a_pair_is_one_player_at_the_average_of_its_two_levels():
    side = one_side((a_rating(3.00, 0.20), a_rating(2.00, 0.20)))

    assert side.mu == pytest.approx(2.50)
    # Independent uncertainties, averaged: the pair is a better-known quantity
    # than either of the people in it.
    assert side.sigma == pytest.approx(math.sqrt(0.20**2 + 0.20**2) / 2)


def test_a_side_of_one_is_that_player():
    side = one_side((a_rating(3.10, 0.31),))

    assert side == a_rating(3.10, 0.31)


def test_a_side_with_nobody_on_it_is_refused():
    """A broken precondition and not somebody's typing, so it is an invariant."""

    with pytest.raises(InvariantViolated):
        one_side(())


def test_carrying_a_weak_partner_to_a_win_pays_more_than_winning_with_an_equal():
    """The average is what made it the upset it was — nothing extra is needed.

    Compared against the *same* player winning the *same* game beside an equal,
    because ``won.mu > player.mu`` on its own is guaranteed by ``win > 0`` for
    every input and would pass whatever the partner did.
    """

    you = a_rating(3.60, 0.25)
    opposition = one_side((a_rating(3.40, 0.20), a_rating(3.30, 0.20)))

    carrying = rating_after(
        player=you,
        own_side=one_side((you, a_rating(2.60, 0.25))),
        opposition=opposition,
        share=SHARED_COURT_SHARE,
        won=True,
        results_so_far=10,
    )
    beside_an_equal = rating_after(
        player=you,
        own_side=one_side((you, a_rating(3.60, 0.25))),
        opposition=opposition,
        share=SHARED_COURT_SHARE,
        won=True,
        results_so_far=10,
    )

    assert carrying.stakes.win > beside_an_equal.stakes.win > 0


def test_both_partners_move_by_the_same_amount_however_far_apart_they_are():
    """**All four move equally**, and a partner is not somebody you are rated against.

    Pricing each player on their own μ would move two people on the same side of
    the same scoreline differently — which the card would have to explain, and
    which pays a strong player to pick a weak partner.
    """

    strong, weak = a_rating(4.00, 0.30), a_rating(2.00, 0.30)
    side = one_side((strong, weak))
    opposition = one_side((a_rating(3.00, 0.30), a_rating(3.00, 0.30)))

    moves = [
        rating_after(
            player=who,
            own_side=side,
            opposition=opposition,
            share=SHARED_COURT_SHARE,
            won=True,
            results_so_far=5,
        )
        for who in (strong, weak)
    ]

    assert moves[0].stakes == moves[1].stakes
    assert moves[0].mu - strong.mu == pytest.approx(moves[1].mu - weak.mu, abs=1e-9)


def test_partners_keep_their_own_certainty_even_sharing_one_level_move():
    """*Skill and certainty are separate variables*, and they separate here too.

    What the evening taught is a property of the game, so both partners gain the
    same information — and fold it into the uncertainty they actually had. A
    newcomer and a player watched for years do not come off one court equally
    sure of themselves.
    """

    newcomer, veteran = a_rating(3.60, SIGMA_FLOOR), a_rating(3.60, 0.15)
    side = one_side((newcomer, veteran))
    opposition = one_side((a_rating(3.40, 0.20), a_rating(3.30, 0.20)))

    moved = [
        rating_after(
            player=who,
            own_side=side,
            opposition=opposition,
            share=SHARED_COURT_SHARE,
            won=True,
            results_so_far=5,
        )
        for who in (newcomer, veteran)
    ]

    assert moved[0].stakes == moved[1].stakes
    assert moved[0].sigma > moved[1].sigma


def test_a_side_of_one_is_what_a_singles_game_and_a_card_both_read():
    """``own_side`` omitted is a side of one.

    So nothing about a two is special-cased, and the card's head-to-head reading
    and a singles game are the same call.
    """

    player = a_rating(2.90, 0.42)
    opposition = a_rating(3.30, 0.22)

    implied = rating_after(
        player=player, opposition=opposition, won=True, results_so_far=6
    )
    spelled = rating_after(
        player=player,
        own_side=player,
        opposition=opposition,
        won=True,
        results_so_far=6,
    )

    assert implied == spelled


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_the_rule_is_a_pure_function_of_its_arguments():
    """Called twice, the same answer — no clock, no randomness, no state."""

    once = rating_after(
        player=FRESH, opposition=SETTLED, won=True, results_so_far=3
    )
    twice = rating_after(
        player=FRESH, opposition=SETTLED, won=True, results_so_far=3
    )

    assert once == twice


#: A corpus the whole rule is walked over, digested to one line. Wide enough that
#: any term dropping out of the arithmetic moves it, and small enough to run in a
#: subprocess twice.
_CORPUS = """
import hashlib, json
from app.engines.racketskill.core import SkillEstimate
from app.engines.racketskill.update_v1 import (
    SHARED_COURT_SHARE, one_side, rating_after, stakes,
)
rows = []
levels = [1.0, 1.7, 2.4, 3.1, 3.8, 4.5, 5.0]
sigmas = [0.84, 0.55, 0.30, 0.15, 0.10]
for share in (1.0, SHARED_COURT_SHARE):
    for pm in levels:
        for ps in sigmas:
            for om in levels:
                for os_ in sigmas:
                    player = SkillEstimate(mu=pm, sigma=ps)
                    side = one_side(
                        (SkillEstimate(mu=om, sigma=os_),
                         SkillEstimate(mu=om - 0.3, sigma=os_))
                    ) if share != 1.0 else SkillEstimate(mu=om, sigma=os_)
                    mine = one_side(
                        (player, SkillEstimate(mu=pm - 0.2, sigma=ps))
                    ) if share != 1.0 else player
                    at = stakes(player=mine, opposition=side, share=share)
                    for won in (True, False):
                        moved = rating_after(
                            player=player, own_side=mine, opposition=side,
                            share=share, won=won, results_so_far=7,
                        )
                        rows.append([at.win, at.loss, moved.mu, moved.sigma,
                                     moved.confidence, moved.status])
print(hashlib.sha256(json.dumps(rows).encode()).hexdigest())
"""


def test_the_whole_rule_reproduces_under_two_hash_seeds():
    """``docs/adr/0105``'s question, asked of the arithmetic itself.

    A rule the marketplace's honesty rests on has to settle the same pairing the
    same way on every machine, and *set iteration order* is the way that stops
    being true in Python without anybody writing anything wrong. Driven through
    a subprocess because ``PYTHONHASHSEED`` is read once, at interpreter start —
    an in-process assertion could not fail.
    """

    import subprocess
    import sys
    from pathlib import Path

    digests = []
    for seed in ("0", "1"):
        run = subprocess.run(
            [sys.executable, "-c", _CORPUS],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[2],
            env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"},
        )
        assert run.returncode == 0, run.stderr
        digests.append(run.stdout.strip())

    assert digests[0] == digests[1]
    assert len(digests[0]) == 64

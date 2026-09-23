"""The played history's own arithmetic: a declared winner, and the score it is.

Everything else this module does is I/O through use cases and is asserted where
the seed asserts everything — against a database, in `test_seed_cohort.py`'s
acceptance test and on the run's own report. What is here is the one decision
`games.py` makes on its own: **what a score is, given who won.**
"""

from __future__ import annotations

import pytest

from app.bootstrap.composition import build_ruleset
from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.games.domain.lineup import GameSide
from app.modules.games.domain.results import Outcome
from app.seeds.cohort import COHORT, PLAYED_GAMES
from app.seeds.games import SCORES, GameRefused, mode_of


class _JustTheRuleset:
    """The one thing `mode_of` reads off the run's paths.

    A hand-written stub rather than the whole wiring, which is what this suite
    does everywhere a use case takes a port: the function under test asks for a
    released ruleset and nothing else, and building a session to give it one
    would be building a database to check a mapping.
    """

    def __init__(self) -> None:
        self.ruleset = build_ruleset()


@pytest.mark.parametrize("side", list(GameSide))
def test_each_score_is_won_by_the_side_it_is_filed_under(side):
    """**Derived from the declared winner rather than declared beside it.**

    `cohort.json` commits *who won*, which is what a player did; the sets are the
    shape of that win. A committed set score would be a second input saying the
    same thing, with the two free to disagree — and the one a card believed would
    be whichever the fold read.
    """

    assert SCORES[side].winner is side


@pytest.mark.parametrize("side", list(GameSide))
def test_the_loser_is_the_other_side_and_nobody_draws(side):
    """A score names a winner — none of the four sports Raketa rates produces a
    draw — so the two outcomes a card can print are both reachable from one
    declared winner and nothing else is."""

    assert SCORES[side].outcome_for(side) is Outcome.WIN
    assert SCORES[side].outcome_for(side.other) is Outcome.LOSS


def test_the_two_scores_disagree_about_who_won():
    """The unscored game is **two sides who disagree**, and this is what makes it
    one: a second score agreeing with the first is a correction nobody objected
    to, and it would confirm rather than leave the game unscored."""

    assert SCORES[GameSide.A].winner is not SCORES[GameSide.B].winner


def test_an_organiser_searches_under_their_own_declaration():
    """**Derived and never tabled.** A member takes whatever the intent cycle
    gave them, and a search run under a mode they never asked for would score
    them against a tolerance they never chose — and, because a court built on a
    *for fun* search opens a **friendly**, it would also quietly stop the game
    counting toward anything.
    """

    for game in PLAYED_GAMES:
        organiser = COHORT.by_handle(game.organiser)

        mode = mode_of(_JustTheRuleset(), organiser, Sport(game.sport))

        assert mode is not SearchMode.FOR_FUN, (
            f"'{organiser.handle}' organises a {game.sport} game under a for-fun "
            f"search, and a court built on one is a friendly — which was never "
            f"evidence about anybody, by the choice of the people who arranged it"
        )


def test_a_sport_the_organiser_never_declared_is_refused_by_name():
    """Play intent is declared **per sport** (ADR-0094), so a sport a member
    never declared has no mode to run a search under — and the refusal names the
    member rather than raising a `KeyError` naming a dictionary."""

    padel_only = next(
        member
        for member in COHORT.members
        if Sport.TENNIS not in member.sports
    )

    with pytest.raises(GameRefused, match=padel_only.handle):
        mode_of(_JustTheRuleset(), padel_only, Sport.TENNIS)

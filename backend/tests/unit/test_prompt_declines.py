"""*Not now* — what a decline is keyed on, and what it may not be keyed on.

Three prompts suppress and one does not, and the three do not all key the same
way. That asymmetry is the whole of this file: it is easy to state and easy to
get subtly wrong, and getting it wrong is invisible — a decline keyed too widely
silences a question about tennis that a player answered about padel, and one
keyed too narrowly re-asks them next month with a different number in it.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.kernel import InvariantViolated, Sport
from app.modules.matchmaking.domain.declines import (
    DECLINE_KEYS,
    DECLINE_SUPPRESS,
    PromptDecline,
    keyed_sport,
    silence_began,
    suppresses,
)
from app.modules.matchmaking.domain.prompts import Prompt
from tests.unit.matchmaking_builders import player

NOW = datetime(2026, 8, 30, 18, 0, tzinfo=timezone.utc)
ALICE = player(1)


def test_every_prompt_says_whether_it_suppresses():
    """**Total over the union.** A fifth prompt added in two years has to answer
    here, rather than defaulting to whichever half the mapping happened to hold."""

    assert set(DECLINE_KEYS) == set(Prompt)


def test_the_improvised_week_is_the_one_prompt_that_buys_no_silence():
    """Ruled out in writing, and by citation rather than by omission: a grid
    legitimately differs per search where a radius, a declaration and a described
    week do not."""

    assert not suppresses(Prompt.KEEP_THESE_TIMES)
    assert all(
        suppresses(prompt) for prompt in Prompt if prompt is not Prompt.KEEP_THESE_TIMES
    )


def test_a_declaration_is_declined_for_one_sport():
    """ADR-0094's *for that sport*, kept literally: intent is per sport."""

    assert keyed_sport(Prompt.UPDATE_PLAY_INTENT, Sport.PADEL) is Sport.PADEL


def test_the_radius_and_the_week_are_declined_for_the_player():
    """The asymmetry, and the reason for it. The grid is one week and not seven,
    and the radius is one number on a profile with no sport dimension — so a
    padel-driven prompt keyed per sport would go on offering to change tennis
    with the same number."""

    assert keyed_sport(Prompt.KEEP_THIS_RADIUS, Sport.PADEL) is None
    assert keyed_sport(Prompt.REFRESH_YOUR_TIMES, Sport.PADEL) is None


def test_a_prompt_that_suppresses_nothing_has_no_key_to_be_given():
    with pytest.raises(InvariantViolated):
        keyed_sport(Prompt.KEEP_THESE_TIMES, Sport.PADEL)


def test_a_decline_of_the_one_prompt_that_does_not_suppress_is_not_a_row():
    """It would be a row nothing ever reads: the filter that consults these never
    asks about the improvised week."""

    with pytest.raises(InvariantViolated):
        PromptDecline(
            player_id=ALICE, prompt=Prompt.KEEP_THESE_TIMES, sport=None, at=NOW
        )


def test_a_row_may_not_be_keyed_against_what_its_prompt_is_keyed_on():
    """Both directions, because both are how the asymmetry gets lost: a radius
    remembered per sport, and a declaration remembered for every sport at once."""

    with pytest.raises(InvariantViolated):
        PromptDecline(
            player_id=ALICE,
            prompt=Prompt.KEEP_THIS_RADIUS,
            sport=Sport.PADEL,
            at=NOW,
        )
    with pytest.raises(InvariantViolated):
        PromptDecline(
            player_id=ALICE, prompt=Prompt.UPDATE_PLAY_INTENT, sport=None, at=NOW
        )


def test_the_silence_is_thirty_days_and_it_is_a_date():
    """A cut-off rather than a stored flag, so nothing goes stale hourly."""

    assert DECLINE_SUPPRESS.days == 30
    assert silence_began(NOW) == NOW - DECLINE_SUPPRESS

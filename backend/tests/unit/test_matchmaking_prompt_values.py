"""The value a raised prompt carries, and the two absences it keeps apart.

``RaisedPrompt`` holds one payload field per prompt and every one of them says
*this is not that prompt* by being absent. The grid's field is the one that also
has to be able to say **a cleared week**, because a player may untick every cell
and search anyway — so ``None`` and ``()`` are two answers here, where every
other field has only the one.

Beside it, the one rule three surfaces now share: **a week that is not the
profile's is an improvised one**, and it is asked about wherever it was consumed.
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated
from app.modules.matchmaking.domain.prompts import (
    Prompt,
    RaisedPrompt,
    improvised_week,
)
from app.modules.player_profile.domain.weekly_hours import WeeklyHours

A_WEEK = WeeklyHours.from_codes(("2:19", "6:10"))
ANOTHER_WEEK = WeeklyHours.from_codes(("4:19",))
CLEARED = WeeklyHours.blank()


def test_a_cleared_week_is_a_legal_value_to_ask_about():
    """**The bug this file exists for.** A player who unticked every cell
    improvised a week exactly as one who ticked a new cell did, and the prompt
    that offers to save it has to be able to carry what they did."""

    raised = RaisedPrompt(prompt=Prompt.KEEP_THESE_TIMES, slots=())

    assert raised.slots == ()


def test_a_grid_prompt_carrying_no_grid_at_all_is_a_broken_prompt():
    """``None`` is *not this prompt*, so a ``KEEP_THESE_TIMES`` with it is a
    prompt about nothing rather than a prompt about an empty week."""

    with pytest.raises(InvariantViolated):
        RaisedPrompt(prompt=Prompt.KEEP_THESE_TIMES)


def test_another_prompt_carrying_an_empty_week_is_a_broken_prompt():
    """The other side of the same distinction: ``()`` is a cleared week, which
    is a fact only one of the four prompts has anything to say about."""

    with pytest.raises(InvariantViolated):
        RaisedPrompt(prompt=Prompt.REFRESH_YOUR_TIMES, slots=())


def test_the_other_two_payloads_still_have_one_absence_each():
    """Nothing here widened the other two fields: a radius of *nothing* and a
    mode of *nothing* remain the single spelling they always were."""

    assert RaisedPrompt(prompt=Prompt.REFRESH_YOUR_TIMES).slots is None
    with pytest.raises(InvariantViolated):
        RaisedPrompt(prompt=Prompt.KEEP_THIS_RADIUS)


def test_a_search_on_the_profiles_own_week_improvises_nothing():
    assert improvised_week(asked=A_WEEK, profile=A_WEEK) is None


def test_a_week_that_is_not_the_profiles_is_asked_about():
    raised = improvised_week(asked=ANOTHER_WEEK, profile=A_WEEK)

    assert raised is not None
    assert raised.prompt is Prompt.KEEP_THESE_TIMES
    assert raised.slots == ("4:19",)


def test_clearing_the_week_is_an_edit_and_is_asked_about_too():
    """The case that used to `500` one line past the one that used to `400`."""

    raised = improvised_week(asked=CLEARED, profile=A_WEEK)

    assert raised is not None
    assert raised.slots == ()


def test_a_profile_that_was_already_blank_improvises_nothing_by_staying_blank():
    """A profile committed before the floor existed, searched with no override:
    the grids agree, and agreement raises nothing whatever they hold."""

    assert improvised_week(asked=CLEARED, profile=CLEARED) is None

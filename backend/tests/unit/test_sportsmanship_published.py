"""The published fold: an average out of five, for everybody it is shown to.

**One answer off one window.** Every reader is shown the figure beside how many
different people it rests on — the subject included, since ``docs/adr/0179`` §5
retired the coarse band that used to stand in for it on their own sheet and
accepted the cost by name. What is asserted here is the fold itself, which did
not move: the mean, the rounding, and the two absences.

**The collapse is not tested here.** *Only a rater's most recent stars count* is
the primary key of ``sportsmanship_rating`` and not arithmetic, so the place it
can fail is a database and it is contracted in ``tests/demands/``.
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated
from app.modules.sportsmanship.domain.published import (
    RATER_WINDOW,
    PublishedSportsmanship,
    published_from,
)


def test_one_rating_publishes_and_says_it_rests_on_one_person():
    """**No minimum, and the count is what makes that safe.** ``3,0 / 5 · 1
    player`` is visibly one person's opinion and reads as one, which is the same
    discipline the metered rows take by printing their raw pairs."""

    assert published_from([3]) == PublishedSportsmanship(average=3.0, raters=1)


def test_the_count_is_people_and_never_ratings():
    """Each row in the window is one rater's standing answer, so the count of
    them **is** the number of different people with an opinion."""

    published = published_from([5, 4, 4])

    assert published is not None
    assert published.raters == 3


def test_nobody_has_said_anything_is_an_absence_and_never_a_nought():
    """A person nobody has rated has no figure, and the record omits the zone.
    A nought here would publish *they are unpleasant* about somebody nobody has
    ever been asked about."""

    assert published_from([]) is None


def test_a_half_rounds_up_rather_than_to_even():
    """``round`` rounds halves to even, so 4,25 would print 4,2 and 4,35 would
    print 4,4 — a rule nobody reading a figure out of five expects. The platform
    already spells half-up once for percentages, and this is that rule at one
    decimal."""

    assert published_from([4, 4, 4, 5]).average == 4.3  # 4.25 exactly


def test_the_figure_is_one_decimal_and_the_rounding_happens_once():
    """**Derived here and nowhere else.** Nothing downstream divides again, and
    nothing downstream coarsens — the figure the subject reads is this one."""

    assert published_from([5, 4, 4, 4, 3, 3, 3]).average == 3.7


def test_a_window_wider_than_the_rule_is_a_broken_precondition():
    """The window is applied where the rows are read and is **checked** here, so
    a caller that over-fetched cannot quietly publish a figure over a wider
    record than the rule allows. A broken precondition and not a refusal: no
    person typed this."""

    with pytest.raises(InvariantViolated):
        published_from([5] * (RATER_WINDOW + 1))


def test_the_published_scale_and_the_tapped_scale_are_the_same_two_numbers():
    """**Two bounds for two things, asserted rather than assumed.** ``card.py``
    bounds what a person may tap and this module bounds what a mean of taps may
    be; they are the same pair for one reason and not by construction, so the day
    a half-star arrives the disagreement goes red here rather than publishing a
    figure off the scale a reader is told it sits on."""

    from app.modules.sportsmanship.domain.card import MAXIMUM_STARS, MINIMUM_STARS
    from app.modules.sportsmanship.domain.published import (
        HIGHEST_AVERAGE,
        LOWEST_AVERAGE,
    )

    assert (LOWEST_AVERAGE, HIGHEST_AVERAGE) == (
        float(MINIMUM_STARS),
        float(MAXIMUM_STARS),
    )

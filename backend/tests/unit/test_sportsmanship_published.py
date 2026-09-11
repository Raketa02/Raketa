"""The published fold: an average out of five, and the band the subject sees.

**Two answers off one window, and the second one cannot say the first.** A reader
is shown the figure beside how many different people it rests on; the person it is
about is shown a coarse band and no count. That asymmetry is the whole of
``docs/adr/0158``'s privacy argument — an average plus a count lets the subject
subtract, name each new rating exactly, and go and find the one person who could
have given it — so it is asserted here at the rule rather than only at the route.

**The collapse is not tested here.** *Only a rater's most recent stars count* is
the primary key of ``sportsmanship_rating`` and not arithmetic, so the place it
can fail is a database and it is contracted in ``tests/demands/``. What this file
owns is the fold over whatever window that key produced: the mean, the rounding,
the band's edges, and the two absences.
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated
from app.modules.sportsmanship.domain.published import (
    RATER_WINDOW,
    PublishedSportsmanship,
    SportsmanshipBand,
    band_of,
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
    """**Derived here and nowhere else.** The band below is taken from this
    number rather than from the raw mean, so nothing downstream ever divides
    again."""

    assert published_from([5, 4, 4, 4, 3, 3, 3]).average == 3.7


def test_a_window_wider_than_the_rule_is_a_broken_precondition():
    """The window is applied where the rows are read and is **checked** here, so
    a caller that over-fetched cannot quietly publish a figure over a wider
    record than the rule allows. A broken precondition and not a refusal: no
    person typed this."""

    with pytest.raises(InvariantViolated):
        published_from([5] * (RATER_WINDOW + 1))


@pytest.mark.parametrize(
    "average, expected",
    [
        (5.0, SportsmanshipBand.GOOD),
        (4.0, SportsmanshipBand.GOOD),
        (3.9, SportsmanshipBand.MIXED),
        (3.0, SportsmanshipBand.MIXED),
        (2.9, SportsmanshipBand.POOR),
        (1.0, SportsmanshipBand.POOR),
    ],
)
def test_the_band_is_three_steps_across_the_whole_scale(average, expected):
    """**Deliberately too coarse to name a rating.** Whole-star edges over a
    one-to-five scale: it tells somebody that something is going wrong, which is
    the useful half, and never who to blame for it."""

    assert band_of(average) is expected


def test_the_band_is_taken_from_the_published_figure_and_not_the_raw_mean():
    """**One number, coarsened.** A band read off the unrounded mean could
    disagree with the figure a reader is shown at an edge — 3,96 prints 4,0 to a
    stranger, and a subject told *mixed* would be looking at a different record
    from everybody else."""

    published = published_from([4] * 23 + [3])

    assert published.average == 4.0
    assert band_of(published.average) is SportsmanshipBand.GOOD


def test_the_published_scale_and_the_tapped_scale_are_the_same_two_numbers():
    """**Two bounds for two things, asserted rather than assumed.** ``card.py``
    bounds what a person may tap and this module bounds what a mean of taps may
    be; they are the same pair for one reason and not by construction, so the day
    a half-star arrives the disagreement goes red here rather than publishing a
    figure the band has no step for."""

    from app.modules.sportsmanship.domain.card import MAXIMUM_STARS, MINIMUM_STARS
    from app.modules.sportsmanship.domain.published import (
        HIGHEST_AVERAGE,
        LOWEST_AVERAGE,
    )

    assert (LOWEST_AVERAGE, HIGHEST_AVERAGE) == (
        float(MINIMUM_STARS),
        float(MAXIMUM_STARS),
    )


def test_every_band_edge_lies_inside_the_scale_it_coarsens():
    """A step whose edge sits off the scale is a step nothing can land in."""

    from app.modules.sportsmanship.domain.published import (
        GOOD_FROM,
        HIGHEST_AVERAGE,
        LOWEST_AVERAGE,
        MIXED_FROM,
    )

    assert LOWEST_AVERAGE < MIXED_FROM < GOOD_FROM < HIGHEST_AVERAGE
    assert {band_of(LOWEST_AVERAGE), band_of(HIGHEST_AVERAGE)} == {
        SportsmanshipBand.POOR,
        SportsmanshipBand.GOOD,
    }

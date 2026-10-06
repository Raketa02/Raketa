"""The Player profile's value objects: what each one refuses, and what it fixes.

These are the rules a client also enforces, and the reason to test them here is
that a client enforcing them is not the same as this platform enforcing them —
a disabled button is absent from a replayed request (``docs/adr/0089``).
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated, iso_weekday
from app.modules.player_profile.domain.errors import (
    DuplicateSocialTag,
    SocialTagSelectionOutOfBounds,
    UnknownSocialTag,
    WeeklyHoursEmpty,
)
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.social_tags import (
    SOCIAL_TAG_SELECTION_BOUNDS,
    SOCIAL_TAG_VOCABULARY,
    SocialTag,
    SocialTagSelection,
)
from app.modules.player_profile.domain.weekly_hours import (
    DAY_RANGES,
    FIRST_HOUR,
    HOURS_OF_THE_DAY,
    LAST_HOUR,
    WeeklyHour,
    WeeklyHours,
)


def hour(day: int, at: int) -> WeeklyHour:
    return WeeklyHour(day=iso_weekday(day), hour=at)


# ---------------------------------------------------------------------------
# Social tag selection
# ---------------------------------------------------------------------------


def test_a_selection_at_each_end_of_the_bounds_is_accepted():
    every_tag = [tag for group in SOCIAL_TAG_VOCABULARY.values() for tag in group]

    floor = SocialTagSelection.chosen(
        every_tag[: SOCIAL_TAG_SELECTION_BOUNDS.minimum_tags]
    )
    ceiling = SocialTagSelection.chosen(
        every_tag[: SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags]
    )

    assert len(floor) == SOCIAL_TAG_SELECTION_BOUNDS.minimum_tags
    assert len(ceiling) == SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags


def test_a_selection_below_the_floor_is_refused():
    with pytest.raises(SocialTagSelectionOutOfBounds):
        SocialTagSelection.chosen([SocialTag.PLAYS_TO_WIN])


def test_a_selection_above_the_ceiling_is_refused():
    every_tag = [tag for group in SOCIAL_TAG_VOCABULARY.values() for tag in group]
    too_many = every_tag[: SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags + 1]

    with pytest.raises(SocialTagSelectionOutOfBounds):
        SocialTagSelection.chosen(too_many)


def test_a_tag_id_outside_the_vocabulary_is_refused_with_its_own_code():
    """Its own error, not "invalid selection" — the recovery is to re-read the
    options, which is a different thing to ask of a client than *pick fewer*."""

    with pytest.raises(UnknownSocialTag):
        SocialTagSelection.from_ids(["PLAYS_TO_WIN", "LOOKING_FOR_A_DATE"])


def test_a_repeated_tag_is_refused_rather_than_collapsed():
    """Collapsing would refuse a player for their client's mistake and tell them
    they had picked too few, which is a sentence nobody can act on."""

    with pytest.raises(DuplicateSocialTag):
        SocialTagSelection.from_ids(
            ["PLAYS_TO_WIN", "PLAYS_TO_WIN", "HERE_TO_IMPROVE"]
        )


def test_a_selection_is_held_in_vocabulary_order_whatever_order_it_arrived_in():
    forwards = SocialTagSelection.from_ids(["STAYS_FOR_A_DRINK", "HERE_TO_IMPROVE"])
    backwards = SocialTagSelection.from_ids(["HERE_TO_IMPROVE", "STAYS_FOR_A_DRINK"])

    assert forwards == backwards
    assert forwards.ids == ("STAYS_FOR_A_DRINK", "HERE_TO_IMPROVE")


def test_a_selection_already_on_a_stream_is_not_re_counted():
    """**The write path refuses; the fold accepts**: the ceiling is a number
    product may lower, and a fold that could refuse a recorded fact would
    un-rehydrate every profile above the new one."""

    every_tag = [tag for group in SOCIAL_TAG_VOCABULARY.values() for tag in group]
    was_legal_once = [
        tag.value for tag in every_tag[: SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags + 2]
    ]

    recorded = SocialTagSelection.recorded(was_legal_once)

    assert len(recorded) == len(was_legal_once)
    with pytest.raises(SocialTagSelectionOutOfBounds):
        SocialTagSelection.from_ids(was_legal_once), "but the write path still refuses"


def test_an_unparseable_tag_id_still_raises_on_replay():
    """Not the same hazard as a moved bound: **a tag id is permanent**, never
    reused and never renamed, so an id on a stream is one this enum still holds.
    A failure here means that invariant was broken — a bug to hear about."""

    with pytest.raises(UnknownSocialTag):
        SocialTagSelection.recorded(["NO_SUCH_TAG"])


# ---------------------------------------------------------------------------
# Weekly hours
# ---------------------------------------------------------------------------


def test_the_write_path_refuses_a_week_with_nothing_ticked():
    """The floor ADR-0102 put on the week: at least one hour of the 112.

    ``of_cells`` is the command path's entry point, so this is the one place a
    player's own answer is counted — and a commit that ticked nothing is refused
    with a code of its own rather than recorded as a measured zero.
    """

    with pytest.raises(WeeklyHoursEmpty):
        WeeklyHours.of_cells(())


def test_one_ticked_hour_is_enough():
    """The minimum is exactly one, and one tick is a real answer: a player who
    only ever plays at ten on a Saturday must be able to say precisely that."""

    week = WeeklyHours.of_cells([(6, 10)])

    assert week.codes == ("6:10",)


def test_the_fold_still_accepts_a_blank_week():
    """**The write path refuses; the fold accepts** — ``social_tags``' split,
    verbatim.

    A player may clear their week after committing, and that is not a stream a
    replay may refuse to rehydrate, so ``blank``, ``of`` and ``from_codes`` take
    an empty week: a blank week met anyway is *absent*, never zero (ADR-0102
    part 3, amended by ADR-0189).
    """

    assert len(WeeklyHours.blank()) == 0
    assert WeeklyHours.blank().codes == ()
    assert WeeklyHours.of(()).codes == ()
    assert WeeklyHours.from_codes(()).codes == ()


def test_a_later_edit_of_the_week_may_clear_it():
    """``edited`` is the floor's named exit, and it takes the same primitives.

    ``SocialTagSelection.from_ids`` / ``recorded``'s discipline, applied to the
    week:
    two named constructors, so every call site says which of the two it is. The
    commit path refuses a blank week; a player clearing theirs afterwards is a
    later edit, and the minimum binds the answer they were asked for rather
    than every edit of it.
    """

    assert WeeklyHours.edited(()).codes == ()
    assert WeeklyHours.edited([(6, 10)]).codes == ("6:10",)


def test_an_edited_week_is_folded_exactly_as_a_committed_one_is():
    """Same fold, same order, same refusals — the floor is the only difference,
    so an edit cannot quietly hold a week a commit could not."""

    week = WeeklyHours.edited([(3, 8), (1, 19), (3, 8)])

    assert week.codes == ("1:19", "3:8")
    with pytest.raises(InvariantViolated):
        WeeklyHours.edited([(1, 23)])


def test_the_week_runs_from_seven_in_the_morning_to_eleven_at_night():
    """Sixteen one-hour cells a day: the first starts at 07:00 and the last at
    22:00, so the grid ends at 23:00 (the mechanics §4.2)."""

    assert (FIRST_HOUR, LAST_HOUR) == (7, 22)
    assert len(HOURS_OF_THE_DAY) == 16
    assert hour(1, 7).code == "1:7"
    assert hour(7, 22).code == "7:22"
    for outside in (6, 23, 0):
        with pytest.raises(InvariantViolated):
            hour(1, outside)


def test_the_day_is_summarised_in_three_ranges_that_share_no_hour():
    """Morning 07–12, Afternoon 12–17, Evening 17–23 (the mechanics §9.1, Q71):
    every hour of the day in exactly one of them, in the order a day runs."""

    assert {name: (hours[0], hours[-1] + 1) for name, hours in DAY_RANGES.items()} == {
        "MORNING": (7, 12),
        "AFTERNOON": (12, 17),
        "EVENING": (17, 23),
    }
    every = [hour for hours in DAY_RANGES.values() for hour in hours]
    assert every == list(HOURS_OF_THE_DAY)


def test_a_repeated_hour_is_collapsed_rather_than_refused():
    """The opposite of a repeated tag, and deliberately: a week is a set of
    hours, and an hour ticked twice is ticked."""

    week = WeeklyHours.of([hour(2, 9), hour(2, 9)])

    assert len(week) == 1


def test_a_week_is_held_in_reading_order_whatever_order_it_arrived_in():
    """Day first, then hour — and nine before ten, which is not what comparing
    the two codes as text would give."""

    week = WeeklyHours.of([hour(3, 7), hour(1, 10), hour(1, 9), hour(1, 22)])

    assert week.codes == ("1:9", "1:10", "1:22", "3:7")


def test_a_week_round_trips_through_the_codes_a_stream_stores():
    week = WeeklyHours.of([hour(7, 21), hour(1, 7)])

    assert WeeklyHours.from_codes(week.codes) == week


def test_a_day_outside_the_week_is_a_broken_precondition():
    """Through the kernel's own factory, so 0 and 8 are refused here exactly as
    they are refused anywhere else a weekday is built."""

    with pytest.raises(InvariantViolated):
        WeeklyHour(day=iso_weekday(8), hour=10)


@pytest.mark.parametrize("code", ["1:NIGHT", "1:EVENING", "1:23", "9:10", "1-10"])
def test_a_code_that_did_not_come_from_an_hour_is_refused(code):
    """A stored part of the day from before the week became hours is one of
    them: nothing is in production, so it is a corrupt stream and not a value to
    translate (ADR-0189 §5)."""

    with pytest.raises(InvariantViolated):
        WeeklyHours.from_codes([code])


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------


def test_a_precise_fix_is_coarsened_before_anything_can_store_it():
    area = LocationArea.around(51.5073509, -0.1277583)

    assert (area.latitude, area.longitude) == (51.51, -0.13)


def test_two_fixes_in_the_same_area_become_the_same_area():
    """Which is the property that makes the precise fix unrecoverable, rather
    than merely unshown."""

    assert LocationArea.around(51.5073, -0.1277) == LocationArea.around(
        51.5081, -0.1284
    )

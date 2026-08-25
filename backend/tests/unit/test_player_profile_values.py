"""The Player profile's value objects: what each one refuses, and what it fixes.

These are the rules a client also enforces, and the reason to test them here is
that a client enforcing them is not the same as this platform enforcing them —
a disabled button is absent from a replayed request (``docs/adr/0089``).
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated, iso_weekday
from app.modules.player_profile.domain.availability import (
    AvailabilityGrid,
    AvailabilitySlot,
    DayPart,
)
from app.modules.player_profile.domain.consent import (
    ConsentSurface,
    ProposalsOptIn,
)
from app.modules.player_profile.domain.errors import (
    DuplicateSocialTag,
    SearchRadiusOutOfBounds,
    SocialTagSelectionOutOfBounds,
    UnknownSocialTag,
)
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.search_radius import (
    SEARCH_RADIUS_BOUNDS,
    SearchRadius,
)
from app.modules.player_profile.domain.social_tags import (
    SOCIAL_TAG_SELECTION_BOUNDS,
    SOCIAL_TAG_VOCABULARY,
    SocialTag,
    SocialTagSelection,
)
from tests.unit.fake_event_store import utc


def slot(day: int, part: DayPart) -> AvailabilitySlot:
    return AvailabilitySlot(day=iso_weekday(day), part=part)


# ---------------------------------------------------------------------------
# Social tag selection
# ---------------------------------------------------------------------------


def test_a_selection_at_each_end_of_the_bounds_is_accepted():
    every_tag = [tag for group in SOCIAL_TAG_VOCABULARY.values() for tag in group]

    floor = SocialTagSelection.of(
        every_tag[: SOCIAL_TAG_SELECTION_BOUNDS.minimum_tags]
    )
    ceiling = SocialTagSelection.of(
        every_tag[: SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags]
    )

    assert len(floor) == SOCIAL_TAG_SELECTION_BOUNDS.minimum_tags
    assert len(ceiling) == SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags


def test_a_selection_below_the_floor_is_refused():
    with pytest.raises(SocialTagSelectionOutOfBounds):
        SocialTagSelection.of([SocialTag.PLAYS_TO_WIN])


def test_a_selection_above_the_ceiling_is_refused():
    every_tag = [tag for group in SOCIAL_TAG_VOCABULARY.values() for tag in group]
    too_many = every_tag[: SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags + 1]

    with pytest.raises(SocialTagSelectionOutOfBounds):
        SocialTagSelection.of(too_many)


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


# ---------------------------------------------------------------------------
# Search radius
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kilometres",
    [SEARCH_RADIUS_BOUNDS.minimum_km, SEARCH_RADIUS_BOUNDS.maximum_km],
)
def test_both_ends_of_the_served_range_are_a_radius(kilometres: int):
    assert SearchRadius(kilometres=kilometres).kilometres == kilometres


@pytest.mark.parametrize(
    "kilometres",
    [SEARCH_RADIUS_BOUNDS.minimum_km - 1, SEARCH_RADIUS_BOUNDS.maximum_km + 1],
)
def test_a_radius_outside_the_served_range_is_refused(kilometres: int):
    with pytest.raises(SearchRadiusOutOfBounds):
        SearchRadius(kilometres=kilometres)


def test_the_default_radius_is_the_one_the_control_opens_at():
    assert SearchRadius.default().kilometres == SEARCH_RADIUS_BOUNDS.default_km


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------


def test_a_blank_grid_is_a_grid():
    """The invariant the commit rests on: blank means no preference, and is an
    answer rather than the absence of one."""

    assert len(AvailabilityGrid.blank()) == 0
    assert AvailabilityGrid.blank().codes == ()


def test_a_repeated_cell_is_collapsed_rather_than_refused():
    """The opposite of a repeated tag, and deliberately: a grid is a set of
    cells, and a cell ticked twice is ticked."""

    grid = AvailabilityGrid.of(
        [slot(2, DayPart.MORNING), slot(2, DayPart.MORNING)]
    )

    assert len(grid) == 1


def test_a_grid_is_held_in_reading_order_whatever_order_it_arrived_in():
    """Day first, then part of day — and *morning* before *afternoon*, which is
    not what comparing the two enum values as text would give."""

    grid = AvailabilityGrid.of(
        [
            slot(3, DayPart.MORNING),
            slot(1, DayPart.EVENING),
            slot(1, DayPart.AFTERNOON),
            slot(1, DayPart.MORNING),
        ]
    )

    assert grid.codes == ("1:MORNING", "1:AFTERNOON", "1:EVENING", "3:MORNING")


def test_a_grid_round_trips_through_the_codes_a_stream_stores():
    grid = AvailabilityGrid.of([slot(7, DayPart.EVENING), slot(1, DayPart.MORNING)])

    assert AvailabilityGrid.from_codes(grid.codes) == grid


def test_a_day_outside_the_week_is_a_broken_precondition():
    """Through the kernel's own factory, so 0 and 8 are refused here exactly as
    they are refused anywhere else a weekday is built."""

    with pytest.raises(InvariantViolated):
        AvailabilitySlot(day=iso_weekday(8), part=DayPart.MORNING)


def test_a_slot_code_that_did_not_come_from_a_slot_is_refused():
    with pytest.raises(InvariantViolated):
        AvailabilityGrid.from_codes(["1:NIGHT"])


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


# ---------------------------------------------------------------------------
# Consent
# ---------------------------------------------------------------------------


def test_a_consent_record_cannot_be_built_without_the_words_it_was_given_against():
    with pytest.raises(InvariantViolated):
        ProposalsOptIn(
            accepted=True,
            copy_version="   ",
            surface=ConsentSurface.ONBOARDING,
            answered_at=utc(2026, 8, 25),
        )

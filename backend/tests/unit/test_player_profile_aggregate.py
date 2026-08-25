"""The PlayerProfile aggregate: what creation records, and what a change does.

Two things are being asserted throughout, and they are the two ADR-0089 turns
on. **The consent answer is its own event, appended by the creating commit as
well as by every later change** — so a reader of consent history has one event
type and no special first case. And **a preference transition that changes
nothing records nothing**, while the consent transition always records.
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated, iso_weekday
from app.modules.player_profile.domain.availability import (
    AvailabilityGrid,
    AvailabilitySlot,
    DayPart,
)
from app.modules.player_profile.domain.consent import ConsentSurface
from app.modules.player_profile.domain.errors import DuplicatePhoto, TooManyPhotos
from app.modules.player_profile.domain.events import (
    AvailabilityChanged,
    LocationChanged,
    PhotosChanged,
    PlayerProfileCreated,
    ProposalsOptInAnswered,
    SearchRadiusChanged,
    SocialTagsChanged,
)
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.profile import (
    MAX_PROFILE_PHOTOS,
    PlayerProfile,
)
from app.modules.player_profile.domain.search_radius import SearchRadius
from app.modules.player_profile.domain.social_tags import SocialTagSelection
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import utc

PLAYER = new_uuid()
CREATED_AT = utc(2026, 8, 25)
LATER = utc(2026, 9, 1)
TAGS = ("PLAYS_TO_WIN", "HERE_TO_IMPROVE")


def a_profile(**overrides) -> PlayerProfile:
    """A committed profile, with every answer given and nothing left implicit."""

    arguments = dict(
        player_id=PLAYER,
        social_tags=SocialTagSelection.from_ids(TAGS),
        photo_ids=(),
        availability=AvailabilityGrid.of(
            [AvailabilitySlot(day=iso_weekday(2), part=DayPart.EVENING)]
        ),
        location=LocationArea.around(51.5074, -0.1278),
        search_radius=SearchRadius(kilometres=10),
        proposals_opt_in_accepted=True,
        consent_copy_version="proposals-2026-08",
        consent_surface=ConsentSurface.ONBOARDING,
        idempotency_key="commit-1",
        occurred_at=CREATED_AT,
    )
    arguments.update(overrides)
    return PlayerProfile.create(**arguments)


def replayed(profile: PlayerProfile) -> PlayerProfile:
    """The same profile rebuilt from the events it just recorded."""

    return PlayerProfile.from_history(profile.pull_events())


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


def test_creation_records_the_preferences_and_the_consent_as_two_events():
    profile = a_profile()

    recorded = profile.pull_events()

    assert [type(event) for event in recorded] == [
        PlayerProfileCreated,
        ProposalsOptInAnswered,
    ]


def test_the_creating_commit_appends_the_same_consent_event_a_later_change_does():
    """The whole of "one sequence with no special first case": a reader after
    every answer this player ever gave replays one event type."""

    profile = a_profile()
    created, consent = profile.pull_events()

    assert isinstance(consent, ProposalsOptInAnswered)
    assert consent.accepted is True
    assert consent.copy_version == "proposals-2026-08"
    assert consent.surface == ConsentSurface.ONBOARDING.value
    # The moment is the event's own, and it is the moment of the commit — the
    # consent and the preferences it arrived with cannot be timestamped apart.
    assert consent.occurred_at == created.occurred_at == CREATED_AT


def test_the_creating_event_carries_the_key_the_commit_was_made_under():
    """Which is what lets a retry be recognised without a table beside the
    stream to keep in step with it."""

    created, _ = a_profile(idempotency_key="draft-7").pull_events()

    assert created.idempotency_key == "draft-7"


def test_a_created_profile_replays_to_itself():
    profile = a_profile()
    expected = (
        profile.social_tags,
        profile.availability,
        profile.location,
        profile.search_radius,
        profile.proposals_opt_in,
        profile.idempotency_key,
    )

    rebuilt = replayed(profile)

    assert (
        rebuilt.social_tags,
        rebuilt.availability,
        rebuilt.location,
        rebuilt.search_radius,
        rebuilt.proposals_opt_in,
        rebuilt.idempotency_key,
    ) == expected
    assert rebuilt.version == 2, "two events, two versions"


def test_a_blank_availability_grid_is_committed_as_an_answer():
    """Blank means no preference and never *leave me out*, so it is stored as an
    empty grid rather than refused or filled in."""

    profile = a_profile(availability=AvailabilityGrid.blank())
    created, _ = profile.pull_events()

    assert created.availability == ()
    assert len(profile.availability) == 0


def test_photos_keep_the_order_the_player_arranged_them_in():
    """Order is meaning: the first photo is the one a player card shows."""

    first, second = new_uuid(), new_uuid()

    profile = a_profile(photo_ids=[second, first])

    assert profile.photo_ids == (second, first)
    assert replayed(profile).photo_ids == (second, first)


def test_more_photos_than_a_profile_may_hold_is_refused():
    too_many = [new_uuid() for _ in range(MAX_PROFILE_PHOTOS + 1)]

    with pytest.raises(TooManyPhotos):
        a_profile(photo_ids=too_many)


def test_the_same_photo_twice_is_refused_rather_than_deduplicated():
    """Deduplicating would silently reorder tiles a player arranged."""

    photo = new_uuid()

    with pytest.raises(DuplicatePhoto):
        a_profile(photo_ids=[photo, photo])


# ---------------------------------------------------------------------------
# Later changes
# ---------------------------------------------------------------------------


def test_each_preference_has_its_own_change_event():
    profile = replayed(a_profile())

    profile.change_social_tags(
        SocialTagSelection.from_ids(["QUIET_AND_FOCUSED", "HERE_TO_COMPETE"]),
        occurred_at=LATER,
    )
    profile.change_photos([new_uuid()], occurred_at=LATER)
    profile.change_availability(AvailabilityGrid.blank(), occurred_at=LATER)
    profile.change_location(LocationArea.around(48.85, 2.35), occurred_at=LATER)
    profile.change_search_radius(SearchRadius(kilometres=25), occurred_at=LATER)

    assert [type(event) for event in profile.pull_events()] == [
        SocialTagsChanged,
        PhotosChanged,
        AvailabilityChanged,
        LocationChanged,
        SearchRadiusChanged,
    ]


def test_a_preference_set_to_what_it_already_is_records_nothing():
    """So an idempotent client retry cannot grow a stream by an event that says
    the player did not do anything."""

    profile = replayed(a_profile())

    profile.change_social_tags(
        SocialTagSelection.from_ids(TAGS), occurred_at=LATER
    )
    profile.change_search_radius(SearchRadius(kilometres=10), occurred_at=LATER)
    profile.change_location(
        LocationArea.around(51.5074, -0.1278), occurred_at=LATER
    )
    profile.change_photos([], occurred_at=LATER)

    assert profile.pull_events() == []


def test_re_answering_the_opt_in_with_the_same_answer_is_still_recorded():
    """The deliberate exception, and the point of the aggregate: *asked again,
    against these words, and said yes again* is a fact about consent."""

    profile = replayed(a_profile())

    profile.answer_proposals_opt_in(
        accepted=True,
        copy_version="proposals-2026-09",
        surface=ConsentSurface.PROFILE,
        occurred_at=LATER,
    )

    recorded = profile.pull_events()
    assert [type(event) for event in recorded] == [ProposalsOptInAnswered]
    assert recorded[0].copy_version == "proposals-2026-09"
    assert recorded[0].surface == ConsentSurface.PROFILE.value


def test_the_standing_answer_is_the_latest_one_and_the_history_is_the_stream():
    profile = a_profile(proposals_opt_in_accepted=True)
    profile.answer_proposals_opt_in(
        accepted=False,
        copy_version="proposals-2026-09",
        surface=ConsentSurface.PROFILE,
        occurred_at=LATER,
    )
    events = profile.pull_events()

    rebuilt = PlayerProfile.from_history(events)

    assert rebuilt.proposals_opt_in is not None
    assert rebuilt.proposals_opt_in.accepted is False
    answers = [
        event for event in events if isinstance(event, ProposalsOptInAnswered)
    ]
    assert [answer.accepted for answer in answers] == [True, False], (
        "both answers survive — the change is appended, never applied over the "
        "top of the one it replaces"
    )


def test_reordering_the_same_photos_is_a_change():
    first, second = new_uuid(), new_uuid()
    profile = replayed(a_profile(photo_ids=[first, second]))

    profile.change_photos([second, first], occurred_at=LATER)

    assert [type(event) for event in profile.pull_events()] == [PhotosChanged]


def test_an_event_this_aggregate_does_not_know_is_refused_rather_than_ignored():
    """A stream folding an unknown event silently is a profile that is quietly
    wrong; this fails at the replay instead."""

    class SomethingElse:
        occurred_at = CREATED_AT

    with pytest.raises(TypeError):
        PlayerProfile.from_history([SomethingElse()])


def test_a_profile_cannot_be_created_without_an_opt_in_answer():
    """There is no path to the created state with the consent absent — the
    argument is required, and ``None`` is not a bool."""

    with pytest.raises(InvariantViolated):
        a_profile(proposals_opt_in_accepted=None)

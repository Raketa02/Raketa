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
from app.modules.player_profile.domain import search_radius, social_tags
from app.modules.player_profile.domain.consent import ConsentSurface
from app.modules.player_profile.domain.errors import (
    DuplicatePhoto,
    SearchRadiusOutOfBounds,
    SocialTagSelectionOutOfBounds,
    TooManyPhotos,
)
from app.modules.player_profile.domain.events import (
    AvailabilityChanged,
    GenderChanged,
    GenderPreferenceChanged,
    IntroWritten,
    LocationChanged,
    PhotosChanged,
    PlayerProfileCreated,
    ProposalsOptInAnswered,
    SearchRadiusChanged,
    SocialTagsChanged,
)
from app.modules.player_profile.domain.gender import (
    DEFAULT_GENDER_PREFERENCE,
    Gender,
    GenderPreference,
)
from app.modules.player_profile.domain.intro import Intro
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.profile import (
    MAX_PROFILE_PHOTOS,
    PlayerProfile,
)
from app.modules.player_profile.domain.search_radius import (
    SearchRadius,
    SearchRadiusBounds,
)
from app.modules.player_profile.domain.social_tags import (
    SocialTagSelection,
    SocialTagSelectionBounds,
)
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
        search_radius=SearchRadius.chosen(kilometres=10),
        gender=Gender.WOMAN,
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
        profile.gender,
        profile.gender_preference,
    )

    rebuilt = replayed(profile)

    assert (
        rebuilt.social_tags,
        rebuilt.availability,
        rebuilt.location,
        rebuilt.search_radius,
        rebuilt.proposals_opt_in,
        rebuilt.idempotency_key,
        rebuilt.gender,
        rebuilt.gender_preference,
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
    profile.change_search_radius(SearchRadius.chosen(kilometres=25), occurred_at=LATER)
    profile.change_gender(Gender.PREFER_NOT_TO_SAY, occurred_at=LATER)
    profile.change_gender_preference(GenderPreference.WOMEN_ONLY, occurred_at=LATER)

    assert [type(event) for event in profile.pull_events()] == [
        SocialTagsChanged,
        PhotosChanged,
        AvailabilityChanged,
        LocationChanged,
        SearchRadiusChanged,
        GenderChanged,
        GenderPreferenceChanged,
    ]


def test_a_preference_set_to_what_it_already_is_records_nothing():
    """So an idempotent client retry cannot grow a stream by an event that says
    the player did not do anything."""

    profile = replayed(a_profile())

    profile.change_social_tags(SocialTagSelection.from_ids(TAGS), occurred_at=LATER)
    profile.change_search_radius(SearchRadius.chosen(kilometres=10), occurred_at=LATER)
    profile.change_location(LocationArea.around(51.5074, -0.1278), occurred_at=LATER)
    profile.change_photos([], occurred_at=LATER)
    profile.change_gender(Gender.WOMAN, occurred_at=LATER)
    profile.change_gender_preference(DEFAULT_GENDER_PREFERENCE, occurred_at=LATER)

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
    answers = [event for event in events if isinstance(event, ProposalsOptInAnswered)]
    assert [answer.accepted for answer in answers] == [True, False], (
        "both answers survive — the change is appended, never applied over the "
        "top of the one it replaces"
    )


def test_reordering_the_same_photos_is_a_change():
    first, second = new_uuid(), new_uuid()
    profile = replayed(a_profile(photo_ids=[first, second]))

    profile.change_photos([second, first], occurred_at=LATER)

    assert [type(event) for event in profile.pull_events()] == [PhotosChanged]


def test_a_profile_still_replays_after_the_served_bounds_are_narrowed(monkeypatch):
    """**The write path refuses; the fold accepts.** The regression this exists
    for: replaying through the *checking* constructors meant that the day product
    lowered the tag ceiling or raised the minimum radius, every profile outside
    the new range stopped rehydrating — so `GET /users/me` would 400 for players
    who had done nothing, and the fourth branch of the entry gate ADR-0090
    depends on would fail for exactly them.

    The bounds are documented as editable (*"a later opinion is an edit here"*),
    which is what makes this reachable rather than theoretical.
    """

    committed = a_profile(
        social_tags=SocialTagSelection.from_ids(
            ["PLAYS_TO_WIN", "HERE_TO_IMPROVE", "QUIET_AND_FOCUSED"]
        ),
        search_radius=SearchRadius.chosen(kilometres=40),
    )
    stream = committed.pull_events()

    # Product changes its mind: at most two tags, and never further than 20km.
    monkeypatch.setattr(
        social_tags,
        "SOCIAL_TAG_SELECTION_BOUNDS",
        SocialTagSelectionBounds(minimum_tags=1, maximum_tags=2),
    )
    monkeypatch.setattr(
        search_radius,
        "SEARCH_RADIUS_BOUNDS",
        SearchRadiusBounds(minimum_km=1, maximum_km=20, step_km=1, default_km=10),
    )

    rebuilt = PlayerProfile.from_history(stream)

    assert len(rebuilt.social_tags) == 3, "the three tags they actually picked"
    assert rebuilt.search_radius.kilometres == 40
    # And the write path has moved with the bounds, which is the other half.
    with pytest.raises(SocialTagSelectionOutOfBounds):
        SocialTagSelection.from_ids(
            ["PLAYS_TO_WIN", "HERE_TO_IMPROVE", "QUIET_AND_FOCUSED"]
        )
    with pytest.raises(SearchRadiusOutOfBounds):
        SearchRadius.chosen(kilometres=40)


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


# ---------------------------------------------------------------------------
# Gender, and the two things its absence must never be confused with
# ---------------------------------------------------------------------------


def test_the_creating_event_carries_the_gender_answer_and_the_preference():
    """Both are on the *creating* event and neither gets a commit of its own:
    gender is required at profile creation (``docs/adr/0096``), and profile
    creation is one request."""

    profile = a_profile(gender=Gender.MAN, gender_preference=GenderPreference.MEN_ONLY)

    created, _consent = profile.pull_events()

    assert created.gender == "MAN"
    assert created.gender_preference == "MEN_ONLY"


def test_a_profile_that_names_no_preference_is_created_holding_any():
    """The asymmetry ADR-0096 draws: the answer about oneself is required, the
    preference over others is optional and *no constraint* is what its absence
    already means."""

    profile = a_profile()

    assert profile.gender_preference is DEFAULT_GENDER_PREFERENCE
    assert profile.pull_events()[0].gender_preference == "ANY"


def test_prefer_not_to_say_is_an_answer_and_is_recorded_as_one():
    """It is not a null and not a skip. A player who chooses it has answered,
    and the event says so in the same field every other answer uses."""

    profile = a_profile(gender=Gender.PREFER_NOT_TO_SAY)

    assert profile.pull_events()[0].gender == "PREFER_NOT_TO_SAY"


def test_a_profile_committed_before_the_question_existed_holds_no_gender():
    """The fold must keep absence absent.

    This is the stream of a profile created before ADR-0096 — the creating event
    exactly as it was written, with the two fields that did not exist then still
    unset. Folding that into ``PREFER_NOT_TO_SAY`` would have the profile claim
    an answer nobody gave, and a gate downstream would then read a fabricated
    self-declaration as a real one.
    """

    before_the_question_existed = PlayerProfileCreated(
        player_id=PLAYER,
        social_tags=TAGS,
        photo_ids=(),
        availability=("2:EVENING",),
        latitude=51.51,
        longitude=-0.13,
        search_radius_km=10,
        idempotency_key="commit-1",
        occurred_at=CREATED_AT,
    )

    profile = PlayerProfile.from_history([before_the_question_existed])

    assert profile.gender is None
    # The preference is not the same case: optional, and `ANY` is what never
    # having expressed one *is*.
    assert profile.gender_preference is GenderPreference.ANY


def test_answering_for_the_first_time_on_an_older_profile_is_a_change():
    """Which is what makes ADR-0096's *existing players are asked on next open*
    reachable at all: there is no value to be equal to, so the no-op rule does
    not swallow the first answer."""

    profile = PlayerProfile.from_history(
        [
            PlayerProfileCreated(
                player_id=PLAYER,
                social_tags=TAGS,
                photo_ids=(),
                availability=("2:EVENING",),
                latitude=51.51,
                longitude=-0.13,
                search_radius_km=10,
                idempotency_key="commit-1",
                occurred_at=CREATED_AT,
            )
        ]
    )

    profile.change_gender(Gender.WOMAN, occurred_at=LATER)

    assert [type(event) for event in profile.pull_events()] == [GenderChanged]
    assert profile.gender is Gender.WOMAN


def test_gender_and_the_preference_replay_from_their_own_events():
    """*Self-declared, freely changed* is a property of the stream, not of a
    setter: the latest event of each kind is the state."""

    profile = replayed(a_profile(gender=Gender.WOMAN))
    profile.change_gender(Gender.MAN, occurred_at=LATER)
    profile.change_gender_preference(GenderPreference.MEN_ONLY, occurred_at=LATER)

    rebuilt = PlayerProfile.from_history(
        a_profile(gender=Gender.WOMAN).pull_events() + profile.pull_events()
    )

    assert rebuilt.gender is Gender.MAN
    assert rebuilt.gender_preference is GenderPreference.MEN_ONLY


# ---------------------------------------------------------------------------
# The intro (docs/adr/0170)
# ---------------------------------------------------------------------------


def test_a_line_present_at_the_commit_is_its_own_event_after_the_two():
    """``IntroWritten`` is emitted by the commit when the line is present —
    after the creation and the consent, so *no special first case* for the
    consent history stays literally true."""

    profile = a_profile(intro=Intro.written("Moved from Wrocław in May."))

    recorded = profile.pull_events()

    assert [type(event) for event in recorded] == [
        PlayerProfileCreated,
        ProposalsOptInAnswered,
        IntroWritten,
    ]
    written = recorded[2]
    assert isinstance(written, IntroWritten)
    assert written.intro == "Moved from Wrocław in May."
    assert written.player_id == PLAYER
    assert written.occurred_at == CREATED_AT
    assert profile.intro == Intro.recorded("Moved from Wrocław in May.")


def test_a_skipped_intro_leaves_nothing_behind():
    """A blank leaves nothing behind — the shape sportsmanship already takes.
    ``PlayerProfileCreated`` does not grow a field for it."""

    profile = a_profile()

    recorded = profile.pull_events()

    assert [type(event) for event in recorded] == [
        PlayerProfileCreated,
        ProposalsOptInAnswered,
    ]
    assert not hasattr(recorded[0], "intro")
    assert profile.intro is None


def test_an_intro_replays_from_its_own_event():
    profile = a_profile(intro=Intro.written("Will travel for a hard game."))

    rebuilt = replayed(profile)

    assert rebuilt.intro == Intro.recorded("Will travel for a hard game.")
    assert rebuilt.version == 3, "three events, three versions"


def test_a_stream_with_no_intro_written_folds_to_no_intro():
    """No upcaster: a profile committed before the question existed replays
    with the intro absent, which is what those players have."""

    rebuilt = replayed(a_profile())

    assert rebuilt.intro is None

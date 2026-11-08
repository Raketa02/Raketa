"""The use cases behind the profile surface reads and writes.

One read and, since ``docs/adr/0179`` §8, seven writes: the week and the
location the Play screens and the cold start were already writing, and the five
the You tab writes — the tags, the photos, the intro, the gender and the
preference. The radius and the opt-in answered again from ``PROFILE`` went with
the ranking that read them (#581).

The **event store** is faked and both repositories are real, for the reason every
use-case test in this suite works that way: a repository fake would leave the
aggregate-type strings, the version arithmetic and the two derived stream ids
exercised by nothing, and those are what the repositories introduced.

What is asserted here is what HTTP cannot see — **which events a write released**,
**that a write that changed nothing released none**, and **that the read asks each
of the two aggregates the question it owns**.
"""

from __future__ import annotations

import pytest

from app.engines.matchfit.core import ReliabilityBand
from app.kernel import Sport
from app.modules.player_profile.application.change_gender import ChangeGender
from app.modules.player_profile.application.change_gender_preference import (
    ChangeGenderPreference,
)
from app.modules.player_profile.application.change_intro import ChangeIntro
from app.modules.player_profile.application.change_location import ChangeLocation
from app.modules.player_profile.application.change_photos import ChangePhotos
from app.modules.player_profile.application.change_social_tags import (
    ChangeSocialTags,
)
from app.modules.player_profile.application.commands import (
    SetWeeklyHoursCommand,
    ChangeGenderCommand,
    ChangeGenderPreferenceCommand,
    ChangeIntroCommand,
    ChangeLocationCommand,
    ChangePhotosCommand,
    ChangeSocialTagsCommand,
    CommitPlayerProfileCommand,
    DeclarePlayIntentCommand,
    PhoneReading,
    SetRankingVisibilityCommand,
    SetReliabilityMinimumCommand,
)
from app.modules.player_profile.application.commit_player_profile import (
    CommitPlayerProfile,
)
from app.modules.player_profile.application.declare_play_intent import (
    DeclarePlayIntent,
)
from app.modules.player_profile.application.read_player_profile import (
    ReadPlayerProfile,
)
from app.modules.player_profile.application.set_ranking_visibility import (
    SetRankingVisibility,
)
from app.modules.player_profile.application.set_reliability_minimum import (
    SetReliabilityMinimum,
)
from app.modules.player_profile.application.set_weekly_hours import SetWeeklyHours
from app.modules.player_profile.domain.errors import (
    IntroNotAdmitted,
    IntroRefusal,
    PhotoNotFound,
    PlayerProfileNotFound,
    ReliabilityMinimumNotOffered,
    SocialTagSelectionOutOfBounds,
    TooManyPhotos,
    UnknownSocialTag,
)
from app.modules.player_profile.domain.events import (
    GenderChanged,
    GenderPreferenceChanged,
    IntroChanged,
    LocationChanged,
    PhotosChanged,
    PlayerProfileCreated,
    PlayIntentDeclared,
    RankingVisibilitySet,
    ReliabilityMinimumSet,
    SocialTagsChanged,
    WeeklyHoursSet,
)
from app.modules.player_profile.domain.gender import (
    DEFAULT_GENDER_PREFERENCE,
    Gender,
    GenderPreference,
)
from app.modules.player_profile.domain.intro import Intro
from app.modules.player_profile.domain.photos import (
    PhotoRef,
    PhotoReviewDecision,
    PhotoReviewUnavailability,
    review_metadata,
    verdict_from_similarities,
    verdict_when_unreviewable,
)
from app.modules.player_profile.domain.play_intent import (
    PlayIntent,
    PlayIntentSurface,
)
from app.modules.player_profile.domain.profile import MAX_PROFILE_PHOTOS
from app.modules.player_profile.domain.ranking_visibility import RankingVisibility
from app.modules.player_profile.infrastructure.event_sourced_play_intent_declaration_repository import (  # noqa: E501
    EventSourcedPlayIntentDeclarationRepository,
)
from app.modules.player_profile.infrastructure.event_sourced_player_profile_repository import (  # noqa: E501
    PLAYER_PROFILE_AGGREGATE,
    EventSourcedPlayerProfileRepository,
)
from app.modules.player_profile.presentation.schemas import PlayerProfileReadResponse
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import (
    CountingUnitOfWork,
    FrozenClock,
    InMemoryEventStore,
    RecordingPublisher,
)
from tests.unit.fake_club_points import InMemoryClubPoints
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

PLAYER = new_uuid()
STRANGER = new_uuid()

#: The fix every profile here is committed with. It rounds to (51.51, -0.13).
HOME_FIX = (51.5073509, -0.1277583)


class Harness:
    """The use cases over fakes, each built the way a request builds one."""

    def __init__(self) -> None:
        self.store = InMemoryEventStore()
        self.publisher = RecordingPublisher()
        self.uow = CountingUnitOfWork()
        self.clock = FrozenClock()
        #: One store for the commit and the read: the commit proves each photo
        #: id against it, and the read asks it what was concluded about each.
        self.photos = InMemoryPhotoStorage()
        #: No club is placed: every profile here commits and moves by a reading.
        self.clubs = InMemoryClubPoints()

    # A repository per call, as the request scope makes one: each remembers the
    # stream versions *it* read, and one that outlived its transaction would be
    # answering another request's question about a version.
    def _profiles(self) -> EventSourcedPlayerProfileRepository:
        return EventSourcedPlayerProfileRepository(
            event_store=self.store, events=self.publisher
        )

    def _declarations(self) -> EventSourcedPlayIntentDeclarationRepository:
        return EventSourcedPlayIntentDeclarationRepository(
            event_store=self.store, events=self.publisher
        )

    async def commit_profile(self, *, player_id=PLAYER, **overrides):
        """A profile, through the commit — the only way one legitimately exists."""

        arguments = dict(
            player_id=player_id,
            idempotency_key=f"commit-{player_id}",
            social_tag_ids=["PLAYS_TO_WIN", "HERE_TO_IMPROVE"],
            photo_ids=[],
            weekly_hours=[(2, 19), (6, 10)],
            location=PhoneReading(latitude=HOME_FIX[0], longitude=HOME_FIX[1]),
            gender=Gender.WOMAN,
            gender_preference=DEFAULT_GENDER_PREFERENCE,
        )
        arguments.update(overrides)
        await CommitPlayerProfile(
            profiles=self._profiles(),
            photos=self.photos,
            clubs=self.clubs,
            uow=self.uow,
            clock=self.clock,
        ).execute(CommitPlayerProfileCommand(**arguments))
        self.forget_what_the_commit_released()

    def forget_what_the_commit_released(self) -> None:
        """The arrangement is not the act. What a test asserts on is the write."""

        self.publisher.published.clear()
        self.uow.commits = 0
        self.store.appends = 0

    async def set_weekly_hours(self, cells, *, player_id=PLAYER):
        return await SetWeeklyHours(
            profiles=self._profiles(), uow=self.uow, clock=self.clock
        ).execute(SetWeeklyHoursCommand(player_id=player_id, weekly_hours=cells))

    async def change_location(
        self, latitude: float, longitude: float, *, player_id=PLAYER
    ) -> None:
        await ChangeLocation(
            profiles=self._profiles(), clubs=self.clubs, uow=self.uow, clock=self.clock
        ).execute(
            ChangeLocationCommand(
                player_id=player_id,
                location=PhoneReading(latitude=latitude, longitude=longitude),
            )
        )

    async def change_social_tags(self, ids, *, player_id=PLAYER):
        return await ChangeSocialTags(
            profiles=self._profiles(), uow=self.uow, clock=self.clock
        ).execute(ChangeSocialTagsCommand(player_id=player_id, social_tag_ids=ids))

    async def change_photos(self, photo_ids, *, player_id=PLAYER):
        return await ChangePhotos(
            profiles=self._profiles(),
            photos=self.photos,
            uow=self.uow,
            clock=self.clock,
        ).execute(ChangePhotosCommand(player_id=player_id, photo_ids=photo_ids))

    async def change_intro(self, intro: str | None, *, player_id=PLAYER) -> None:
        await ChangeIntro(
            profiles=self._profiles(), uow=self.uow, clock=self.clock
        ).execute(ChangeIntroCommand(player_id=player_id, intro=intro))

    async def change_gender(self, gender: Gender, *, player_id=PLAYER) -> None:
        await ChangeGender(
            profiles=self._profiles(), uow=self.uow, clock=self.clock
        ).execute(ChangeGenderCommand(player_id=player_id, gender=gender))

    async def change_gender_preference(
        self, preference: GenderPreference, *, player_id=PLAYER
    ) -> None:
        await ChangeGenderPreference(
            profiles=self._profiles(), uow=self.uow, clock=self.clock
        ).execute(
            ChangeGenderPreferenceCommand(
                player_id=player_id, gender_preference=preference
            )
        )

    async def set_reliability_minimum(
        self, minimum: ReliabilityBand | None, *, player_id=PLAYER
    ) -> None:
        await SetReliabilityMinimum(
            profiles=self._profiles(), uow=self.uow, clock=self.clock
        ).execute(SetReliabilityMinimumCommand(player_id=player_id, minimum=minimum))

    async def set_ranking_visibility(
        self, visibility: RankingVisibility, *, player_id=PLAYER
    ) -> None:
        await SetRankingVisibility(
            profiles=self._profiles(), uow=self.uow, clock=self.clock
        ).execute(
            SetRankingVisibilityCommand(player_id=player_id, visibility=visibility)
        )

    async def declare(
        self,
        intent: PlayIntent,
        *,
        player_id=PLAYER,
        sport: Sport = Sport.PADEL,
        surface: PlayIntentSurface = PlayIntentSurface.RATING_TAIL,
    ):
        return await DeclarePlayIntent(
            declarations=self._declarations(), uow=self.uow, clock=self.clock
        ).execute(
            DeclarePlayIntentCommand(
                player_id=player_id, sport=sport, intent=intent, surface=surface
            )
        )

    async def read(self, *, player_id=PLAYER):
        return await ReadPlayerProfile(
            profiles=self._profiles(),
            declarations=self._declarations(),
            photos=self.photos,
        ).execute(player_id)

    def a_photo_held(self, *, metadata: dict[str, str], owner=PLAYER):
        """One photograph already in the store, carrying what a verdict writes."""

        photo_id = new_uuid()
        self.photos.already_holding(
            PhotoRef(owner_id=owner, photo_id=photo_id), metadata
        )
        return photo_id


@pytest.fixture
def harness() -> Harness:
    return Harness()


# ---------------------------------------------------------------------------
# The week
# ---------------------------------------------------------------------------


async def test_clearing_the_week_records_a_change_rather_than_being_refused(harness):
    """The floor's named exit, exercised from the layer that reaches it.

    ``WeeklyHours.edited`` is what this write builds through, so a player
    who unticks everything appends a ``WeeklyHoursSet`` carrying nothing —
    which is a fact recorded, not a value missing.
    """

    await harness.commit_profile()

    profile = await harness.set_weekly_hours([])

    assert len(profile.weekly_hours) == 0
    (released,) = harness.publisher.published
    assert isinstance(released, WeeklyHoursSet)
    assert released.weekly_hours == ()
    assert harness.uow.commits == 1


async def test_the_same_week_twice_appends_once(harness):
    """The aggregate's *a transition that changes nothing records nothing* rule,
    which is what makes the unkeyed `PUT` safe to send twice."""

    await harness.commit_profile()
    week = [(4, 15)]

    await harness.set_weekly_hours(week)
    harness.publisher.published.clear()
    profile = await harness.set_weekly_hours(week)

    assert harness.publisher.published == []
    assert profile.weekly_hours.codes == ("4:15",)
    # Still committed: the transaction boundary belongs to the command, not to
    # whether the command found anything to record.
    assert harness.uow.commits == 2


async def test_a_week_written_by_a_player_with_no_profile_is_refused(harness):
    with pytest.raises(PlayerProfileNotFound):
        await harness.set_weekly_hours([(1, 10)])

    assert harness.publisher.published == []
    assert harness.uow.commits == 0


# ---------------------------------------------------------------------------
# The location
# ---------------------------------------------------------------------------


async def test_a_fix_in_a_new_cell_records_the_cell_and_never_the_fix(harness):
    """``docs/adr/0174`` §6: the cold start's write. The aggregate's
    ``change_location`` has existed since ADR-0089 with no caller in ``app/``;
    this is its first. What crosses into the stream is the **cell** the fix rounds to —
    the location value object's own rule, applied here exactly as the commit
    applies it — so the device's reading is nowhere a replay could recover it."""

    await harness.commit_profile()

    await harness.change_location(52.2297, 21.0122)

    (released,) = harness.publisher.published
    assert isinstance(released, LocationChanged)
    assert (released.latitude, released.longitude) == (52.23, 21.01)
    assert harness.uow.commits == 1


async def test_a_fix_rounding_to_the_stored_cell_records_nothing(harness):
    """The time after that: the phone reads a slightly different fix in the same
    cell, and the aggregate's no-op rule means nothing is appended. Still
    committed, for the week's reason — the transaction boundary is the
    command's, not the change's."""

    await harness.commit_profile()

    await harness.change_location(51.5099, -0.1310)

    assert harness.publisher.published == []
    assert harness.store.appends == 0
    assert harness.uow.commits == 1


async def test_a_location_written_by_a_player_with_no_profile_is_refused(harness):
    with pytest.raises(PlayerProfileNotFound):
        await harness.change_location(52.2297, 21.0122)

    assert harness.publisher.published == []
    assert harness.uow.commits == 0


# ---------------------------------------------------------------------------
# The tags (docs/adr/0179 §6, §8)
# ---------------------------------------------------------------------------


async def test_the_tags_are_replaced_whole_and_re_validated_as_the_commit_validates(
    harness,
):
    """Re-validated against the served vocabulary and bounds exactly as the
    commit re-validates — ``SocialTagSelection.from_ids`` is what both build
    through — and released as one ``SocialTagsChanged`` carrying the selection
    in the vocabulary's order, whatever order the picker sent it in."""

    await harness.commit_profile()

    profile = await harness.change_social_tags(["HERE_TO_COMPETE", "QUIET_AND_FOCUSED"])

    (released,) = harness.publisher.published
    assert isinstance(released, SocialTagsChanged)
    assert set(released.social_tags) == {"QUIET_AND_FOCUSED", "HERE_TO_COMPETE"}
    assert profile.social_tags.ids == released.social_tags
    assert harness.uow.commits == 1


async def test_the_same_selection_twice_appends_nothing(harness):
    await harness.commit_profile()

    profile = await harness.change_social_tags(["HERE_TO_IMPROVE", "PLAYS_TO_WIN"])

    assert harness.publisher.published == []
    assert harness.store.appends == 0
    assert set(profile.social_tags.ids) == {"PLAYS_TO_WIN", "HERE_TO_IMPROVE"}
    assert harness.uow.commits == 1


async def test_an_unserved_tag_and_an_out_of_bounds_count_are_refused_before_the_store(
    harness,
):
    """The refusal is pure and the replay is not, so the check comes first —
    a player with no profile still gets the tag's own code."""

    with pytest.raises(UnknownSocialTag):
        await harness.change_social_tags(["PLAYS_TO_WIN", "NOT_A_TAG"])
    with pytest.raises(SocialTagSelectionOutOfBounds):
        await harness.change_social_tags([])

    assert harness.store.appends == 0
    assert harness.uow.commits == 0


async def test_tags_written_by_a_player_with_no_profile_are_refused(harness):
    with pytest.raises(PlayerProfileNotFound):
        await harness.change_social_tags(["PLAYS_TO_WIN", "HERE_TO_IMPROVE"])

    assert harness.uow.commits == 0


# ---------------------------------------------------------------------------
# The photos (docs/adr/0179 §6, §8)
# ---------------------------------------------------------------------------


async def test_the_photos_are_replaced_in_the_order_sent(harness):
    """Order is meaning — the first is the one a card shows — so promoting the
    second photograph is a change even though the set is the same, and the
    event carries the whole list in its new order."""

    first = harness.a_photo_held(metadata={})
    second = harness.a_photo_held(metadata={})
    await harness.commit_profile(photo_ids=[first, second])

    profile = await harness.change_photos([second, first])

    (released,) = harness.publisher.published
    assert isinstance(released, PhotosChanged)
    assert released.photo_ids == (str(second), str(first))
    assert profile.photo_ids == (second, first)
    assert harness.uow.commits == 1


async def test_an_empty_list_clears_the_photographs(harness):
    """A profile may hold none, and the poster returns. Recorded as a change
    carrying nothing — a fact recorded, not a value missing."""

    photo = harness.a_photo_held(metadata={})
    await harness.commit_profile(photo_ids=[photo])

    profile = await harness.change_photos([])

    (released,) = harness.publisher.published
    assert isinstance(released, PhotosChanged)
    assert released.photo_ids == ()
    assert profile.photo_ids == ()


async def test_the_same_order_twice_appends_nothing(harness):
    photo = harness.a_photo_held(metadata={})
    await harness.commit_profile(photo_ids=[photo])

    await harness.change_photos([photo])

    assert harness.publisher.published == []
    assert harness.store.appends == 0
    assert harness.uow.commits == 1


async def test_a_photograph_that_is_not_the_callers_is_refused(harness):
    """The commit's check, through the same port and the same ``PhotoRef``:
    another player's photo id answers exactly as an imaginary one does, and
    nothing is recorded."""

    await harness.commit_profile()
    theirs = harness.a_photo_held(metadata={}, owner=STRANGER)

    with pytest.raises(PhotoNotFound):
        await harness.change_photos([theirs])
    with pytest.raises(PhotoNotFound):
        await harness.change_photos([new_uuid()])

    assert harness.publisher.published == []
    assert harness.store.appends == 0


async def test_too_many_photographs_are_refused_before_the_store_is_asked(harness):
    await harness.commit_profile()
    checks_before = len(harness.photos.existence_checks)

    with pytest.raises(TooManyPhotos):
        await harness.change_photos([new_uuid() for _ in range(MAX_PROFILE_PHOTOS + 1)])

    assert harness.store.appends == 0
    assert harness.uow.commits == 0
    assert len(harness.photos.existence_checks) == checks_before


async def test_photos_written_by_a_player_with_no_profile_are_refused(harness):
    with pytest.raises(PlayerProfileNotFound):
        await harness.change_photos([])

    assert harness.uow.commits == 0


# ---------------------------------------------------------------------------
# The intro (docs/adr/0179 §6)
# ---------------------------------------------------------------------------


async def test_the_line_is_replaced_and_trimmed_as_the_commit_trims(harness):
    await harness.commit_profile(intro="Moved from Wrocław in May.")

    await harness.change_intro("  Will travel for a hard game.  ")

    (released,) = harness.publisher.published
    assert isinstance(released, IntroChanged)
    assert released.intro == "Will travel for a hard game."
    read = await harness.read()
    assert read.profile.intro == Intro.recorded("Will travel for a hard game.")
    assert harness.uow.commits == 1


async def test_none_withdraws_the_line_and_the_profile_folds_to_none(harness):
    await harness.commit_profile(intro="Moved from Wrocław in May.")

    await harness.change_intro(None)

    (released,) = harness.publisher.published
    assert isinstance(released, IntroChanged)
    assert released.intro is None
    assert (await harness.read()).profile.intro is None


async def test_a_blank_line_is_the_withdrawal_too(harness):
    """Whitespace is what it is at the commit — *no line* — and here that is
    a withdrawal rather than a skip."""

    await harness.commit_profile(intro="Moved from Wrocław in May.")

    await harness.change_intro("   ")

    (released,) = harness.publisher.published
    assert isinstance(released, IntroChanged) and released.intro is None
    assert (await harness.read()).profile.intro is None


async def test_the_same_line_twice_appends_nothing(harness):
    await harness.commit_profile(intro="Moved from Wrocław in May.")

    await harness.change_intro("Moved from Wrocław in May.")

    assert harness.publisher.published == []
    assert harness.store.appends == 0
    assert harness.uow.commits == 1


async def test_a_line_carrying_contact_is_refused_before_the_store_is_asked(
    harness,
):
    """The commit's fence, with the commit's reason — and first, so a player
    with no profile still gets ``intro_not_admitted`` rather than
    ``player_profile_not_found``, which is the assertion that the check really
    does come before the replay."""

    with pytest.raises(IntroNotAdmitted) as refused:
        await harness.change_intro("WhatsApp me on 600 123 456")

    assert refused.value.reason is IntroRefusal.CONTAINS_CONTACT
    assert harness.store.appends == 0
    assert harness.uow.commits == 0


async def test_an_intro_written_by_a_player_with_no_profile_is_refused(harness):
    with pytest.raises(PlayerProfileNotFound):
        await harness.change_intro("Late to the game.")

    assert harness.uow.commits == 0


# ---------------------------------------------------------------------------
# The gender and the preference (docs/adr/0096, docs/adr/0179 §8)
# ---------------------------------------------------------------------------


async def test_a_corrected_gender_is_its_own_event(harness):
    await harness.commit_profile(gender=Gender.WOMAN)

    await harness.change_gender(Gender.PREFER_NOT_TO_SAY)

    (released,) = harness.publisher.published
    assert isinstance(released, GenderChanged)
    assert released.gender == "PREFER_NOT_TO_SAY"
    assert harness.uow.commits == 1


async def test_the_same_gender_twice_appends_nothing(harness):
    await harness.commit_profile(gender=Gender.WOMAN)

    await harness.change_gender(Gender.WOMAN)

    assert harness.publisher.published == []
    assert harness.store.appends == 0
    assert harness.uow.commits == 1


async def test_a_first_answer_on_a_pre_question_profile_is_a_change(harness):
    """ADR-0096's *existing players are asked on next open*, reachable from
    this route: a stream from before the question folds to no gender, so there
    is nothing for the first answer to be equal to."""

    await harness.store.append(
        aggregate_type=PLAYER_PROFILE_AGGREGATE,
        aggregate_id=PLAYER,
        expected_version=0,
        events=[
            PlayerProfileCreated(
                player_id=PLAYER,
                social_tags=("PLAYS_TO_WIN", "HERE_TO_IMPROVE"),
                photo_ids=(),
                weekly_hours=("2:19",),
                latitude=51.51,
                longitude=-0.13,
                idempotency_key="commit-before-the-question",
                occurred_at=harness.clock.now(),
            ),
        ],
    )

    await harness.change_gender(Gender.MAN)

    (released,) = harness.publisher.published
    assert isinstance(released, GenderChanged) and released.gender == "MAN"
    assert (await harness.read()).profile.gender is Gender.MAN


async def test_a_narrowed_preference_is_its_own_event(harness):
    await harness.commit_profile()

    await harness.change_gender_preference(GenderPreference.WOMEN_ONLY)

    (released,) = harness.publisher.published
    assert isinstance(released, GenderPreferenceChanged)
    assert released.gender_preference == "WOMEN_ONLY"
    read = await harness.read()
    assert read.profile.gender_preference is GenderPreference.WOMEN_ONLY


async def test_the_same_preference_twice_appends_nothing(harness):
    await harness.commit_profile()

    await harness.change_gender_preference(DEFAULT_GENDER_PREFERENCE)

    assert harness.publisher.published == []
    assert harness.store.appends == 0
    assert harness.uow.commits == 1


async def test_a_gender_or_a_preference_written_without_a_profile_is_refused(
    harness,
):
    with pytest.raises(PlayerProfileNotFound):
        await harness.change_gender(Gender.MAN)
    with pytest.raises(PlayerProfileNotFound):
        await harness.change_gender_preference(GenderPreference.MEN_ONLY)

    assert harness.uow.commits == 0


# ---------------------------------------------------------------------------
# The reliability filter (#661)
# ---------------------------------------------------------------------------


async def test_a_profile_starts_with_the_filter_off(harness):
    await harness.commit_profile()

    assert (await harness.read()).profile.reliability_minimum is None


async def test_switching_the_filter_on_is_its_own_event(harness):
    """*Play only with players of at least High reliability* — a durable
    answer to *who am I willing to play with*, beside the gender preference
    (``docs/adr/0195`` §6)."""

    await harness.commit_profile()

    await harness.set_reliability_minimum(ReliabilityBand.HIGH)

    (released,) = harness.publisher.published
    assert isinstance(released, ReliabilityMinimumSet)
    assert released.minimum == "HIGH"
    assert (await harness.read()).profile.reliability_minimum is ReliabilityBand.HIGH


async def test_switching_it_off_again_is_recorded_as_none(harness):
    await harness.commit_profile()
    await harness.set_reliability_minimum(ReliabilityBand.MEDIUM)
    harness.forget_what_the_commit_released()

    await harness.set_reliability_minimum(None)

    (released,) = harness.publisher.published
    assert isinstance(released, ReliabilityMinimumSet) and released.minimum is None
    assert (await harness.read()).profile.reliability_minimum is None


async def test_the_same_filter_twice_appends_nothing(harness):
    await harness.commit_profile()
    await harness.set_reliability_minimum(ReliabilityBand.HIGH)
    harness.forget_what_the_commit_released()

    await harness.set_reliability_minimum(ReliabilityBand.HIGH)
    await harness.set_reliability_minimum(None)
    await harness.set_reliability_minimum(None)

    assert [type(event) for event in harness.publisher.published] == [
        ReliabilityMinimumSet
    ]


@pytest.mark.parametrize("band", [ReliabilityBand.VERY_HIGH, ReliabilityBand.LOW])
async def test_a_minimum_the_switch_does_not_offer_is_refused_before_the_store(
    harness, band
):
    """*At least Medium* or *at least High*, and nothing else: *at least Low*
    is no filter, and *at least Very high* is not a choice the product makes."""

    await harness.commit_profile()

    with pytest.raises(ReliabilityMinimumNotOffered):
        await harness.set_reliability_minimum(band)

    assert harness.store.appends == 0
    assert harness.uow.commits == 0


async def test_a_filter_written_without_a_profile_is_refused(harness):
    with pytest.raises(PlayerProfileNotFound):
        await harness.set_reliability_minimum(ReliabilityBand.HIGH)

    assert harness.uow.commits == 0


# ---------------------------------------------------------------------------
# Show me in General (#772)
# ---------------------------------------------------------------------------


async def test_a_profile_starts_shown_in_general(harness):
    await harness.commit_profile()

    assert (await harness.read()).profile.ranking_visibility is RankingVisibility.SHOWN


async def test_hiding_from_general_is_its_own_event_and_showing_again_another(
    harness,
):
    """*Show me in General* off, then on — each a new event on the profile's
    stream (``docs/adr/0203`` §7), carrying the whole new value."""

    await harness.commit_profile()
    harness.forget_what_the_commit_released()

    await harness.set_ranking_visibility(RankingVisibility.HIDDEN)
    hidden = (await harness.read()).profile.ranking_visibility
    await harness.set_ranking_visibility(RankingVisibility.SHOWN)

    first, second = harness.publisher.published
    assert isinstance(first, RankingVisibilitySet) and first.visibility == "HIDDEN"
    assert isinstance(second, RankingVisibilitySet) and second.visibility == "SHOWN"
    assert first.player_id == PLAYER
    assert hidden is RankingVisibility.HIDDEN
    assert (await harness.read()).profile.ranking_visibility is RankingVisibility.SHOWN


async def test_the_same_visibility_twice_appends_nothing(harness):
    await harness.commit_profile()
    harness.forget_what_the_commit_released()

    await harness.set_ranking_visibility(RankingVisibility.SHOWN)
    await harness.set_ranking_visibility(RankingVisibility.HIDDEN)
    await harness.set_ranking_visibility(RankingVisibility.HIDDEN)

    assert [type(event) for event in harness.publisher.published] == [
        RankingVisibilitySet
    ]


async def test_a_visibility_written_without_a_profile_is_refused(harness):
    with pytest.raises(PlayerProfileNotFound):
        await harness.set_ranking_visibility(RankingVisibility.HIDDEN)

    assert harness.uow.commits == 0


# ---------------------------------------------------------------------------
# The declaration
# ---------------------------------------------------------------------------


async def test_a_first_declaration_opens_the_stream(harness):
    declaration = await harness.declare(PlayIntent.COMPETITIVE)

    (released,) = harness.publisher.published
    assert isinstance(released, PlayIntentDeclared)
    assert released.intent == "COMPETITIVE"
    assert released.surface == "RATING_TAIL"
    assert declaration.version == 1
    assert harness.uow.commits == 1


async def test_a_change_of_mind_appends_to_the_same_stream(harness):
    await harness.declare(PlayIntent.COMPETITIVE)
    harness.publisher.published.clear()

    declaration = await harness.declare(
        PlayIntent.FOR_FUN, surface=PlayIntentSurface.SEARCH_SWITCH
    )

    (released,) = harness.publisher.published
    assert isinstance(released, PlayIntentDeclared)
    assert released.intent == "FOR_FUN"
    assert declaration.version == 2


async def test_the_same_answer_from_a_different_screen_records_nothing(harness):
    """Intent is a preference: *where they were standing* is not a new fact
    about what kind of game they want."""

    await harness.declare(PlayIntent.COMPETITIVE)
    harness.publisher.published.clear()

    declaration = await harness.declare(
        PlayIntent.COMPETITIVE, surface=PlayIntentSurface.SEARCH_SWITCH
    )

    assert harness.publisher.published == []
    assert declaration.version == 1
    assert declaration.surface is PlayIntentSurface.RATING_TAIL


async def test_two_sports_are_two_streams(harness):
    """*Levels never transfer between sports, and intent does not either* — held
    structurally, because no object holds two sports' intent at once."""

    await harness.declare(PlayIntent.COMPETITIVE, sport=Sport.PADEL)
    tennis = await harness.declare(PlayIntent.FOR_FUN, sport=Sport.TENNIS)

    assert tennis.version == 1
    assert tennis.intent is PlayIntent.FOR_FUN


async def test_a_declaration_needs_no_profile(harness):
    """The rating tail comes before onboarding's second part, so the ordinary
    first declaration is made by a player who has no profile yet."""

    declaration = await harness.declare(PlayIntent.NO_PREFERENCE)

    assert declaration.intent is PlayIntent.NO_PREFERENCE


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------


async def test_the_read_joins_the_profile_and_the_sports_declared_in(harness):
    await harness.commit_profile()
    await harness.declare(PlayIntent.COMPETITIVE, sport=Sport.PADEL)
    await harness.declare(PlayIntent.FOR_FUN, sport=Sport.SQUASH)

    surface = await harness.read()

    assert surface.profile.player_id == PLAYER
    assert surface.play_intents == {
        Sport.PADEL: PlayIntent.COMPETITIVE,
        Sport.SQUASH: PlayIntent.FOR_FUN,
    }


async def test_an_undeclared_sport_is_absent_from_the_map(harness):
    """Absence is the encoding of *undeclared*. There is no key with a null
    behind it, because ADR-0094 leaves no unanswered value to put there."""

    await harness.commit_profile()
    await harness.declare(PlayIntent.COMPETITIVE, sport=Sport.PADEL)

    surface = await harness.read()

    assert set(surface.play_intents) == {Sport.PADEL}
    assert all(intent is not None for intent in surface.play_intents.values())


async def test_the_read_is_one_players_own(harness):
    await harness.commit_profile()
    await harness.commit_profile(player_id=STRANGER)
    await harness.declare(PlayIntent.COMPETITIVE, player_id=STRANGER)

    surface = await harness.read()

    assert surface.play_intents == {}


async def test_the_read_refuses_a_player_with_no_profile(harness):
    """A declaration is not enough: the read is *the profile* plus what was
    declared, and there is nothing to serve the first half of."""

    await harness.declare(PlayIntent.COMPETITIVE)

    with pytest.raises(PlayerProfileNotFound):
        await harness.read()


# ---------------------------------------------------------------------------
# The read, for the You tab: what the store concluded about each photograph
# ---------------------------------------------------------------------------

#: The reviewer the stored verdicts name. Any string the note can carry.
MODEL = "openai/clip-vit-base-patch32"
#: Thirteen similarities: five on-court prompts high, eight off-court low — and
#: the reverse. What the numbers are is `verdict_from_similarities`'s business.
ON_COURT = [0.9] * 5 + [0.1] * 8
OFF_COURT = [0.1] * 5 + [0.9] * 8


async def test_the_read_carries_what_was_concluded_about_each_photograph(harness):
    """The uploader's three-valued reading, one photo at a time
    (``docs/adr/0179`` §8): passed, flagged, and *nobody looked* — which is an
    **absence** from the map, never a third value, exactly as an undeclared
    sport is absent from ``play_intents``.

    ``GET /photos/{id}`` answers no verdict on purpose (``docs/adr/0133``), so
    this read is the one place the owner is told what stands beside each of
    their photographs.
    """

    passed = harness.a_photo_held(
        metadata=review_metadata(
            verdict_from_similarities(model=MODEL, similarities=ON_COURT)
        )
    )
    flagged = harness.a_photo_held(
        metadata=review_metadata(
            verdict_from_similarities(model=MODEL, similarities=OFF_COURT)
        )
    )
    unlooked_at = harness.a_photo_held(
        metadata=review_metadata(
            verdict_when_unreviewable(PhotoReviewUnavailability.TIMEOUT)
        )
    )
    await harness.commit_profile(photo_ids=[flagged, passed, unlooked_at])

    surface = await harness.read()

    assert surface.profile.photo_ids == (flagged, passed, unlooked_at)
    assert surface.photo_verdicts == {
        passed: PhotoReviewDecision.ALLOWED,
        flagged: PhotoReviewDecision.FLAGGED,
    }


async def test_a_profile_with_no_photographs_asks_the_store_nothing(harness):
    """A verdict costs a round trip per photograph (``docs/adr/0138``), and a
    profile holding none has nothing to pay for."""

    await harness.commit_profile(photo_ids=[])

    surface = await harness.read()

    assert surface.photo_verdicts == {}
    assert harness.photos.decision_reads == []


async def test_a_profile_from_before_the_gender_question_omits_the_answer(harness):
    """Never ``PREFER_NOT_TO_SAY``, which is an answer a player gives. The
    stream is one written before the question existed — no upcaster, the field
    simply unset — and the response leaves the key out so a client pre-selects
    nothing rather than something (``docs/adr/0179`` §4). The preference is
    the other case: ``ANY`` is what never having expressed one *is*.
    """

    await harness.store.append(
        aggregate_type=PLAYER_PROFILE_AGGREGATE,
        aggregate_id=PLAYER,
        expected_version=0,
        events=[
            PlayerProfileCreated(
                player_id=PLAYER,
                social_tags=("PLAYS_TO_WIN", "HERE_TO_IMPROVE"),
                photo_ids=(),
                weekly_hours=("2:19",),
                latitude=51.51,
                longitude=-0.13,
                idempotency_key="commit-before-the-question",
                occurred_at=harness.clock.now(),
            ),
        ],
    )

    body = PlayerProfileReadResponse.from_domain(await harness.read()).model_dump(
        exclude_unset=True, mode="json"
    )

    assert "gender" not in body
    assert body["gender_preference"] == "ANY"

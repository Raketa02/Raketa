"""The five use cases behind the profile surface reads and writes.

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

from app.kernel import Sport
from app.modules.player_profile.application.change_availability import (
    ChangeAvailability,
)
from app.modules.player_profile.application.change_location import ChangeLocation
from app.modules.player_profile.application.change_search_radius import (
    ChangeSearchRadius,
)
from app.modules.player_profile.application.commands import (
    ChangeAvailabilityCommand,
    ChangeLocationCommand,
    ChangeSearchRadiusCommand,
    CommitPlayerProfileCommand,
    DeclarePlayIntentCommand,
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
from app.modules.player_profile.domain.consent import ConsentSurface
from app.modules.player_profile.domain.errors import (
    PlayerProfileNotFound,
    SearchRadiusOutOfBounds,
)
from app.modules.player_profile.domain.events import (
    AvailabilityChanged,
    LocationChanged,
    PlayerProfileCreated,
    PlayIntentDeclared,
    ProposalsOptInAnswered,
    SearchRadiusChanged,
)
from app.modules.player_profile.domain.gender import (
    DEFAULT_GENDER_PREFERENCE,
    Gender,
)
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
from app.modules.player_profile.domain.search_radius import SEARCH_RADIUS_BOUNDS
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
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

PLAYER = new_uuid()
STRANGER = new_uuid()

#: The fix every profile here is committed with. It rounds to (51.51, -0.13).
HOME_FIX = (51.5073509, -0.1277583)


class Harness:
    """The five use cases over fakes, each built the way a request builds one."""

    def __init__(self) -> None:
        self.store = InMemoryEventStore()
        self.publisher = RecordingPublisher()
        self.uow = CountingUnitOfWork()
        self.clock = FrozenClock()
        #: One store for the commit and the read: the commit proves each photo
        #: id against it, and the read asks it what was concluded about each.
        self.photos = InMemoryPhotoStorage()

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
            availability=[(2, "EVENING"), (6, "MORNING")],
            latitude=HOME_FIX[0],
            longitude=HOME_FIX[1],
            search_radius_km=SEARCH_RADIUS_BOUNDS.default_km,
            gender=Gender.WOMAN,
            gender_preference=DEFAULT_GENDER_PREFERENCE,
            proposals_opt_in=True,
            consent_copy_version="proposals-2026-08",
            consent_surface=ConsentSurface.ONBOARDING,
        )
        arguments.update(overrides)
        await CommitPlayerProfile(
            profiles=self._profiles(),
            photos=self.photos,
            uow=self.uow,
            clock=self.clock,
        ).execute(CommitPlayerProfileCommand(**arguments))
        self.forget_what_the_commit_released()

    def forget_what_the_commit_released(self) -> None:
        """The arrangement is not the act. What a test asserts on is the write."""

        self.publisher.published.clear()
        self.uow.commits = 0
        self.store.appends = 0

    async def change_availability(self, cells, *, player_id=PLAYER):
        return await ChangeAvailability(
            profiles=self._profiles(), uow=self.uow, clock=self.clock
        ).execute(
            ChangeAvailabilityCommand(player_id=player_id, availability=cells)
        )

    async def change_radius(self, kilometres: int, *, player_id=PLAYER):
        return await ChangeSearchRadius(
            profiles=self._profiles(), uow=self.uow, clock=self.clock
        ).execute(
            ChangeSearchRadiusCommand(
                player_id=player_id, search_radius_km=kilometres
            )
        )

    async def change_location(
        self, latitude: float, longitude: float, *, player_id=PLAYER
    ) -> None:
        await ChangeLocation(
            profiles=self._profiles(), uow=self.uow, clock=self.clock
        ).execute(
            ChangeLocationCommand(
                player_id=player_id, latitude=latitude, longitude=longitude
            )
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

    ``AvailabilityGrid.edited`` is what this write builds through, so a player
    who unticks everything appends an ``AvailabilityChanged`` carrying nothing —
    which is a fact recorded, not a value missing.
    """

    await harness.commit_profile()

    profile = await harness.change_availability([])

    assert len(profile.availability) == 0
    (released,) = harness.publisher.published
    assert isinstance(released, AvailabilityChanged)
    assert released.availability == ()
    assert harness.uow.commits == 1


async def test_the_same_week_twice_appends_once(harness):
    """The aggregate's *a transition that changes nothing records nothing* rule,
    which is what makes the unkeyed `PUT` safe to send twice."""

    await harness.commit_profile()
    week = [(4, "AFTERNOON")]

    await harness.change_availability(week)
    harness.publisher.published.clear()
    profile = await harness.change_availability(week)

    assert harness.publisher.published == []
    assert profile.availability.codes == ("4:AFTERNOON",)
    # Still committed: the transaction boundary belongs to the command, not to
    # whether the command found anything to record.
    assert harness.uow.commits == 2


async def test_a_week_written_by_a_player_with_no_profile_is_refused(harness):
    with pytest.raises(PlayerProfileNotFound):
        await harness.change_availability([(1, "MORNING")])

    assert harness.publisher.published == []
    assert harness.uow.commits == 0


# ---------------------------------------------------------------------------
# The radius
# ---------------------------------------------------------------------------


async def test_the_radius_is_rechecked_against_the_served_bounds(harness):
    await harness.commit_profile()

    profile = await harness.change_radius(22)

    (released,) = harness.publisher.published
    assert isinstance(released, SearchRadiusChanged)
    assert released.search_radius_km == 22
    assert profile.search_radius.kilometres == 22


async def test_an_illegal_radius_is_refused_before_the_store_is_asked_anything(
    harness,
):
    """The refusal is pure and the replay is not, so the order is the cheap one.

    A player with no profile at all still gets ``search_radius_out_of_bounds``
    rather than ``player_profile_not_found``, which is the assertion that the
    check really does come first.
    """

    with pytest.raises(SearchRadiusOutOfBounds):
        await harness.change_radius(SEARCH_RADIUS_BOUNDS.maximum_km + 1)

    assert harness.store.appends == 0
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
    """Intent is a preference and not a consent: there is no wording to evidence
    it against, so *where they were standing* is not a new fact about what kind
    of game they want."""

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
                availability=("2:EVENING",),
                latitude=51.51,
                longitude=-0.13,
                search_radius_km=10,
                idempotency_key="commit-before-the-question",
                occurred_at=harness.clock.now(),
            ),
            ProposalsOptInAnswered(
                player_id=PLAYER,
                accepted=True,
                copy_version="proposals-2026-08",
                surface=ConsentSurface.ONBOARDING.value,
                occurred_at=harness.clock.now(),
            ),
        ],
    )

    body = PlayerProfileReadResponse.from_domain(await harness.read()).model_dump(
        exclude_unset=True, mode="json"
    )

    assert "gender" not in body
    assert body["gender_preference"] == "ANY"

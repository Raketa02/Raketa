"""The four use cases behind the profile surface Play reads and writes.

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
from app.modules.player_profile.application.change_search_radius import (
    ChangeSearchRadius,
)
from app.modules.player_profile.application.commands import (
    ChangeAvailabilityCommand,
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
    PlayIntentDeclared,
    SearchRadiusChanged,
)
from app.modules.player_profile.domain.gender import (
    DEFAULT_GENDER_PREFERENCE,
    Gender,
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
    EventSourcedPlayerProfileRepository,
)
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


class Harness:
    """The four use cases over fakes, each built the way a request builds one."""

    def __init__(self) -> None:
        self.store = InMemoryEventStore()
        self.publisher = RecordingPublisher()
        self.uow = CountingUnitOfWork()
        self.clock = FrozenClock()

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
            latitude=51.5073509,
            longitude=-0.1277583,
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
            photos=InMemoryPhotoStorage(),
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
            profiles=self._profiles(), declarations=self._declarations()
        ).execute(player_id)


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

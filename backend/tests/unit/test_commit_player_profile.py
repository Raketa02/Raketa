"""The profile commit use case: one transaction, idempotent, and re-validating.

The **event store** is faked, not the repository — so the identity map, the
version arithmetic and the aggregate-type string the repository introduced are
all exercised rather than replaced. The **photo storage** is faked too, and
ownership is the reason it is faithful: it keys objects on the whole
``PhotoRef``, so a photo id belonging to another player misses here exactly as it
misses in S3.
"""

from __future__ import annotations

import pytest

from app.modules.player_profile.application.commands import (
    CommitPlayerProfileCommand,
)
from app.modules.player_profile.application.commit_player_profile import (
    CommitPlayerProfile,
)
from app.modules.player_profile.application.has_player_profile import HasPlayerProfile
from app.modules.player_profile.domain.errors import (
    WeeklyHoursEmpty,
    IntroNotAdmitted,
    IntroRefusal,
    PhotoNotFound,
    PlayerProfileAlreadyExists,
    SocialTagSelectionOutOfBounds,
    UnknownSocialTag,
)
from app.modules.player_profile.domain.events import (
    IntroWritten,
    PlayerProfileCreated,
)
from app.modules.player_profile.domain.gender import (
    DEFAULT_GENDER_PREFERENCE,
    Gender,
    GenderPreference,
)
from app.modules.player_profile.domain.photos import PhotoRef, TranscodedImage
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


class Harness:
    """The use case over fakes, plus the reads a test wants afterwards."""

    def __init__(self) -> None:
        self.store = InMemoryEventStore()
        self.publisher = RecordingPublisher()
        self.uow = CountingUnitOfWork()
        self.photos = InMemoryPhotoStorage()
        self.clock = FrozenClock()

    def commit(self) -> CommitPlayerProfile:
        # A repository per call, as the request scope builds one: the version
        # bookkeeping it holds must never outlive the transaction it was built
        # beside.
        return CommitPlayerProfile(
            profiles=self._profiles(),
            photos=self.photos,
            uow=self.uow,
            clock=self.clock,
        )

    def has_profile(self) -> HasPlayerProfile:
        return HasPlayerProfile(profiles=self._profiles())

    def _profiles(self) -> EventSourcedPlayerProfileRepository:
        return EventSourcedPlayerProfileRepository(
            event_store=self.store, events=self.publisher
        )

    async def upload(self, *, owner_id=PLAYER):
        """A photo that exists, the way the upload path leaves one behind."""

        ref = PhotoRef(owner_id=owner_id, photo_id=new_uuid())
        await self.photos.put(
            ref,
            TranscodedImage(
                data=b"jpeg", media_type="image/jpeg", width=100, height=100
            ),
            metadata={},
        )
        return ref.photo_id


def a_command(**overrides) -> CommitPlayerProfileCommand:
    arguments = dict(
        player_id=PLAYER,
        idempotency_key="commit-1",
        social_tag_ids=["PLAYS_TO_WIN", "HERE_TO_IMPROVE"],
        photo_ids=[],
        weekly_hours=[(2, 19)],
        latitude=51.5073509,
        longitude=-0.1277583,
        gender=Gender.WOMAN,
        gender_preference=GenderPreference.WOMEN_ONLY,
    )
    arguments.update(overrides)
    return CommitPlayerProfileCommand(**arguments)


@pytest.fixture
def harness() -> Harness:
    return Harness()


# ---------------------------------------------------------------------------
# The happy path
# ---------------------------------------------------------------------------


async def test_a_commit_records_every_answer_in_one_transaction(harness: Harness):
    committed = await harness.commit().execute(a_command())

    assert committed.created is True
    assert harness.uow.commits == 1, "one transaction, not one per answer"
    assert [type(event) for event in harness.publisher.published] == [
        PlayerProfileCreated,
    ]


async def test_the_precise_fix_never_reaches_the_stream(harness: Harness):
    """Coarsened on the way in, so there is no version of this stream from which
    the device's own reading could be recovered."""

    await harness.commit().execute(a_command(latitude=51.5073509, longitude=-0.1277583))

    created = harness.publisher.published[0]
    assert (created.latitude, created.longitude) == (51.51, -0.13)


async def test_a_commit_with_no_hours_ticked_is_refused(harness: Harness):
    """The week has a floor of one hour (ADR-0102), and this is where it binds.

    Blank is not read as *no preference* any more, and it is not read as a
    measured zero either — it is refused, so the question is answered rather
    than guessed at.
    """

    with pytest.raises(WeeklyHoursEmpty):
        await harness.commit().execute(a_command(weekly_hours=[]))

    assert harness.uow.commits == 0, "a refused commit records nothing"


async def test_one_ticked_hour_is_enough_to_commit(harness: Harness):
    """The minimum is exactly one — a player who only plays at ten on a Saturday
    must be able to say precisely that."""

    committed = await harness.commit().execute(a_command(weekly_hours=[(6, 10)]))

    assert committed.profile.weekly_hours.codes == ("6:10",)


async def test_committed_photos_are_the_ones_the_player_uploaded(harness: Harness):
    first, second = await harness.upload(), await harness.upload()

    committed = await harness.commit().execute(a_command(photo_ids=[second, first]))

    assert committed.profile.photo_ids == (second, first)


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


async def test_the_same_key_twice_creates_one_profile_and_returns_the_same_result(
    harness: Harness,
):
    first = await harness.commit().execute(a_command(idempotency_key="draft-7"))
    second = await harness.commit().execute(a_command(idempotency_key="draft-7"))

    assert second.created is False
    assert second.profile.created_at == first.profile.created_at
    assert second.profile.social_tags == first.profile.social_tags
    stream = await harness.store.load_stream(
        aggregate_type="player_profile", aggregate_id=PLAYER
    )
    assert len(stream) == 1, "the retry recorded nothing"
    assert harness.uow.commits == 1


async def test_a_retry_carrying_different_answers_still_replays_the_first_commit(
    harness: Harness,
):
    """The key identifies the *request*. A retry of it is the same request, and
    a client that re-sent a differently-shaped body has a bug the platform must
    not resolve by silently rewriting what was committed."""

    first = await harness.commit().execute(a_command(idempotency_key="draft-7"))

    second = await harness.commit().execute(
        a_command(
            idempotency_key="draft-7",
            social_tag_ids=["QUIET_AND_FOCUSED", "HERE_TO_COMPETE"],
            gender=Gender.MAN,
        )
    )

    assert second.profile.social_tags == first.profile.social_tags
    assert second.profile.gender == first.profile.gender


async def test_a_second_commit_under_a_different_key_is_refused(harness: Harness):
    """Not a retry: a second attempt at a part that happens once."""

    await harness.commit().execute(a_command(idempotency_key="draft-7"))

    with pytest.raises(PlayerProfileAlreadyExists):
        await harness.commit().execute(a_command(idempotency_key="draft-8"))


async def test_two_players_commit_independently(harness: Harness):
    """The stream is keyed on the player, so one player's key says nothing about
    another's."""

    other = new_uuid()

    await harness.commit().execute(a_command(idempotency_key="k"))
    committed = await harness.commit().execute(
        a_command(player_id=other, idempotency_key="k")
    )

    assert committed.created is True


# ---------------------------------------------------------------------------
# Re-validation — every one of these is something a client could have prevented
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tag_ids, expected",
    [
        (["PLAYS_TO_WIN"], SocialTagSelectionOutOfBounds),
        (
            [
                "PLAYS_TO_WIN",
                "HERE_TO_IMPROVE",
                "QUIET_AND_FOCUSED",
                "HERE_TO_COMPETE",
                "STAYS_FOR_A_DRINK",
                "SHARES_A_LIFT",
                "WARMS_UP_PROPERLY",
            ],
            SocialTagSelectionOutOfBounds,
        ),
        (["PLAYS_TO_WIN", "LOOKING_FOR_A_DATE"], UnknownSocialTag),
    ],
)
async def test_a_tag_selection_the_vocabulary_refuses_is_refused_here(
    harness: Harness, tag_ids, expected
):
    with pytest.raises(expected):
        await harness.commit().execute(a_command(social_tag_ids=tag_ids))

    assert harness.uow.commits == 0


async def test_a_photo_id_that_does_not_exist_is_refused(harness: Harness):
    with pytest.raises(PhotoNotFound):
        await harness.commit().execute(a_command(photo_ids=[new_uuid()]))

    assert harness.uow.commits == 0


async def test_another_players_photo_id_is_refused_the_same_way(harness: Harness):
    """Checked through the port's own ``PhotoRef``, so ownership is the port's
    contract rather than a check this use case had to remember to write."""

    somebody_elses = await harness.upload(owner_id=new_uuid())

    with pytest.raises(PhotoNotFound):
        await harness.commit().execute(a_command(photo_ids=[somebody_elses]))

    assert harness.photos.existence_checks == [
        PhotoRef(owner_id=PLAYER, photo_id=somebody_elses)
    ], "asked under the caller's own identity, which is why it missed"


async def test_a_refused_commit_asks_the_photo_store_nothing(harness: Harness):
    """The pure refusals run first: a commit that was going to be refused for
    its tags should not cost a round trip per photo before it is."""

    photo = await harness.upload()

    with pytest.raises(SocialTagSelectionOutOfBounds):
        await harness.commit().execute(
            a_command(social_tag_ids=["PLAYS_TO_WIN"], photo_ids=[photo])
        )

    assert harness.photos.existence_checks == []


# ---------------------------------------------------------------------------
# The entry gate's question
# ---------------------------------------------------------------------------


async def test_a_player_with_no_profile_is_reported_as_having_none(harness: Harness):
    assert await harness.has_profile().execute(PLAYER) is False


async def test_the_profile_is_reported_as_existing_immediately_after_the_commit(
    harness: Harness,
):
    """Read from the stream rather than a projection, which is what stops a
    player who has just finished the social steps being sent back into them."""

    await harness.commit().execute(a_command())

    assert await harness.has_profile().execute(PLAYER) is True


async def test_asking_whether_a_profile_exists_replays_nothing(harness: Harness):
    """A caller that only asked a question must not come away holding an
    aggregate it could then save."""

    await harness.commit().execute(a_command())
    appends_before = harness.store.appends

    await harness.has_profile().execute(PLAYER)

    assert harness.store.appends == appends_before


async def test_the_gender_answer_and_the_preference_reach_the_creating_event():
    """Both ride on the commit that creates the profile, because gender is
    required at profile creation and profile creation is one request
    (``docs/adr/0096``)."""

    harness = Harness()

    await harness.commit().execute(
        a_command(
            gender=Gender.PREFER_NOT_TO_SAY,
            gender_preference=GenderPreference.MEN_ONLY,
        )
    )

    created = harness.publisher.published[0]
    assert isinstance(created, PlayerProfileCreated)
    assert created.gender == "PREFER_NOT_TO_SAY"
    assert created.gender_preference == "MEN_ONLY"


async def test_a_commit_that_names_no_preference_records_the_unconstrained_one():
    """`ANY` is what never having expressed a preference *is*, so the default
    survives the whole path rather than being re-decided at each layer."""

    harness = Harness()

    await harness.commit().execute(
        a_command(gender_preference=DEFAULT_GENDER_PREFERENCE)
    )

    assert harness.publisher.published[0].gender_preference == "ANY"


# ---------------------------------------------------------------------------
# The intro (docs/adr/0170) — fenced before anything is stored
# ---------------------------------------------------------------------------


async def test_a_commit_with_an_intro_stores_it_as_its_own_event(harness: Harness):
    committed = await harness.commit().execute(
        a_command(intro="Moved from Wrocław in May. Needs opponents.")
    )

    assert [type(event) for event in harness.publisher.published] == [
        PlayerProfileCreated,
        IntroWritten,
    ]
    assert harness.uow.commits == 1, "still one transaction"
    assert committed.profile.intro is not None
    assert committed.profile.intro.text == "Moved from Wrocław in May. Needs opponents."


async def test_a_commit_without_an_intro_stores_no_intro_event(harness: Harness):
    committed = await harness.commit().execute(a_command(intro=None))

    assert [type(event) for event in harness.publisher.published] == [
        PlayerProfileCreated,
    ]
    assert committed.profile.intro is None


async def test_a_whitespace_only_intro_is_a_skipped_one(harness: Harness):
    committed = await harness.commit().execute(a_command(intro="   "))

    assert committed.profile.intro is None
    assert IntroWritten not in {type(event) for event in harness.publisher.published}


async def test_an_intro_carrying_contact_is_refused_before_anything_is_stored(
    harness: Harness,
):
    """The refusal is a pure one and runs ahead of the object-store reads — a
    commit that was going to be refused for its line should not cost three
    round trips first, and nothing about it may reach a stream."""

    with pytest.raises(IntroNotAdmitted) as caught:
        await harness.commit().execute(a_command(intro="WhatsApp me 600 123 456"))

    assert caught.value.reason is IntroRefusal.CONTAINS_CONTACT
    assert harness.uow.commits == 0
    assert harness.publisher.published == []

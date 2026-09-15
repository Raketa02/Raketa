"""The three card fields the candidate index deliberately does not hold.

Two of them were always here — a nickname belongs to ``users`` and a photo list
to the Player profile — and the third arrived with ``docs/adr/0138``: **what the
on-court check concluded about the photograph a card is about to draw**.

That third one is the only field on a card assembled from an *object store*, and
it is the reason this file exists. It costs one round trip per row that has a
photograph, so *who is asked, and how many times* is a property worth asserting
rather than a consequence of how the loop happens to be written. And what may be
believed about a stored verdict is a rule with three legacy populations behind
it, every one of which reads ``allowed`` off an image nothing ever looked at.
"""

from __future__ import annotations

from asyncio import sleep
from typing import Collection, Mapping, Sequence
from uuid import UUID

import pytest

from app.kernel import Instant, instant
from app.modules.matchmaking.infrastructure.player_card_source import (
    PlayerCardIdentities,
)
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.availability import AvailabilityGrid
from app.modules.player_profile.domain.consent import ConsentSurface
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.photos import (
    PhotoRef,
    PhotoReviewDecision,
    PhotoReviewUnavailability,
    PhotoReviewVerdict,
    review_metadata,
    verdict_from_similarities,
    verdict_when_unreviewable,
)
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_profile.domain.search_radius import SearchRadius
from app.modules.player_profile.domain.social_tags import SocialTagSelection
from app.modules.users.domain.ports import Naming
from datetime import datetime, timezone

from tests.unit.fake_photo_storage import InMemoryPhotoStorage

ALICE = UUID("11111111-1111-1111-1111-111111111111")
BRUNO = UUID("22222222-2222-2222-2222-222222222222")

COMMITTED_AT: Instant = instant(datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc))

MODEL = "openai/clip-vit-base-patch32"

#: Confidently on-court, and confidently not. Both are answers somebody took.
ON_COURT = [0.9] * 5 + [0.1] * 8
OFF_COURT = [0.1] * 5 + [0.9] * 8


class Names:
    """``users``, answering the one question the matcher asks it.

    Answers the pair the port promises — the nickname is a lowercase twin of the
    name here — because the adapter under test is what leaves the handle behind.
    """

    def __init__(self, by_id: Mapping[UUID, str]) -> None:
        self._by_id = dict(by_id)
        self.asked: list[Collection[UUID]] = []

    async def find_namings_of(
        self, user_ids: Collection[UUID]
    ) -> Mapping[UUID, Naming]:
        self.asked.append(list(user_ids))
        return {
            user_id: Naming(name=name, nickname=name.lower())
            for user_id, name in self._by_id.items()
            if user_id in set(user_ids)
        }


class Profiles:
    """The Player profile port, holding one folded profile per player."""

    def __init__(self, photos: Mapping[UUID, Sequence[UUID]]) -> None:
        self._photos = dict(photos)

    async def load(self, player_id: UUID) -> PlayerProfile | None:
        if player_id not in self._photos:
            return None
        return PlayerProfile.create(
            player_id=player_id,
            social_tags=SocialTagSelection.from_ids(
                ["PLAYS_TO_WIN", "HERE_TO_IMPROVE"]
            ),
            photo_ids=list(self._photos[player_id]),
            availability=AvailabilityGrid.from_codes(["1:EVENING"]),
            location=LocationArea.around(41.39, 2.16),
            search_radius=SearchRadius.chosen(10),
            gender=Gender.WOMAN,
            gender_preference=GenderPreference.ANY,
            proposals_opt_in_accepted=True,
            consent_copy_version="proposals-2026-08",
            consent_surface=ConsentSurface.ONBOARDING,
            idempotency_key=f"commit-{player_id}",
            occurred_at=COMMITTED_AT,
        )


def store_photo(
    storage: InMemoryPhotoStorage, *, owner_id: UUID, verdict: PhotoReviewVerdict
) -> UUID:
    """One photo in the store, carrying the metadata that verdict would write."""

    ref = PhotoRef(owner_id=owner_id, photo_id=UUID(int=len(storage.objects) + 1))
    storage.already_holding(ref, review_metadata(verdict))
    return ref.photo_id


def scored(similarities: list[float]) -> PhotoReviewVerdict:
    return verdict_from_similarities(model=MODEL, similarities=similarities)


def source(
    storage: InMemoryPhotoStorage,
    *,
    names: Mapping[UUID, str],
    photos: Mapping[UUID, Sequence[UUID]],
) -> PlayerCardIdentities:
    return PlayerCardIdentities(
        users=Names(names),  # type: ignore[arg-type]
        profiles=Profiles(photos),  # type: ignore[arg-type]
        photos=storage,
    )


# ---------------------------------------------------------------------------
# What the check concluded, on somebody else's card
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("similarities", "expected"),
    [(ON_COURT, PhotoReviewDecision.ALLOWED), (OFF_COURT, PhotoReviewDecision.FLAGGED)],
)
async def test_a_scored_photo_carries_its_verdict_onto_the_card(
    similarities: list[float], expected: PhotoReviewDecision
) -> None:
    storage = InMemoryPhotoStorage()
    photo_id = store_photo(storage, owner_id=ALICE, verdict=scored(similarities))

    cards = await source(
        storage, names={ALICE: "ali"}, photos={ALICE: [photo_id]}
    ).identities_for([ALICE])

    assert cards[ALICE].photo_id == photo_id
    assert cards[ALICE].review is expected


@pytest.mark.parametrize("why", list(PhotoReviewUnavailability))
async def test_a_photo_nobody_could_check_carries_no_verdict(
    why: PhotoReviewUnavailability,
) -> None:
    """The whole of #307's second half, seen from the card.

    The photograph is drawn — an outage is not a reason to hide somebody's face
    — and it wears no shield, because nothing looked at it.
    """

    storage = InMemoryPhotoStorage()
    photo_id = store_photo(
        storage, owner_id=ALICE, verdict=verdict_when_unreviewable(why)
    )

    cards = await source(
        storage, names={ALICE: "ali"}, photos={ALICE: [photo_id]}
    ).identities_for([ALICE])

    assert cards[ALICE].photo_id == photo_id
    assert cards[ALICE].review is None


async def test_the_pass_through_eras_allowed_draws_no_shield() -> None:
    # `PassThroughPhotoReview` wrote `review: allowed` about images nothing
    # looked at. ADR-0132's job drains that population on a clock measured in
    # hours; a tick claiming a stranger's photo passed a check is not a thing to
    # be wrong about for that long.
    storage = InMemoryPhotoStorage()
    photo_id = store_photo(
        storage,
        owner_id=ALICE,
        verdict=PhotoReviewVerdict(decision=PhotoReviewDecision.ALLOWED),
    )

    cards = await source(
        storage, names={ALICE: "ali"}, photos={ALICE: [photo_id]}
    ).identities_for([ALICE])

    assert cards[ALICE].review is None


async def test_the_verdict_asked_for_is_the_photo_the_card_draws() -> None:
    """**The first photo, and only the first.** Order is meaning in a player's
    photo list, and a shield taken from a photograph nobody can see would be a
    fact about an image the card does not show."""

    storage = InMemoryPhotoStorage()
    shown = store_photo(storage, owner_id=ALICE, verdict=scored(ON_COURT))
    second = store_photo(storage, owner_id=ALICE, verdict=scored(OFF_COURT))

    cards = await source(
        storage, names={ALICE: "ali"}, photos={ALICE: [shown, second]}
    ).identities_for([ALICE])

    assert cards[ALICE].review is PhotoReviewDecision.ALLOWED
    assert storage.decision_reads == [PhotoRef(owner_id=ALICE, photo_id=shown)]


# ---------------------------------------------------------------------------
# What it costs, and what it must not cost
# ---------------------------------------------------------------------------


async def test_a_player_with_no_photo_costs_no_round_trip() -> None:
    """A card with no photograph has nothing to say about a check, so the store
    is not asked — the one place this could quietly become a request per row of
    the shortlist rather than per row that has a picture."""

    storage = InMemoryPhotoStorage()

    cards = await source(
        storage, names={ALICE: "ali"}, photos={ALICE: []}
    ).identities_for([ALICE])

    assert cards[ALICE].photo_id is None
    assert cards[ALICE].review is None
    assert storage.decision_reads == []


class CountsOverlap(InMemoryPhotoStorage):
    """Records how many verdict reads were in flight at once.

    The one property a call count cannot see. Each read yields to the event loop
    before it answers, so a caller that awaits them one at a time never gets past
    one in flight and a caller that hands them over together reaches as many as
    it handed over.
    """

    def __init__(self) -> None:
        super().__init__()
        self._in_flight = 0
        self.most_at_once = 0

    async def review_decision(self, ref: PhotoRef) -> PhotoReviewDecision | None:
        self._in_flight += 1
        self.most_at_once = max(self.most_at_once, self._in_flight)
        try:
            await sleep(0)
            return await super().review_decision(ref)
        finally:
            self._in_flight -= 1


async def test_the_shortlists_verdicts_are_asked_for_together() -> None:
    """**Twenty store latencies beside each other, never end to end.**

    A profile is folded through the request's own session, so those reads stay
    serial — an ``AsyncSession`` is not safe to use concurrently. A verdict is an
    object-store round trip that shares nothing, and serialising those would put
    the whole shortlist's store latency inside one search.
    """

    storage = CountsOverlap()
    hers = store_photo(storage, owner_id=ALICE, verdict=scored(ON_COURT))
    theirs = store_photo(storage, owner_id=BRUNO, verdict=scored(OFF_COURT))

    cards = await source(
        storage,
        names={ALICE: "ali", BRUNO: "bru"},
        photos={ALICE: [hers], BRUNO: [theirs]},
    ).identities_for([ALICE, BRUNO])

    assert cards[ALICE].review is PhotoReviewDecision.ALLOWED
    assert cards[BRUNO].review is PhotoReviewDecision.FLAGGED
    assert storage.most_at_once == 2, "the verdicts were asked for one at a time"


async def test_one_ask_per_row_that_has_a_photograph() -> None:
    storage = InMemoryPhotoStorage()
    hers = store_photo(storage, owner_id=ALICE, verdict=scored(ON_COURT))

    cards = await source(
        storage,
        names={ALICE: "ali", BRUNO: "bru"},
        photos={ALICE: [hers], BRUNO: []},
    ).identities_for([ALICE, BRUNO])

    assert set(cards) == {ALICE, BRUNO}
    assert len(storage.decision_reads) == 1


async def test_an_empty_shortlist_asks_nobody_anything() -> None:
    storage = InMemoryPhotoStorage()

    assert await source(storage, names={}, photos={}).identities_for([]) == {}
    assert storage.decision_reads == []


# ---------------------------------------------------------------------------
# The two absences that were already here
# ---------------------------------------------------------------------------


async def test_a_player_users_has_never_heard_of_gets_no_card() -> None:
    # Unchanged by the verdict: the nickname is what decides whether there is a
    # card at all, and the caller drops the row before the record is written.
    storage = InMemoryPhotoStorage()

    cards = await source(
        storage, names={ALICE: "ali"}, photos={ALICE: [], BRUNO: []}
    ).identities_for([ALICE, BRUNO])

    assert set(cards) == {ALICE}


async def test_a_player_with_no_committed_profile_draws_the_poster() -> None:
    storage = InMemoryPhotoStorage()

    cards = await source(
        storage, names={ALICE: "ali"}, photos={}
    ).identities_for([ALICE])

    assert cards[ALICE].photo_id is None
    assert cards[ALICE].review is None

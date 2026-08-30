"""The card's photograph gets an address, and the record never learns it.

``GET /photos/{id}`` signs only your own photos and refuses a stranger's id on
purpose, so a card's photo id — which is by definition somebody else's — is an id
the client can do nothing with. This adapter is the other half of that refusal:
the server that already disclosed the person signs their photograph too.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.modules.matchmaking.domain.cards import CardPhotoLinks
from app.modules.matchmaking.domain.searches import (
    CandidateBand,
    RecordedCard,
    SearchCandidateRecord,
    WithheldReason,
)
from app.modules.matchmaking.infrastructure.card_photo_links import (
    PresignedCardPhotos,
)
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

VALID_FOR_MINUTES = 5


def _row(
    *, photo_id: UUID | None, band: CandidateBand = CandidateBand.RETURNED
) -> SearchCandidateRecord:
    returned = band is CandidateBand.RETURNED
    return SearchCandidateRecord(
        band=band,
        position=1,
        player_id=uuid4(),
        fit=72.5,
        terms=({"term": "LEVEL_FIT", "weight": 29.9, "value": 1.0},),
        degraded_terms=(),
        degraded_reasons=(),
        modifiers=(),
        liveness_reasons=(),
        liveness_signals={},
        shared_count=2,
        their_slot_count=5,
        days_away=1,
        inclusion_reason=None,
        withheld_reason=None if returned else WithheldReason.BELOW_FLOOR,
        missing_terms=(),
        reliability_penalty_applied=False,
        reliability_penalty_decisive=False,
        concerns=(),
        distance_km=4,
        card=(
            RecordedCard(
                nickname="ada",
                photo_id=photo_id,
                area_code="LDN-CENTRAL",
                social_tags=("PLAYS_TO_WIN",),
                level=2.7,
                band="Improver",
                range_low=2.36,
                range_high=3.04,
            )
            if returned
            else None
        ),
        at_stake=None,
    )


@pytest.fixture
def storage() -> InMemoryPhotoStorage:
    return InMemoryPhotoStorage()


@pytest.fixture
def links(storage: InMemoryPhotoStorage) -> CardPhotoLinks:
    return PresignedCardPhotos(
        storage=storage, valid_for_minutes=VALID_FOR_MINUTES
    )


async def test_it_signs_each_card_photo_as_the_candidates_own(
    links: CardPhotoLinks, storage: InMemoryPhotoStorage
):
    """**The owner is the person on the card, never the person looking.**

    Storage keys the whole ``PhotoRef``, so a link signed under the searcher's
    id would reach an object that does not exist — the ownership rule the port
    carries, arriving here as a broken image rather than as a leak.
    """

    photo = uuid4()
    row = _row(photo_id=photo)

    minted = await links.links_for([row])

    assert minted == {
        row.player_id: storage.URL_PREFIX + f"{row.player_id}/{photo}"
    }


async def test_a_row_with_no_photo_is_absent_rather_than_none(
    links: CardPhotoLinks, storage: InMemoryPhotoStorage
):
    """A player with no photo is not an absence to report: the field is omitted
    and the client draws the generated court poster. A ``None`` in the mapping
    would be a measured nothing, which is the other spelling."""

    with_one, without = _row(photo_id=uuid4()), _row(photo_id=None)

    minted = await links.links_for([with_one, without])

    assert without.player_id not in minted
    assert set(minted) == {with_one.player_id}
    assert len(storage.signed_windows) == 1, "a photo nobody has was signed for"


async def test_the_window_is_the_one_the_platform_signs_every_photo_for(
    links: CardPhotoLinks, storage: InMemoryPhotoStorage
):
    """One window for photographs, wherever they are asked for. A card that
    signed for longer than ``GET /photos/{id}`` would be a second answer to *how
    long may a link live*, decided where nobody is looking."""

    await links.links_for([_row(photo_id=uuid4())])

    assert storage.signed_windows == [VALID_FOR_MINUTES * 60]


async def test_it_never_asks_whether_the_photo_is_still_there(
    links: CardPhotoLinks, storage: InMemoryPhotoStorage
):
    """**Twenty round trips to turn a broken image into a poster, and it buys
    nothing.**

    ``GET /photos/{id}`` checks existence because there the photograph *is* the
    response and a 404 is an answer the client asked for. Here it is one field on
    one of twenty rows, and the link expires in minutes in any case — so a client
    that cannot survive an image that fails to load is already broken on the
    photograph it *can* see.
    """

    await links.links_for([_row(photo_id=uuid4())])

    assert storage.existence_checks == []


async def test_a_near_miss_carries_no_card_and_is_signed_for_nobody(
    links: CardPhotoLinks, storage: InMemoryPhotoStorage
):
    """The near-miss band is shown to nobody and records no card. A row with no
    card is not a row with a missing photo — it is a row with no person on it."""

    near_miss = _row(photo_id=None, band=CandidateBand.NEAR_MISS)

    assert await links.links_for([near_miss]) == {}
    assert storage.signed_windows == []

"""What an upload says when the reviewer could not be asked at all.

Its own module rather than a case in `test_photo_review.py`, for the reason that
one gives for being module-wide: the reviewer stands where the sidecar stands and
**every assertion here is made under one**, so *what an outage costs* is the
posture of the file rather than a branch inside a test.

**The answer is nothing, and until ``docs/adr/0138`` it was `allowed`.** That word
meant *nothing to warn about* in the only vocabulary the enum had, which was
survivable while the only reader was the person who chose the photograph. The
same word on a player card would mean *this photograph was checked and passed*,
about an image nothing looked at, to twenty people who are not its owner — so the
third state became real, spelled as an absence on the wire and on the object
alike.

Fail-open itself is unchanged and is asserted here: the upload is a `201`, the
photo is stored, and nobody is warned about anything.
"""

from __future__ import annotations

import pytest

from app.modules.player_profile.domain.photos import (
    REVIEW_METADATA_KEY,
    REVIEW_NOTE_METADATA_KEY,
    PhotoReviewUnavailability,
    PhotoReviewVerdict,
    verdict_when_unreviewable,
)
from tests.api.test_photos import ALICE, _auth_headers, _upload

WHY = PhotoReviewUnavailability.TIMEOUT


class UnreachableReview:
    """The sidecar down, answering exactly as the real adapter does then.

    It calls `verdict_when_unreviewable` rather than returning a ready-made
    verdict, so this module cannot pass while the rule it exists to assert has
    been changed underneath it.
    """

    async def review(self, image) -> PhotoReviewVerdict:
        return verdict_when_unreviewable(WHY)


@pytest.fixture
def photo_review():
    """Unreachable, for every test in this module."""

    return UnreachableReview()


async def test_the_upload_still_succeeds_and_the_photo_is_still_stored(
    client, photo_storage
) -> None:
    """**Fail-open, unchanged.** An outage of ours must not refuse a real
    player's first photograph for a reason that has nothing to do with it."""

    headers = await _auth_headers(client, ALICE)

    response = await _upload(client, headers)

    assert response.status_code == 201, response.text
    assert photo_storage.only_stored() is not None


async def test_the_uploader_is_told_nothing_rather_than_told_it_passed(
    client,
) -> None:
    headers = await _auth_headers(client, ALICE)

    body = (await _upload(client, headers)).json()

    assert body["review"] is None, "an outage was reported as a passed check"


async def test_the_object_carries_no_verdict_and_says_which_outage(
    client, photo_storage
) -> None:
    """The stored half, and the half a player card will read.

    No decision key at all — so ``review: allowed`` stops being a word this
    application writes about an unexamined image — and a note that keeps the
    population queryable for ADR-0132's re-review job.
    """

    headers = await _auth_headers(client, ALICE)
    await _upload(client, headers)

    metadata = photo_storage.only_stored().metadata

    assert REVIEW_METADATA_KEY not in metadata
    assert f"unavailable={WHY.value}" in metadata[REVIEW_NOTE_METADATA_KEY]

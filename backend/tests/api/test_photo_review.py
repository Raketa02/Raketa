"""What a flagged photo does to the two endpoints: nothing visible.

**The whole module runs with a reviewer that flags everything**, which is the
point rather than a setup detail — a flagged upload has to be the same 201, the
same body and the same readable photo as any other, because the check soft-warns
and never blocks (`docs/adr/0091`). The verdict's only trace is on the stored
object.

The rule that decides *flagged* is not here and could not usefully be: it is
arithmetic over similarity scores, asserted in
`tests/unit/test_photo_review_policy.py` with no HTTP, no container and no model.
"""

from __future__ import annotations

import pytest

from app.modules.player_profile.application.upload_photo import (
    REVIEW_METADATA_KEY,
    REVIEW_NOTE_METADATA_KEY,
)
from app.modules.player_profile.domain.photos import (
    PhotoReviewDecision,
    PhotoReviewVerdict,
)
from tests.api.test_photos import ALICE, _auth_headers, _upload


class ScriptedReview:
    """A reviewer with one answer, standing where the sidecar would."""

    def __init__(self, verdict: PhotoReviewVerdict) -> None:
        self._verdict = verdict

    async def review(self, image) -> PhotoReviewVerdict:
        return self._verdict


@pytest.fixture
def photo_review():
    """Flags everything, for every test in this module.

    Overrides the suite-wide pass-through in `tests/conftest.py`. Module-wide
    rather than per-test deliberately: *nothing changes* is the claim, so the
    ordinary assertions being made under a flagging reviewer is the assertion.
    """

    return ScriptedReview(
        PhotoReviewVerdict(
            decision=PhotoReviewDecision.FLAGGED,
            note="clip;m=test;p=deadbeef;c=0.1000;s=0.1000,0.2000",
        )
    )


async def test_a_flagged_photo_is_still_uploaded_and_still_readable(client) -> None:
    """Soft-warn, never hard-block — `docs/adr/0091`.

    The route answers 201 and the photo comes back, because a false reject stops
    a real player on their first day and that cost did not fall when the player
    card made the other side of the trade heavier.
    """

    headers = await _auth_headers(client, ALICE)

    response = await _upload(client, headers)

    assert response.status_code == 201, response.text
    photo_id = response.json()["photo_id"]
    assert (
        await client.get(f"/api/v1/photos/{photo_id}", headers=headers)
    ).status_code == 200


async def test_the_verdict_and_its_evidence_ride_on_the_stored_object(
    client, photo_storage
) -> None:
    # Beside the bytes rather than in a table of its own, and carrying the
    # numbers it was decided from — so a threshold chosen later is derivable
    # from the corpus rather than from a second inference run over it.
    headers = await _auth_headers(client, ALICE)

    await _upload(client, headers)

    stored = photo_storage.only_stored()
    assert stored.metadata[REVIEW_METADATA_KEY] == "flagged"
    assert stored.metadata[REVIEW_NOTE_METADATA_KEY].startswith("clip;")


async def test_the_response_says_nothing_about_the_verdict(client) -> None:
    """The client is told nothing, deliberately, and that is this ticket's
    boundary.

    The copy today states the on-court rule without claiming enforcement
    (`docs/adr/0091`). A soft warning is new copy and a `frontend_player/`
    change, so a flagged upload is byte-for-byte the same response as an allowed
    one until that ships — which is also what makes shipping the checker early
    change nothing a player experiences.
    """

    headers = await _auth_headers(client, ALICE)

    body = (await _upload(client, headers)).json()

    assert set(body) == {"photo_id", "url", "expires_at"}

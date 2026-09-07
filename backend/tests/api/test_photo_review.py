"""What a flagged photo does to the two endpoints: one word, and nothing else.

**The whole module runs with a reviewer that flags everything**, which is the
point rather than a setup detail — a flagged upload has to be the same 201, the
same readable photo and the same committable id as any other, because the check
soft-warns and never blocks (`docs/adr/0091`). What changed is that the response
now *says* what the reviewer concluded, so a client can put a sentence on the
tile; everything the verdict was computed from stays on the object.

Three assertions carry the contract, and each is a different way it could go
wrong. The verdict **crosses** on the upload — otherwise no client can warn about
anything. The note **does not** — it is the model, the prompt-set fingerprint and
the raw similarity vector, which is evidence for us and not a fact about the
player, and a confidence score on the wire is an invitation to a client that
renders one. And the read carries **`null` rather than `allowed`**, because *we
did not ask* and *we asked and it was fine* are different answers and only one of
them is about the photograph.

The rule that decides *flagged* is not here and could not usefully be: it is
arithmetic over similarity scores, asserted in
`tests/unit/test_photo_review_policy.py` with no HTTP, no container and no model.
"""

from __future__ import annotations

import pytest

from app.modules.player_profile.domain.photos import (
    REVIEW_METADATA_KEY,
    REVIEW_NOTE_METADATA_KEY,
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


async def test_the_upload_says_which_verdict_it_reached(client) -> None:
    """One new field, carrying a code and not a sentence (`docs/adr/0022`).

    The wording of the warning belongs to the client, in its own copy and its own
    language; what crosses is which of the two the reviewer concluded.
    """

    headers = await _auth_headers(client, ALICE)

    body = (await _upload(client, headers)).json()

    assert set(body) == {"photo_id", "url", "expires_at", "review"}
    assert body["review"] == "flagged"


async def test_the_evidence_stays_on_the_object_and_never_on_the_wire(
    client, photo_storage
) -> None:
    """The decision crosses; the numbers it was taken from do not.

    Asserted over the whole serialised body rather than over a named field,
    because the failure this guards against is a *new* field carrying the note —
    a confidence score somebody adds later because it was to hand. The stored
    note is asserted present in the same test, so this cannot pass by the
    reviewer having said nothing at all.
    """

    headers = await _auth_headers(client, ALICE)

    response = await _upload(client, headers)

    assert photo_storage.only_stored().metadata[REVIEW_NOTE_METADATA_KEY].startswith(
        "clip;"
    )
    assert "clip;" not in response.text
    assert "0.1000" not in response.text


async def test_the_read_carries_no_verdict_rather_than_an_allowed_one(client) -> None:
    """`null`, and it is not the same word as `allowed`.

    The read proves the photo exists and signs a URL; it does not look at what
    the store holds beside the bytes, which in every S3-compatible store is a
    request per object. A warning belongs to the moment a player *chose* a
    photograph, and a tile being restored is one they already kept — so the field
    is on the shared shape and populated by exactly one of the two routes
    (`PhotoResponse`).
    """

    headers = await _auth_headers(client, ALICE)
    photo_id = (await _upload(client, headers)).json()["photo_id"]

    body = (await client.get(f"/api/v1/photos/{photo_id}", headers=headers)).json()

    assert body["review"] is None

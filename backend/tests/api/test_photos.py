"""The two photo endpoints over HTTP, with the object store faked.

**No test here needs MinIO running.** `tests/conftest.py` overrides the storage
port with an in-memory adapter for every API test, which is this ticket's own
acceptance criterion rather than a convenience: a suite that is only green with
a container up is a suite CI cannot be trusted to run.

The transcoder is *not* faked, so what lands in the fake store is what would
land in a bucket — which is what lets the EXIF assertion below be made over HTTP
rather than only against the adapter.
"""

from __future__ import annotations

import io
from uuid import uuid4

import pytest
from PIL import ExifTags, Image

from app.modules.player_profile.domain.photos import MAX_UPLOAD_BYTES
from tests.unit import image_fixtures as fixtures

ALICE = {
    "email": "alice.photos@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "alice-photos",
    "adult_attested": True,
}
BOB = {
    "email": "bob.photos@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "bob-photos",
    "adult_attested": True,
}


async def _auth_headers(client, payload) -> dict[str, str]:
    await client.post("/api/v1/users", json=payload)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password1"]},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _upload(client, headers, data=None, media_type="image/jpeg"):
    return await client.post(
        "/api/v1/photos",
        content=fixtures.plain_jpeg() if data is None else data,
        headers={**headers, "Content-Type": media_type},
    )


# ---------------------------------------------------------------------------
# Upload, and read back
# ---------------------------------------------------------------------------


async def test_a_player_uploads_one_photo_and_gets_an_id_and_a_url(client) -> None:
    headers = await _auth_headers(client, ALICE)

    response = await _upload(client, headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["photo_id"]
    assert body["url"]
    assert body["expires_at"]
    # The ordinary photo is told it is ordinary. The suite's reviewer allows
    # everything, so this is the *shape* of the answer rather than a claim about
    # the rule — what a flagged one says is `tests/api/test_photo_review.py`'s.
    assert body["review"] == "allowed"


async def test_the_uploaded_photo_can_be_fetched_back(client) -> None:
    headers = await _auth_headers(client, ALICE)
    photo_id = (await _upload(client, headers)).json()["photo_id"]

    response = await client.get(f"/api/v1/photos/{photo_id}", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["photo_id"] == photo_id
    assert response.json()["url"]


async def test_reading_a_photo_twice_signs_a_fresh_url_each_time(client) -> None:
    # A URL is not an address. It expires, so re-reading has to re-sign rather
    # than hand back a cached string that may already be dead.
    headers = await _auth_headers(client, ALICE)
    photo_id = (await _upload(client, headers)).json()["photo_id"]

    first = await client.get(f"/api/v1/photos/{photo_id}", headers=headers)
    second = await client.get(f"/api/v1/photos/{photo_id}", headers=headers)

    assert first.json()["expires_at"] <= second.json()["expires_at"]


@pytest.mark.parametrize(
    "fixture_name",
    ["plain_jpeg", "png_with_alpha", "heic"],
)
async def test_every_accepted_format_uploads(client, fixture_name) -> None:
    headers = await _auth_headers(client, ALICE)
    media_types = {
        "plain_jpeg": "image/jpeg",
        "png_with_alpha": "image/png",
        "heic": "image/heic",
    }

    response = await _upload(
        client,
        headers,
        data=getattr(fixtures, fixture_name)(),
        media_type=media_types[fixture_name],
    )

    assert response.status_code == 201, response.text


async def test_a_content_type_with_a_charset_is_still_accepted(client) -> None:
    # An SDK may append parameters; they say nothing about what the bytes are.
    headers = await _auth_headers(client, ALICE)

    response = await _upload(client, headers, media_type="image/jpeg; charset=binary")

    assert response.status_code == 201, response.text


# ---------------------------------------------------------------------------
# What is actually stored
# ---------------------------------------------------------------------------


async def test_what_the_store_holds_carries_no_exif(client, photo_storage) -> None:
    """The whole reason bytes are re-encoded, asserted end to end.

    A phone writes its GPS position into a photo, and the product's privacy
    rules put a player's precise location in the row nobody ever sees.
    """

    headers = await _auth_headers(client, ALICE)
    original = fixtures.jpeg_with_gps_and_orientation()
    # The guard: the thing being uploaded really does carry what must not survive.
    assert Image.open(io.BytesIO(original)).getexif().get_ifd(ExifTags.IFD.GPSInfo)

    assert (await _upload(client, headers, data=original)).status_code == 201

    stored = photo_storage.only_stored()
    assert b"Exif\x00\x00" not in stored.image.data
    reopened = Image.open(io.BytesIO(stored.image.data))
    assert reopened.getexif().get_ifd(ExifTags.IFD.GPSInfo) == {}
    assert reopened.format == "JPEG"


async def test_the_store_is_asked_for_a_short_window(client, photo_storage) -> None:
    headers = await _auth_headers(client, ALICE)

    await _upload(client, headers)

    assert photo_storage.signed_windows == [5 * 60]


# ---------------------------------------------------------------------------
# Ownership
# ---------------------------------------------------------------------------


async def test_an_anonymous_caller_cannot_upload(client) -> None:
    response = await client.post(
        "/api/v1/photos",
        content=fixtures.plain_jpeg(),
        headers={"Content-Type": "image/jpeg"},
    )

    assert response.status_code == 401, response.text


async def test_an_anonymous_caller_cannot_read_a_photo(client) -> None:
    response = await client.get(f"/api/v1/photos/{uuid4()}")

    assert response.status_code == 401, response.text


async def test_another_players_photo_id_answers_not_found(client) -> None:
    alice = await _auth_headers(client, ALICE)
    photo_id = (await _upload(client, alice)).json()["photo_id"]
    bob = await _auth_headers(client, BOB)

    response = await client.get(f"/api/v1/photos/{photo_id}", headers=bob)

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "photo_not_found"


async def test_a_photo_that_never_existed_answers_not_found(client) -> None:
    headers = await _auth_headers(client, ALICE)

    response = await client.get(f"/api/v1/photos/{uuid4()}", headers=headers)

    assert response.status_code == 404
    assert response.json()["code"] == "photo_not_found"


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------


async def test_an_unaccepted_format_is_refused_by_code(client) -> None:
    headers = await _auth_headers(client, ALICE)

    response = await _upload(client, headers, media_type="image/gif")

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "unsupported_image_format"


async def test_bytes_that_are_not_an_image_are_refused_by_code(client) -> None:
    headers = await _auth_headers(client, ALICE)

    response = await _upload(client, headers, data=fixtures.not_an_image())

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "unreadable_image"


async def test_a_body_past_the_cap_is_refused(client) -> None:
    headers = await _auth_headers(client, ALICE)

    response = await _upload(client, headers, data=b"\x00" * (MAX_UPLOAD_BYTES + 1))

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "image_too_large"


async def test_a_chunked_body_past_the_cap_is_refused_while_it_arrives(
    client, photo_storage
) -> None:
    """The Content-Length check is a courtesy; this is the actual defence.

    A generator body sends no Content-Length at all, so the only thing that can
    stop it is the running total over the stream — which is what keeps an
    unbounded upload from being buffered to disk before anybody looks at it.
    """

    headers = await _auth_headers(client, ALICE)
    chunk = b"\x00" * (1024 * 1024)

    async def oversized():
        for _ in range(12):
            yield chunk

    response = await client.post(
        "/api/v1/photos",
        content=oversized(),
        headers={**headers, "Content-Type": "image/jpeg"},
    )

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "image_too_large"
    assert photo_storage.objects == {}


async def test_a_refused_upload_stores_nothing(client, photo_storage) -> None:
    headers = await _auth_headers(client, ALICE)

    await _upload(client, headers, data=fixtures.not_an_image())

    assert photo_storage.objects == {}

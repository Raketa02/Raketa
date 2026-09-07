"""The object-store adapter, exercised without an object store.

**Presigning is offline computation** — a signature over the request that would
be sent, not a round trip — so the part of this adapter with a decision in it is
fully testable with nothing running. That is worth using: it is where the
endpoint split lives, and the endpoint split is what makes a photo openable on a
phone.

What is *not* covered here, and cannot be from a laptop with no container: that
MinIO and S3 accept these signatures. ADR-0091 says as much in writing — S3
compatible is not S3, and the first deployment will find at least one difference
in presigned URL semantics, multipart edges or CORS.
"""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
from botocore.exceptions import ClientError

from app.kernel import InvariantViolated
from app.modules.player_profile.domain.photos import (
    PhotoRef,
    PhotoReviewDecision,
    decision_on_record,
    review_metadata,
    verdict_from_similarities,
)

from app.modules.player_profile.infrastructure.s3_photo_storage import (
    KEY_PREFIX,
    S3PhotoStorage,
    object_key_for,
    ref_from_object_key,
    photo_refs_in,
    reports_an_absent_object,
    stored_photos_in,
    user_metadata_in,
)

#: Confidently on-court, so the verdict below is one somebody really took.
ON_COURT = [0.9] * 5 + [0.1] * 8

ALICE = UUID("11111111-1111-1111-1111-111111111111")
BOB = UUID("22222222-2222-2222-2222-222222222222")
PHOTO = UUID("33333333-3333-3333-3333-333333333333")
REF = PhotoRef(owner_id=ALICE, photo_id=PHOTO)


def minio() -> S3PhotoStorage:
    """How `local` is wired: an internal endpoint and a different public one."""

    return S3PhotoStorage(
        bucket="raketa-player-photos",
        endpoint_url="http://minio:9000",
        public_endpoint_url="http://localhost:9000",
        region_name="us-east-1",
        access_key_id="raketa_photos",
        secret_access_key="raketa_photos_pwd",
    )


def aws() -> S3PhotoStorage:
    """How a deployed environment is wired: no endpoint override at all."""

    return S3PhotoStorage(
        bucket="raketa-player-photos",
        endpoint_url=None,
        public_endpoint_url=None,
        region_name="eu-north-1",
        access_key_id="key",
        secret_access_key="secret",
    )


# ---------------------------------------------------------------------------
# The endpoint split
# ---------------------------------------------------------------------------


async def test_a_url_is_signed_against_the_public_endpoint_not_the_internal_one() -> (
    None
):
    """`http://minio:9000` is a name only the compose network resolves.

    SigV4 signs the host, so a URL signed for the internal name is invalid at
    the external one — which is why signing has a client of its own. Get this
    wrong and every photo is a broken image on every device.
    """

    url = await minio().presigned_read_url(REF, valid_for_seconds=300)

    assert urlparse(url).netloc == "localhost:9000"
    assert "minio:9000" not in url


async def test_the_public_endpoint_falls_back_to_the_internal_one() -> None:
    # One endpoint configured is the ordinary case on a host-run uvicorn, where
    # MinIO is on localhost for both.
    storage = S3PhotoStorage(
        bucket="b",
        endpoint_url="http://localhost:9000",
        public_endpoint_url=None,
        region_name="us-east-1",
        access_key_id="k",
        secret_access_key="s",
    )

    url = await storage.presigned_read_url(REF, valid_for_seconds=300)

    assert urlparse(url).netloc == "localhost:9000"


async def test_the_deployed_wiring_is_the_same_class_with_no_endpoint() -> None:
    """ADR-0091's adapter swap, demonstrated rather than asserted in prose.

    The same class, one setting different, and the URL is AWS's own https
    endpoint. No code changes and no user data moves — which is the entire
    reason photos are not `bytea` in Postgres.
    """

    url = await aws().presigned_read_url(REF, valid_for_seconds=300)

    assert urlparse(url).scheme == "https"
    assert urlparse(url).netloc.endswith("amazonaws.com")
    assert "eu-north-1" in url


# ---------------------------------------------------------------------------
# What the URL grants
# ---------------------------------------------------------------------------


async def test_the_url_is_signed_and_carries_the_requested_window() -> None:
    url = await minio().presigned_read_url(REF, valid_for_seconds=300)

    query = parse_qs(urlparse(url).query)
    assert query["X-Amz-Expires"] == ["300"]
    assert query["X-Amz-Signature"]
    assert query["X-Amz-Algorithm"] == ["AWS4-HMAC-SHA256"]


async def test_the_url_addresses_this_players_key_and_no_other() -> None:
    url = await minio().presigned_read_url(REF, valid_for_seconds=300)

    assert object_key_for(ALICE, PHOTO) in urlparse(url).path


async def test_the_secret_is_never_in_the_url() -> None:
    # A presigned URL is handed to a device and ends up in logs, crash reports
    # and screenshots. The signature is derived from the secret; the secret
    # itself must not be in it.
    url = await minio().presigned_read_url(REF, valid_for_seconds=300)

    assert "raketa_photos_pwd" not in url


async def test_path_style_addressing_keeps_the_bucket_out_of_the_hostname() -> None:
    # Virtual-host style would resolve `raketa-player-photos.minio`, which is
    # not a name anything on the compose network answers to.
    url = await minio().presigned_read_url(REF, valid_for_seconds=300)

    assert urlparse(url).path.startswith("/raketa-player-photos/")


# ---------------------------------------------------------------------------
# Absent versus broken
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("code", ["404", "NoSuchKey", "NotFound"])
def test_the_stores_several_spellings_of_absent_are_all_read_as_absent(
    code: str,
) -> None:
    # MinIO and S3 do not agree on which of these `head_object` returns, so both
    # are read rather than one being trusted.
    error = ClientError({"Error": {"Code": code}}, "HeadObject")

    assert reports_an_absent_object(error)


@pytest.mark.parametrize(
    "code", ["AccessDenied", "NoSuchBucket", "InternalError", "SlowDown", ""]
)
def test_a_broken_store_is_never_reported_as_an_absent_photo(code: str) -> None:
    """The failure that would be invisible.

    Reading an outage as *not found* turns it into every player's photos
    silently vanishing — and it would make the profile commit refuse every photo
    id it was handed, for the duration, with a validation error rather than an
    error that says the store is down.
    """

    error = ClientError({"Error": {"Code": code}}, "HeadObject")

    assert not reports_an_absent_object(error)


# ---------------------------------------------------------------------------
# Reading a listing back — the half the sweep's deletes rest on (#142)
# ---------------------------------------------------------------------------


def test_a_key_this_adapter_wrote_reads_back_as_the_same_ref() -> None:
    """The round trip, which is the whole claim `ref_from_object_key` makes.

    Written against `object_key_for` rather than against a literal, so the two
    halves cannot drift apart while both look right on their own.
    """

    assert ref_from_object_key(object_key_for(ALICE, PHOTO)) == REF


def test_every_key_this_adapter_writes_is_under_the_prefix_the_sweep_lists() -> None:
    # If these disagreed the sweep would enumerate nothing and report a clean
    # bucket forever — a silent no-op, not a failure.
    assert object_key_for(ALICE, PHOTO).startswith(KEY_PREFIX)


@pytest.mark.parametrize(
    "key",
    [
        "players/",
        "players/not-a-uuid/photos/33333333-3333-3333-3333-333333333333.jpg",
        f"players/{ALICE}/photos/not-a-uuid.jpg",
        f"players/{ALICE}/photos/{PHOTO}.png",
        f"players/{ALICE}/avatars/{PHOTO}.jpg",
        f"players/{ALICE}/photos/nested/{PHOTO}.jpg",
        f"exports/{ALICE}/photos/{PHOTO}.jpg",
        "",
    ],
    ids=[
        "a folder marker",
        "an owner that is not a uuid",
        "a photo id that is not a uuid",
        "some other extension",
        "some other kind of object",
        "a deeper layout",
        "a different prefix entirely",
        "nothing at all",
    ],
)
def test_a_key_this_adapter_did_not_write_is_refused_rather_than_guessed(
    key: str,
) -> None:
    """**This function decides what a sweep may delete.**

    Anything that is not exactly the template's shape must come back `None`, so
    an object nobody can identify is left where it is. A parser that guessed
    here would be a parser that deletes somebody's data on a layout change.
    """

    assert ref_from_object_key(key) is None


def test_a_listing_page_becomes_the_photos_it_named() -> None:
    taken = datetime(2026, 8, 24, 9, 30, tzinfo=timezone.utc)
    page = [{"Key": object_key_for(ALICE, PHOTO), "LastModified": taken}]

    photos = list(stored_photos_in(page))

    assert [photo.ref for photo in photos] == [REF]
    assert photos[0].stored_at == taken


def test_entries_a_listing_page_holds_that_are_not_photos_are_skipped() -> None:
    """A bucket may hold objects this application did not write, and a page may
    describe an entry without a stamp. Neither is a candidate, and neither is an
    error — the sweep judges only what it can name."""

    taken = datetime(2026, 8, 24, 9, 30, tzinfo=timezone.utc)
    page = [
        {"Key": "players/", "LastModified": taken},
        {"Key": "some-other-tool/thing.bin", "LastModified": taken},
        {"Key": object_key_for(ALICE, PHOTO)},
        {"LastModified": taken},
        {"Key": object_key_for(BOB, PHOTO), "LastModified": taken},
    ]

    assert [photo.ref.owner_id for photo in stored_photos_in(page)] == [BOB]


def test_a_stamp_without_a_timezone_is_refused_rather_than_compared() -> None:
    """Every S3-compatible store returns an aware `LastModified`.

    If one ever does not, the value must not reach a comparison against the
    cutoff: a naive datetime read as UTC is wrong by an offset, and the wrong
    direction deletes a photo that is inside the window.
    """

    page = [
        {
            "Key": object_key_for(ALICE, PHOTO),
            "LastModified": datetime(2026, 8, 24, 9, 30),
        }
    ]

    with pytest.raises(InvariantViolated):
        list(stored_photos_in(page))


# ---------------------------------------------------------------------------
# What a HEAD says about a photo's review
# ---------------------------------------------------------------------------


def test_the_metadata_a_head_carries_is_read_back_as_it_was_written() -> None:
    # Lowercase because every S3-compatible store lowercases user metadata keys
    # on the way out, and the two this application writes are lowercase already.
    head = {"ContentType": "image/jpeg", "Metadata": {"review": "flagged"}}

    assert user_metadata_in(head) == {"review": "flagged"}


def test_an_object_carrying_no_metadata_reads_as_none_rather_than_raising() -> None:
    # Every photo from before the checker existed looks like this, and it is the
    # population the backfill is for — so it must be an answer, not an error.
    assert user_metadata_in({"ContentType": "image/jpeg"}) == {}
    assert user_metadata_in({"Metadata": None}) == {}


def test_a_heads_metadata_becomes_a_decision_a_card_may_draw() -> None:
    """The two pure halves of ``review_decision``, composed exactly as it
    composes them. The round trip itself is one ``head_object`` and is not
    faked here; what could go wrong silently is this pair.
    """

    verdict = verdict_from_similarities(model="clip-test", similarities=ON_COURT)
    head = {"ContentType": "image/jpeg", "Metadata": review_metadata(verdict)}

    assert decision_on_record(user_metadata_in(head)) is PhotoReviewDecision.ALLOWED


def test_a_head_from_the_pass_through_era_yields_no_decision() -> None:
    # `review: allowed` and nothing that proves anybody looked. It is the shape
    # every object stored before the checker landed still has, and a shield
    # drawn on it would be a claim about an image nothing scored.
    head = {"ContentType": "image/jpeg", "Metadata": {"review": "allowed"}}

    assert decision_on_record(user_metadata_in(head)) is None


def test_the_backfills_walk_reads_keys_and_never_a_stamp() -> None:
    # It asks what the metadata says, so a listing entry with no `LastModified`
    # — or a naive one, which the sweep refuses rather than compares — is not
    # its rule to inherit. The refusal it *does* share is the one that matters.
    page = [
        {"Key": object_key_for(ALICE, PHOTO)},
        {"Key": "players/not-a-uuid/photos/x.jpg"},
        {"Key": "players/"},
    ]

    assert list(photo_refs_in(page)) == [REF]

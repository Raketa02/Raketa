"""Reading a photo back: whose it is, and how long the answer lasts."""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.modules.player_profile.application.commands import GetPhotoCommand
from app.modules.player_profile.application.get_photo import GetPhoto
from app.modules.player_profile.domain.errors import PhotoNotFound
from app.modules.player_profile.domain.photos import PhotoRef, TranscodedImage
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import FrozenClock, utc
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

NOW = utc(2026, 8, 25)
URL_MINUTES = 5

AN_IMAGE = TranscodedImage(data=b"jpeg", media_type="image/jpeg", width=60, height=40)


def use_case(storage: InMemoryPhotoStorage) -> GetPhoto:
    return GetPhoto(
        storage=storage,
        clock=FrozenClock(at=NOW),
        url_valid_for_minutes=URL_MINUTES,
    )


async def stored(storage: InMemoryPhotoStorage, ref: PhotoRef) -> None:
    await storage.put(ref, AN_IMAGE, metadata={})


async def test_a_photo_the_player_owns_yields_a_signed_url() -> None:
    storage = InMemoryPhotoStorage()
    ref = PhotoRef(owner_id=new_uuid(), photo_id=new_uuid())
    await stored(storage, ref)

    presigned = await use_case(storage).execute(
        GetPhotoCommand(owner_id=ref.owner_id, photo_id=ref.photo_id)
    )

    assert presigned.url.startswith(InMemoryPhotoStorage.URL_PREFIX)
    assert storage.signed_windows == [URL_MINUTES * 60]


async def test_the_expiry_is_the_clock_plus_the_window() -> None:
    storage = InMemoryPhotoStorage()
    ref = PhotoRef(owner_id=new_uuid(), photo_id=new_uuid())
    await stored(storage, ref)

    presigned = await use_case(storage).execute(
        GetPhotoCommand(owner_id=ref.owner_id, photo_id=ref.photo_id)
    )

    assert presigned.expires_at == NOW + timedelta(minutes=URL_MINUTES)


async def test_a_photo_that_does_not_exist_is_not_found() -> None:
    storage = InMemoryPhotoStorage()

    with pytest.raises(PhotoNotFound):
        await use_case(storage).execute(
            GetPhotoCommand(owner_id=new_uuid(), photo_id=new_uuid())
        )


async def test_another_players_photo_is_the_same_answer_as_a_missing_one() -> None:
    """Not *forbidden* — *not found*.

    Distinguishing the two would make the endpoint an oracle: a caller could
    confirm that a photo id it guessed belongs to somebody, which is a fact
    about a stranger it has no business learning.
    """

    storage = InMemoryPhotoStorage()
    alice = PhotoRef(owner_id=new_uuid(), photo_id=new_uuid())
    await stored(storage, alice)
    bob = new_uuid()

    with pytest.raises(PhotoNotFound):
        await use_case(storage).execute(
            GetPhotoCommand(owner_id=bob, photo_id=alice.photo_id)
        )


async def test_existence_is_checked_before_a_url_is_signed() -> None:
    """Signing is pure computation, so an unchecked endpoint would hand back a
    working-looking URL for a photo that is not there — and the player would see
    a broken image rather than an error a client can act on.

    The fake signs whether or not the object exists, exactly as a real store
    does, which is what makes this assertable: nothing was signed at all.
    """

    storage = InMemoryPhotoStorage()

    with pytest.raises(PhotoNotFound):
        await use_case(storage).execute(
            GetPhotoCommand(owner_id=new_uuid(), photo_id=new_uuid())
        )

    assert storage.signed_windows == []

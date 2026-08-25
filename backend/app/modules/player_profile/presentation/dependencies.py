"""Request-scoped declarations for the Player profile context.

*When* each adapter is built and how long it lives, never *what* — every
concrete class comes from `app.bootstrap.composition`, and
`tests/unit/test_composition_root.py` fails this file if it imports one.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import ClockDep, SettingsDep
from app.bootstrap.composition import (
    build_image_transcoder,
    build_photo_review,
    build_photo_storage,
)
from app.modules.player_profile.application.get_photo import GetPhoto
from app.modules.player_profile.application.upload_photo import UploadPhoto
from app.modules.player_profile.domain.ports import (
    ImageTranscoder,
    PhotoReview,
    PhotoStorage,
)


def get_photo_storage(settings: SettingsDep) -> PhotoStorage:
    # Per request. The adapter holds credentials and a bucket name and no
    # connection, so a per-request instance costs a dataclass; what it buys is
    # that a test overrides one dependency and every route in this module is
    # talking to the fake.
    return build_photo_storage(settings)


PhotoStorageDep = Annotated[PhotoStorage, Depends(get_photo_storage)]


def get_image_transcoder() -> ImageTranscoder:
    return build_image_transcoder()


ImageTranscoderDep = Annotated[ImageTranscoder, Depends(get_image_transcoder)]


def get_photo_review() -> PhotoReview:
    return build_photo_review()


PhotoReviewDep = Annotated[PhotoReview, Depends(get_photo_review)]


def get_upload_photo(
    storage: PhotoStorageDep,
    transcoder: ImageTranscoderDep,
    review: PhotoReviewDep,
    clock: ClockDep,
    settings: SettingsDep,
) -> UploadPhoto:
    # No unit of work and no event publisher: an upload writes no row and emits
    # no domain event. It puts bytes somewhere and hands back an id, and the
    # profile commit is what makes that id mean something (`docs/adr/0091`).
    return UploadPhoto(
        storage=storage,
        transcoder=transcoder,
        review=review,
        clock=clock,
        url_valid_for_minutes=settings.PHOTO_URL_VALID_FOR_MINUTES,
    )


UploadPhotoDep = Annotated[UploadPhoto, Depends(get_upload_photo)]


def get_get_photo(
    storage: PhotoStorageDep,
    clock: ClockDep,
    settings: SettingsDep,
) -> GetPhoto:
    return GetPhoto(
        storage=storage,
        clock=clock,
        url_valid_for_minutes=settings.PHOTO_URL_VALID_FOR_MINUTES,
    )


GetPhotoDep = Annotated[GetPhoto, Depends(get_get_photo)]

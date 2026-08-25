"""Request-scoped declarations for the Player profile context.

*When* each adapter is built and how long it lives, never *what* — every
concrete class comes from `app.bootstrap.composition`, and
`tests/unit/test_composition_root.py` fails this file if it imports one.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_image_transcoder,
    build_photo_review,
    build_photo_storage,
    build_player_profile_repository,
)
from app.modules.player_profile.application.commit_player_profile import (
    CommitPlayerProfile,
)
from app.modules.player_profile.application.get_photo import GetPhoto
from app.modules.player_profile.application.has_player_profile import HasPlayerProfile
from app.modules.player_profile.application.upload_photo import UploadPhoto
from app.modules.player_profile.domain.ports import (
    ImageTranscoder,
    PhotoReview,
    PhotoStorage,
    PlayerProfileRepository,
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


def get_player_profile_repository(
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
) -> PlayerProfileRepository:
    # Per request, and it must be: it remembers the stream versions it read, and
    # one request's versions must never answer for another's.
    return build_player_profile_repository(event_store=event_store, events=events)


PlayerProfileRepositoryDep = Annotated[
    PlayerProfileRepository, Depends(get_player_profile_repository)
]


def get_commit_player_profile(
    profiles: PlayerProfileRepositoryDep,
    photos: PhotoStorageDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> CommitPlayerProfile:
    # The same `PhotoStorage` the upload route was given — FastAPI caches a
    # dependency for the life of a request, so the store that took the bytes is
    # the store the commit asks about them.
    return CommitPlayerProfile(profiles=profiles, photos=photos, uow=uow, clock=clock)


CommitPlayerProfileDep = Annotated[
    CommitPlayerProfile, Depends(get_commit_player_profile)
]


def get_has_player_profile(profiles: PlayerProfileRepositoryDep) -> HasPlayerProfile:
    # Declared here rather than in the users context that consumes it, because
    # *what* is built is this context's answer and this file is where its
    # request-scoped lifetimes are stated.
    return HasPlayerProfile(profiles=profiles)


HasPlayerProfileDep = Annotated[HasPlayerProfile, Depends(get_has_player_profile)]

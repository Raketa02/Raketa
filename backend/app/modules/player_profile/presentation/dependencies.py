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
    build_play_intent_declaration_repository,
    build_player_profile_repository,
)
from app.modules.player_profile.application.change_gender import ChangeGender
from app.modules.player_profile.application.change_gender_preference import (
    ChangeGenderPreference,
)
from app.modules.player_profile.application.change_intro import ChangeIntro
from app.modules.player_profile.application.change_location import ChangeLocation
from app.modules.player_profile.application.change_photos import ChangePhotos
from app.modules.player_profile.application.change_social_tags import (
    ChangeSocialTags,
)
from app.modules.player_profile.application.commit_player_profile import (
    CommitPlayerProfile,
)
from app.modules.player_profile.application.declare_play_intent import (
    DeclarePlayIntent,
)
from app.modules.player_profile.application.get_photo import GetPhoto
from app.modules.player_profile.application.has_player_profile import HasPlayerProfile
from app.modules.player_profile.application.read_player_profile import (
    ReadPlayerProfile,
)
from app.modules.player_profile.application.set_weekly_hours import SetWeeklyHours
from app.modules.player_profile.application.upload_photo import UploadPhoto
from app.modules.player_profile.domain.ports import (
    ImageTranscoder,
    PhotoReview,
    PhotoStorage,
    PlayerProfileRepository,
    PlayIntentDeclarationRepository,
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


def get_photo_review(settings: SettingsDep) -> PhotoReview:
    # Per request, like the store beside it: the adapter holds a URL and a
    # timeout and no connection, and an HTTP session is opened per review for
    # the reason the object store opens a client per call — an `aiohttp` session
    # binds to the loop it was made on.
    return build_photo_review(settings)


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


def get_play_intent_declaration_repository(
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
) -> PlayIntentDeclarationRepository:
    # Per request, for the reason the profile's is: it remembers the stream
    # versions it read. Declared here rather than in the matchmaking module that
    # first reads one, because *where a declaration comes from* is this
    # context's answer to give.
    return build_play_intent_declaration_repository(
        event_store=event_store, events=events
    )


PlayIntentDeclarationRepositoryDep = Annotated[
    PlayIntentDeclarationRepository, Depends(get_play_intent_declaration_repository)
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


def get_read_player_profile(
    profiles: PlayerProfileRepositoryDep,
    declarations: PlayIntentDeclarationRepositoryDep,
    photos: PhotoStorageDep,
) -> ReadPlayerProfile:
    # Both repositories, because the read spans both of this context's
    # aggregates — which is the join ADR-0090's precedent makes cheap, one
    # context lower than where that record made it. And the store, because the
    # verdict beside each photograph is metadata on the object and lives
    # nowhere else (``docs/adr/0179`` §8).
    return ReadPlayerProfile(
        profiles=profiles, declarations=declarations, photos=photos
    )


ReadPlayerProfileDep = Annotated[ReadPlayerProfile, Depends(get_read_player_profile)]


def get_set_weekly_hours(
    profiles: PlayerProfileRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SetWeeklyHours:
    # No photo storage: a week has nothing to re-validate against an object
    # store, which is the difference between an edit and the creating commit.
    return SetWeeklyHours(profiles=profiles, uow=uow, clock=clock)


SetWeeklyHoursDep = Annotated[SetWeeklyHours, Depends(get_set_weekly_hours)]


def get_change_location(
    profiles: PlayerProfileRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ChangeLocation:
    # The same three the week takes: the cell is a fact on the profile's own
    # stream and nothing else is told, because the projection follows the
    # event it has always followed (`docs/adr/0174` §6).
    return ChangeLocation(profiles=profiles, uow=uow, clock=clock)


ChangeLocationDep = Annotated[ChangeLocation, Depends(get_change_location)]


def get_change_social_tags(
    profiles: PlayerProfileRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ChangeSocialTags:
    # The three every preference edit takes: the vocabulary and the bounds are
    # the domain's, so there is nothing to re-validate against a store.
    return ChangeSocialTags(profiles=profiles, uow=uow, clock=clock)


ChangeSocialTagsDep = Annotated[ChangeSocialTags, Depends(get_change_social_tags)]


def get_change_photos(
    profiles: PlayerProfileRepositoryDep,
    photos: PhotoStorageDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ChangePhotos:
    # The store as well, for the commit's reason: every id is proved to exist
    # and to be the caller's against the same port the upload used.
    return ChangePhotos(profiles=profiles, photos=photos, uow=uow, clock=clock)


ChangePhotosDep = Annotated[ChangePhotos, Depends(get_change_photos)]


def get_change_intro(
    profiles: PlayerProfileRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ChangeIntro:
    return ChangeIntro(profiles=profiles, uow=uow, clock=clock)


ChangeIntroDep = Annotated[ChangeIntro, Depends(get_change_intro)]


def get_change_gender(
    profiles: PlayerProfileRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ChangeGender:
    return ChangeGender(profiles=profiles, uow=uow, clock=clock)


ChangeGenderDep = Annotated[ChangeGender, Depends(get_change_gender)]


def get_change_gender_preference(
    profiles: PlayerProfileRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ChangeGenderPreference:
    return ChangeGenderPreference(profiles=profiles, uow=uow, clock=clock)


ChangeGenderPreferenceDep = Annotated[
    ChangeGenderPreference, Depends(get_change_gender_preference)
]


def get_declare_play_intent(
    declarations: PlayIntentDeclarationRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> DeclarePlayIntent:
    # The declaration repository alone: the profile is a different aggregate on
    # a different stream, and a declaration neither reads nor writes one.
    return DeclarePlayIntent(declarations=declarations, uow=uow, clock=clock)


DeclarePlayIntentDep = Annotated[DeclarePlayIntent, Depends(get_declare_play_intent)]

"""Who a record says somebody is, and the one word it borrows without importing.

``player_record`` declares its own types rather than reusing another context's
(``docs/adr/0155``), which puts two enums with the same two strings one directory
apart. That is deliberate — a record is not a card and must not inherit a card's
closed list — and the risk it carries is equally deliberate: **two spellings that
drift are worse than an import**, because a client reading a search card and a
record would be handed two words for one fact. So the agreement is asserted, in
both directions, the way ``games_match_history`` asserts its two bounds against
each other.
"""

from __future__ import annotations

from typing import Collection, Mapping
from uuid import UUID, uuid4

from app.modules.player_profile.domain.photos import (
    PhotoRef,
    PhotoReviewDecision,
)
from app.modules.player_record.domain.record import OnCourtVerdict
from app.modules.player_record.infrastructure.subject_identities import (
    ProfileAndAccountIdentity,
)

SUBJECT = uuid4()
PHOTO = uuid4()


def test_the_two_verdict_vocabularies_agree_on_the_wire():
    """Both directions, so a value added to either side is red rather than a
    third answer arriving on one surface and not the other."""

    assert {one.value for one in OnCourtVerdict} == {
        one.value for one in PhotoReviewDecision
    }


class Users:
    def __init__(self, nicknames: Mapping[UUID, str]) -> None:
        self.nicknames = dict(nicknames)

    async def find_nicknames_of(
        self, user_ids: Collection[UUID]
    ) -> Mapping[UUID, str]:
        return {
            player_id: self.nicknames[player_id]
            for player_id in user_ids
            if player_id in self.nicknames
        }


class Area:
    latitude = 51.51
    longitude = -0.13


class Tags:
    ids = ("PLAYS_TO_WIN", "HERE_TO_IMPROVE")


class Profile:
    def __init__(self, photo_ids: tuple[UUID, ...]) -> None:
        self.photo_ids = photo_ids
        self.location = Area()
        self.social_tags = Tags()


class Profiles:
    def __init__(self, profile: Profile | None) -> None:
        self.profile = profile

    async def load(self, player_id: UUID) -> Profile | None:
        return self.profile


class Photos:
    def __init__(self, decision: PhotoReviewDecision | None) -> None:
        self.decision = decision
        self.asked: list[PhotoRef] = []

    async def review_decision(self, ref: PhotoRef) -> PhotoReviewDecision | None:
        self.asked.append(ref)
        return self.decision


def identity_source(
    *,
    nickname: str | None = "Karol T.",
    photo_ids: tuple[UUID, ...] = (PHOTO,),
    profile: bool = True,
    decision: PhotoReviewDecision | None = PhotoReviewDecision.ALLOWED,
    photos: Photos | None = None,
) -> ProfileAndAccountIdentity:
    return ProfileAndAccountIdentity(
        users=Users({} if nickname is None else {SUBJECT: nickname}),
        profiles=Profiles(Profile(photo_ids) if profile else None),
        photos=photos or Photos(decision),
    )


async def test_an_identity_is_the_handle_the_first_photo_and_where_they_are():
    identity = await identity_source().identity_of(SUBJECT)

    assert identity is not None
    assert identity.nickname == "Karol T."
    assert identity.photo_id == PHOTO
    assert identity.review is OnCourtVerdict.ALLOWED
    assert identity.social_tags == ("PLAYS_TO_WIN", "HERE_TO_IMPROVE")
    # **The code is derived and never spelled here**: one function on this
    # platform turns a coarse area into one, because two would be two answers to
    # *are we in the same area*.
    assert identity.area_code == "A+05151-000013"


async def test_the_photograph_a_record_shows_is_the_first_one():
    """Order is meaning in a player's photo list, and the verdict is asked about
    **that** photograph rather than about the player."""

    second = uuid4()
    photos = Photos(PhotoReviewDecision.FLAGGED)

    identity = await identity_source(
        photo_ids=(PHOTO, second), photos=photos
    ).identity_of(SUBJECT)

    assert identity is not None and identity.photo_id == PHOTO
    assert photos.asked == [PhotoRef(owner_id=SUBJECT, photo_id=PHOTO)]


async def test_a_player_with_no_photograph_is_asked_nothing_about_one():
    photos = Photos(PhotoReviewDecision.ALLOWED)

    identity = await identity_source(photo_ids=(), photos=photos).identity_of(
        SUBJECT
    )

    assert identity is not None
    assert identity.photo_id is None and identity.review is None
    assert photos.asked == []


async def test_nobody_looked_is_an_absence_and_never_a_third_value():
    """A shield says *checked and passed*; only a decision the stored note proves
    earns one (``docs/adr/0138``)."""

    identity = await identity_source(decision=None).identity_of(SUBJECT)

    assert identity is not None
    assert identity.photo_id == PHOTO and identity.review is None


async def test_a_player_the_platform_cannot_describe_is_nobody():
    """Two absences, one answer — a handle that cannot be read and a profile
    never committed. The caller refuses either way, in the one shape it has."""

    assert await identity_source(nickname=None).identity_of(SUBJECT) is None
    assert await identity_source(profile=False).identity_of(SUBJECT) is None

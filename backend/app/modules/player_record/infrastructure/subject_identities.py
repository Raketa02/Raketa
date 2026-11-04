"""Who a person is, from the two contexts that own the answer.

``SubjectIdentitySource`` over ``users`` and the Player profile — the same three
providers a player card is assembled from, asked about **one** person instead of
twenty. It reads each provider's own port and never their tables: a ``select``
over ``UserORM``, or a walk over the profile streams in ``event_store``, would
make this context a second reader of somebody else's schema, and the second is
worse than the first because it would also be a second implementation of how a
profile is folded.

**One profile fold answers four of the six fields.** The photograph, the area,
the tag selection and the intro are all on the aggregate, so this is one stream
read rather than four ports asked separately — which is why the identity is one
demand here and not two split by provider. ``docs/adr/0098`` files a port by
*who supplies the fact*; a fact supplied by one fold is one port.

**The area code is derived by the one function that derives it**, and never
re-spelled here. It lives in ``matchmaking`` because the player card was the
first surface to need one; two implementations of *which square is this* would be
two answers to *are we in the same area*, which is the only sentence a code
licenses a client to say. Where that function ought to finally live is a move
that touches the matcher's own fence and is not this ticket's.

**The verdict is translated rather than passed through.** ``PhotoReviewDecision``
is ``player_profile``'s word and ``OnCourtVerdict`` is this context's; they carry
the same two strings deliberately, because a client reading a photo on a profile
and on a record must not be handed two spellings of one fact.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.matchmaking.domain.areas import area_code_of
from app.modules.matchmaking.domain.geography import Point
from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
    PlayerProfileRepository,
)
from app.modules.player_record.domain.record import (
    OnCourtVerdict,
    SubjectIdentity,
)
from app.modules.users.domain.ports import UserRepository


@final
class ProfileAndAccountIdentity:
    """``SubjectIdentitySource`` over the account, the profile and the photo store."""

    def __init__(
        self,
        *,
        users: UserRepository,
        profiles: PlayerProfileRepository,
        photos: PhotoStorage,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._photos = photos

    async def identity_of(self, player_id: UUID) -> SubjectIdentity | None:
        """Their nickname, first photograph, its verdict, area, tags and intro.

        **Two absences, one answer.** A nickname this platform cannot read — an
        id it never issued, or an account with none yet — and a profile that was
        never committed both mean *there is nobody here to describe*, and the
        caller refuses either way — the record is not a route that can afford to
        distinguish an id nobody was issued from one that was.

        A missing **photograph** is an ordinary state and not an absence to
        report: the client draws the generated court poster. So is a missing
        **verdict**, and for one reason more than the photograph has — the image
        may have arrived while the checker could not be reached, or before it
        existed at all (``docs/adr/0138``).
        """

        nickname = (await self._users.find_nicknames_of([player_id])).get(player_id)
        if nickname is None:
            return None
        profile = await self._profiles.load(player_id)
        if profile is None:
            return None

        # **The first photo, because order is meaning in a player's photo list.**
        photo_id = profile.photo_ids[0] if profile.photo_ids else None
        decision = (
            None
            if photo_id is None
            else await self._photos.review_decision(
                PhotoRef(owner_id=player_id, photo_id=photo_id)
            )
        )
        return SubjectIdentity(
            nickname=nickname,
            photo_id=photo_id,
            review=None if decision is None else OnCourtVerdict(decision.value),
            area_code=area_code_of(
                Point(
                    latitude=profile.location.latitude,
                    longitude=profile.location.longitude,
                )
            ),
            social_tags=profile.social_tags.ids,
            # The text and never the value object — this context's own type
            # holds a `str`, and a missing line is `None` all the way out.
            intro=None if profile.intro is None else profile.intro.text,
        )


__all__ = ["ProfileAndAccountIdentity"]

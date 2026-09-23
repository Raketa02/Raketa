"""``MemberFaces`` — a name from ``users``, a face from the Player profile.

**It reads each provider's own port and never their table or their bucket.** The
name comes from ``users``, which owns what an account is called — and the
nickname it answers beside it is left here, because a handle is drawn on a record
and said nowhere (``docs/adr/0171`` §4); the photo id
comes from the profile, which owns which photograph a person leads with; and the
link is signed by ``PhotoStorage``, which owns where the bytes live. A key
template written here would make this context a second implementation of that,
and the two would disagree the day the layout changed.

**Signing is arithmetic, not a request** (``docs/adr/0107``). Presigning is a
signature over a request that is never sent, so a whole list of rooms costs **no
round trips** — which is what makes minting per response affordable and why the
record goes on storing an id rather than a link that dies within the hour.

**And it never asks whether the object is still there.** That would be a round
trip per member before the response, to turn a photo removed since into a poster;
the link expires in minutes in any case, and a client that cannot survive an
image failing to load is already broken on the photograph it can see.

**Two loops, and the asymmetry is the reason they are written apart.** Profiles
are folded through the request's own session, which is not safe to use
concurrently, so they are read one after another; the signatures share nothing and
are pure computation, so they are not round trips to serialise in the first place.

**A player ``users`` cannot name keeps their membership**, with ``name``
``None`` on the way out — the opposite of a shortlist, which drops a row it
cannot name, and ``games``' rule verbatim: dropping one would draw a
three-person doubles court.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.modules.conversations.domain.ports import MemberFace
from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
    PlayerProfileRepository,
)
from app.modules.users.domain.ports import UserRepository


@final
class ProfileMemberFaces:
    """What each member is called, and the address of the photograph they lead with."""

    def __init__(
        self,
        *,
        users: UserRepository,
        profiles: PlayerProfileRepository,
        photos: PhotoStorage,
        photo_link_minutes: int,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._photos = photos
        self._photo_link_minutes = photo_link_minutes

    async def faces_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, MemberFace]:
        wanted = sorted(set(player_ids))
        if not wanted:
            return {}

        namings = await self._users.find_namings_of(wanted)
        photos = {player_id: await self._first_photo(player_id) for player_id in wanted}

        faces: dict[UUID, MemberFace] = {}
        for player_id in wanted:
            naming = namings.get(player_id)
            photo_id = photos[player_id]
            url = (
                None
                if photo_id is None
                else await self._photos.presigned_read_url(
                    PhotoRef(owner_id=player_id, photo_id=photo_id),
                    valid_for_seconds=self._photo_link_minutes * 60,
                )
            )
            faces[player_id] = MemberFace(
                player_id=player_id,
                name=None if naming is None else naming.name,
                photo_id=None if url is None else photo_id,
                photo_url=url,
            )
        return faces

    async def _first_photo(self, player_id: UUID) -> UUID | None:
        """The photograph a face shows — **the first**, because order is meaning
        in a player's photo list.

        ``None`` when they have none, which is not an absence to report: a player
        with no photograph draws a generated court poster, which needs nothing
        from the wire.
        """

        profile = await self._profiles.load(player_id)
        if profile is None or not profile.photo_ids:
            return None
        return profile.photo_ids[0]

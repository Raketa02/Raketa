"""``DeckPeople`` — a nickname from ``users``, a face and a week from the Player
profile, a Level from rating.

The groups' ``ProfileGroupFaces`` one context over, for the reason that port
gives for being a spelling of its own: it reads **each provider's own port** and
never its table or its bucket. The **nickname**, whole
(``docs/adr/0199`` §1); the **first** photograph, since order is meaning in a
player's photo list; the **published** Level — the figure a rating route already
prints — so a card cannot show a number the person's own record does not; and
the weekly hours the card's overlap grid summarises.

**One set read per provider over the union of every card**, and one profile
stream per person, sorted so the reads run in the same order on every process
(``docs/adr/0105``). Signing a photo link is arithmetic, not a request
(``docs/adr/0107``).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.kernel import Sport
from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
    PlayerProfileRepository,
)
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.ports import DeckPerson
from app.modules.rating.domain.ports import RatedPlayerQuery
from app.modules.users.domain.ports import UserRepository


@final
class ProfileDeckPeople:
    def __init__(
        self,
        *,
        users: UserRepository,
        profiles: PlayerProfileRepository,
        photos: PhotoStorage,
        ratings: RatedPlayerQuery,
        photo_link_minutes: int,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._photos = photos
        self._ratings = ratings
        self._photo_link_minutes = photo_link_minutes

    async def people(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, DeckPerson]:
        wanted = sorted(set(player_ids))
        if not wanted:
            return {}
        nicknames = await self._users.find_nicknames_of(wanted)
        published = await self._ratings.published_for(wanted, sport=sport)
        people: dict[UUID, DeckPerson] = {}
        for player_id in wanted:
            profile = await self._profiles.load(player_id)
            photo_id = (
                profile.photo_ids[0]
                if profile is not None and profile.photo_ids
                else None
            )
            url = (
                None
                if photo_id is None
                else await self._photos.presigned_read_url(
                    PhotoRef(owner_id=player_id, photo_id=photo_id),
                    valid_for_seconds=self._photo_link_minutes * 60,
                )
            )
            rating = published.get(player_id)
            people[player_id] = DeckPerson(
                nickname=nicknames.get(player_id),
                photo_id=None if url is None else photo_id,
                photo_url=url,
                level=None if rating is None else rating.mu,
                week=profile.weekly_hours
                if profile is not None
                else WeeklyHours.blank(),
            )
        return people

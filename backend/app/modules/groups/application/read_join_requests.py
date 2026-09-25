from __future__ import annotations

from uuid import UUID

from app.modules.groups.application.views import RequestCard
from app.modules.groups.domain.errors import GroupNotFound, NotTheGroupOwner
from app.modules.groups.domain.ports import (
    GroupDirectory,
    GroupFace,
    GroupFaces,
    RatedGroupMembers,
)


class ReadJoinRequests:
    """The Join requests waiting on a group, **for its Owner and nobody else**
    (#505) — *Want to join · N* on the Info tab, in the order people asked.

    A stranger meets ``group_not_found``, as the group's page refuses them —
    the person waiting included, who is not in it yet. A member who is not the
    Owner meets ``not_the_group_owner``: they know the group exists, and only
    who asked is withheld from them.

    Two reads whatever the length of the queue: every asker's face, and every
    sport each is rated in with its Level.
    """

    def __init__(
        self,
        *,
        directory: GroupDirectory,
        faces: GroupFaces,
        ratings: RatedGroupMembers,
    ) -> None:
        self._directory = directory
        self._faces = faces
        self._ratings = ratings

    async def execute(
        self, group_id: UUID, *, reader_id: UUID
    ) -> tuple[RequestCard, ...]:
        listing = (await self._directory.listings([group_id])).get(group_id)
        if listing is None or reader_id not in listing.members:
            raise GroupNotFound()
        if listing.owner_id != reader_id:
            raise NotTheGroupOwner()

        faces = await self._faces.faces_of(listing.waiting)
        levels = await self._ratings.levels_of(listing.waiting)
        return tuple(
            RequestCard(
                face=faces.get(player_id, GroupFace(player_id=player_id)),
                levels=levels.get(player_id, ()),
            )
            for player_id in listing.waiting
        )

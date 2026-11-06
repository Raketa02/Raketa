"""Friends' ``ReadersGroups``, **signed here** over the groups' own directory, so
the arrow runs ``groups → friends`` and Friends imports no group
(``.importlinter``) — as clubs' sports question and administrators' groups
question are signed here."""

from __future__ import annotations

from uuid import UUID

from app.modules.friends.domain.ports import ReadersGroup
from app.modules.groups.domain.ports import GroupDirectory


class DirectoryReadersGroups:
    def __init__(self, directory: GroupDirectory) -> None:
        self._directory = directory

    async def groups_of(self, reader: UUID) -> tuple[ReadersGroup, ...]:
        ids = list(await self._directory.groups_of(reader))
        if not ids:
            return ()
        listings = await self._directory.listings(ids)
        return tuple(
            ReadersGroup(
                group_id=listing.id,
                name=listing.name.value,
                members=listing.members,
            )
            for group_id in ids
            if (listing := listings.get(group_id)) is not None
        )

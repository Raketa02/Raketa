"""``OfficialGroupAssignments``, answered by the Groups context — what the
club's Administrators table asks of it, which groups each person runs (#510),
and what an account's profiles ask: which groups were handed to them without
their having been told (``docs/adr/0192``).

**The demand is administrators' and the signature is here**, as clubs'
``OfficialGroupSports`` is: ``groups`` already reads ``administrators``, and an
adapter living there would point the arrow back the other way. It reads this
context's own directory and answers **whom each official group names**, whether
or not that administratorship is still active — which is the demanding
context's to decide.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from uuid import UUID

from app.modules.administrators.domain.ports import AssignedGroup, HandedGroup
from app.modules.groups.domain.ports import GroupDirectory


class GroupsOfficialGroupAssignments:
    def __init__(self, directory: GroupDirectory) -> None:
        self._directory = directory

    async def assigned_at(self, club_id: UUID) -> Sequence[AssignedGroup]:
        return [
            AssignedGroup(
                id=listing.id,
                name=listing.name.value,
                administrator_id=listing.administrator_id,
            )
            for listing in await self._directory.official_at(club_id)
            if listing.administrator_id is not None
        ]

    async def handed_untold(
        self, administrator_ids: Collection[UUID]
    ) -> Sequence[HandedGroup]:
        # One read per administratorship: an account runs a club or two.
        return [
            HandedGroup(
                id=listing.id,
                name=listing.name.value,
                administrator_id=administrator_id,
                handed_over_at=listing.handed_over_at,
                waiting_count=len(listing.waiting),
            )
            for administrator_id in administrator_ids
            for listing in await self._directory.run_by(administrator_id)
            if listing.handed_over_at is not None
        ]

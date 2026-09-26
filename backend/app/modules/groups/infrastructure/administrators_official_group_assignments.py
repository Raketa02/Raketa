"""``OfficialGroupAssignments``, answered by the Groups context — the one thing
the club's Administrators table asks of it: which groups each person runs (#510).

**The demand is administrators' and the signature is here**, as clubs'
``OfficialGroupSports`` is: ``groups`` already reads ``administrators``, and an
adapter living there would point the arrow back the other way. It reads this
context's own directory and answers **whom each official group names**, whether
or not that administratorship is still active — which is the demanding
context's to decide.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from app.modules.administrators.domain.ports import AssignedGroup
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

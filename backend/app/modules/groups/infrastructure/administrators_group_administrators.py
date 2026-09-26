"""``GroupAdministrators`` over the administrators' own directory.

**It reads ``AdministratorDirectory`` and never the ``administrators`` table**:
what makes an administratorship active is that context's business — its states,
its expiry, its removal — and a second reader of its schema would be a second
opinion about all three.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID

from app.modules.administrators.domain.ports import AdministratorDirectory
from app.modules.groups.domain.ports import RunningAdministrator


class AdministratorsGroupAdministrators:
    def __init__(self, directory: AdministratorDirectory) -> None:
        self._directory = directory

    async def running(
        self, administrator_ids: Collection[UUID]
    ) -> Mapping[UUID, RunningAdministrator]:
        active = await self._directory.active_among(administrator_ids)
        return {
            listing.id: RunningAdministrator(
                account_id=listing.account_id, name=listing.name
            )
            for listing in active
            if listing.account_id is not None
        }

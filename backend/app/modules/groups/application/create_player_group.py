from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.groups.application.commands import CreatePlayerGroupCommand
from app.modules.groups.domain.errors import HomeClubUnknown
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.ports import (
    GroupCodeMinter,
    GroupRepository,
    HomeClubs,
)
from app.modules.groups.domain.value_objects import GroupName
from app.shared.ids import new_uuid


class CreatePlayerGroup:
    """A player creates a group at a home club and becomes its Owner and first
    member (``docs/adr/0183`` §2).

    **Refused in the form's order** — the name, then the home club — so the
    first refusal a player meets is the first field they would read down to. The
    code is minted last, once there is a group to give it to.
    """

    def __init__(
        self,
        *,
        groups: GroupRepository,
        clubs: HomeClubs,
        codes: GroupCodeMinter,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._groups = groups
        self._clubs = clubs
        self._codes = codes
        self._uow = uow
        self._clock = clock

    async def execute(self, command: CreatePlayerGroupCommand) -> UUID:
        name = GroupName(command.name)
        if command.home_club_id not in await self._clubs.by_id([command.home_club_id]):
            raise HomeClubUnknown()

        group = Group.create_player_group(
            group_id=new_uuid(),
            name=name,
            home_club_id=command.home_club_id,
            join_policy=command.join_policy,
            owner_id=command.creator_id,
            code=await self._codes.mint(),
            occurred_at=self._clock.now(),
        )
        await self._groups.save(group)
        await self._uow.commit()
        return group.id

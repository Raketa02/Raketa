from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.groups.application.commands import JoinGroupCommand
from app.modules.groups.application.views import (
    GroupAtClub,
    account_running,
    at_clubs,
)
from app.modules.groups.domain.errors import GroupNotFound
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.ports import (
    GroupAdministrators,
    GroupDirectory,
    GroupFaces,
    GroupRepository,
    RatedGroupMembers,
)
from app.modules.groups.domain.value_objects import GroupKind


class JoinGroup:
    """A player taps *Join* or *Ask to join* (``docs/adr/0183`` §7) — one tap,
    and the group's policy decides what it was.

    Under *Anyone* they are a member at once; under *People I approve* their
    Join request waits for whoever answers. Neither is recorded twice. **The
    account running an official group joins it directly**, whatever its policy
    — asked of the administrators on this tap, so a club's removal of that
    account is already in force (``docs/adr/0184`` §7). **Answers the group as
    the tap left it** — the row a search card draws, with the reader's relation
    — so the card turns into *you're in* or *requested · waiting* from the
    answer rather than from a second read.
    """

    def __init__(
        self,
        *,
        groups: GroupRepository,
        directory: GroupDirectory,
        ratings: RatedGroupMembers,
        faces: GroupFaces,
        administrators: GroupAdministrators,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._groups = groups
        self._directory = directory
        self._ratings = ratings
        self._faces = faces
        self._administrators = administrators
        self._uow = uow
        self._clock = clock

    async def execute(self, command: JoinGroupCommand) -> GroupAtClub:
        group = await self._groups.load(command.group_id)
        if group is None:
            raise GroupNotFound()
        group.join(
            command.player_id,
            occurred_at=self._clock.now(),
            runs_it=await self._runs_it(group, command.player_id),
        )
        await self._groups.save(group)
        await self._uow.commit()

        listing = (await self._directory.listings([group.id]))[group.id]
        rows = await at_clubs(
            [listing],
            reader_id=command.player_id,
            ratings=self._ratings,
            faces=self._faces,
            administrators=self._administrators,
        )
        return rows[listing.id]

    async def _runs_it(self, group: Group, player_id: UUID) -> bool:
        """Whether this account runs the group now — never asked of a player
        group, which no Administrator runs."""

        if group.kind is not GroupKind.OFFICIAL or group.administrator_id is None:
            return False
        return (
            await account_running(self._administrators, group.administrator_id)
            == player_id
        )

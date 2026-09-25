from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.groups.application.commands import JoinGroupCommand
from app.modules.groups.application.views import GroupAtClub, at_clubs
from app.modules.groups.domain.errors import GroupNotFound
from app.modules.groups.domain.ports import (
    GroupDirectory,
    GroupFaces,
    GroupRepository,
    RatedGroupMembers,
)


class JoinGroup:
    """A player taps *Join* or *Ask to join* (``docs/adr/0183`` §7) — one tap,
    and the group's policy decides what it was.

    Under *Anyone* they are a member at once; under *People I approve* their
    Join request waits for the Owner. Neither is recorded twice. **Answers the
    group as the tap left it** — the row a search card draws, with the reader's
    relation — so the card turns into *you're in* or *requested · waiting* from
    the answer rather than from a second read.
    """

    def __init__(
        self,
        *,
        groups: GroupRepository,
        directory: GroupDirectory,
        ratings: RatedGroupMembers,
        faces: GroupFaces,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._groups = groups
        self._directory = directory
        self._ratings = ratings
        self._faces = faces
        self._uow = uow
        self._clock = clock

    async def execute(self, command: JoinGroupCommand) -> GroupAtClub:
        group = await self._groups.load(command.group_id)
        if group is None:
            raise GroupNotFound()
        group.join(command.player_id, occurred_at=self._clock.now())
        await self._groups.save(group)
        await self._uow.commit()

        listing = (await self._directory.listings([group.id]))[group.id]
        rows = await at_clubs(
            [listing],
            reader_id=command.player_id,
            ratings=self._ratings,
            faces=self._faces,
        )
        return rows[listing.id]

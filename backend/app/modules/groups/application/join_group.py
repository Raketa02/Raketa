from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.groups.application.commands import JoinGroupCommand
from app.modules.groups.application.views import GroupAtClub, at_club, rated_among
from app.modules.groups.domain.errors import GroupNotFound
from app.modules.groups.domain.ports import (
    GroupDirectory,
    GroupRepository,
    RatedGroupMembers,
)


class JoinGroup:
    """A player taps *Join* (``docs/adr/0183`` §7).

    Under *Anyone* they are a member at once; joining twice changes nothing.
    **Answers the group as the tap left it** — the row a search card draws,
    with the reader's relation — so the card turns into *you're in* from the
    answer rather than from a second read.
    """

    def __init__(
        self,
        *,
        groups: GroupRepository,
        directory: GroupDirectory,
        ratings: RatedGroupMembers,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._groups = groups
        self._directory = directory
        self._ratings = ratings
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
        rated = await rated_among(self._ratings, [listing])
        return at_club(listing, rated, command.player_id)

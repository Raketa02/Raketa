from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.groups.application.commands import LeaveGroupCommand
from app.modules.groups.application.membership import group_of_a_member
from app.modules.groups.domain.ports import GroupRepository


class LeaveGroup:
    """A member leaves a group, after the app's confirmation
    (``docs/adr/0183`` §7) — and may join again later under its policy.

    An Owner leaving a group other people are in passes it to the member who
    has been in longest, with every request waiting on it; an Owner alone is
    refused with ``lone_owner_cannot_leave`` and deletes it instead. Both are
    the aggregate's rules.

    **A stranger meets ``group_not_found``**, as the group's page refuses them —
    and so does somebody tapping *Leave* a second time, who is one now. Answers
    nothing: the app goes back to the Groups list, which reads the groups again.
    """

    def __init__(
        self, *, groups: GroupRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._groups = groups
        self._uow = uow
        self._clock = clock

    async def execute(self, command: LeaveGroupCommand) -> None:
        group = await group_of_a_member(
            self._groups, command.group_id, command.player_id
        )
        group.leave(command.player_id, occurred_at=self._clock.now())
        await self._groups.save(group)
        await self._uow.commit()

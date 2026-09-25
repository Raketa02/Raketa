from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.groups.application.commands import DeleteGroupCommand
from app.modules.groups.application.membership import group_of_a_member
from app.modules.groups.domain.ports import GroupRepository


class DeleteGroup:
    """The Owner deletes a group nobody else is in, after the app's
    confirmation (``docs/adr/0183`` §7).

    Refused in the order a person could meet them: a stranger meets
    ``group_not_found`` as the group's page refuses them, a member who is not
    the Owner ``not_the_group_owner``, and an Owner with other people in it
    ``group_has_other_members`` — the last two the aggregate's.

    Afterwards the group is in no list and no search, its link reads *nothing
    at that link*, and the requests waiting on it are gone (the repository's
    projection). Answers nothing: the app goes back to the Groups list.
    """

    def __init__(
        self, *, groups: GroupRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._groups = groups
        self._uow = uow
        self._clock = clock

    async def execute(self, command: DeleteGroupCommand) -> None:
        group = await group_of_a_member(
            self._groups, command.group_id, command.deleted_by
        )
        group.delete(by=command.deleted_by, occurred_at=self._clock.now())
        await self._groups.save(group)
        await self._uow.commit()

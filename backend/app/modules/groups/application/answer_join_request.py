"""The Owner answers a Join request: *Approve*, or ✕ (#505, ``docs/adr/0183`` §7).

**Two use cases in one module, because they are one question with two
answers** — the same load, the same refusals in the same order, the same save —
and only the aggregate's method differs. Each answers nothing: approving
admits the person at once and declining removes the request silently, and the
Owner's screen reads the queue and the group again for both.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.groups.application.commands import AnswerJoinRequestCommand
from app.modules.groups.domain.errors import GroupNotFound
from app.modules.groups.domain.group import Group
from app.modules.groups.domain.ports import GroupRepository


class _AnswerJoinRequest:
    """What both answers share: load the group, or refuse to admit it exists."""

    def __init__(
        self, *, groups: GroupRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._groups = groups
        self._uow = uow
        self._clock = clock

    async def _group_they_are_in(self, command: AnswerJoinRequestCommand) -> Group:
        """The group, if the person answering is in it. A stranger is refused
        as the group's page refuses them; the member who is not the Owner is the
        aggregate's to refuse."""

        group = await self._groups.load(command.group_id)
        if group is None or not group.is_member(command.answered_by):
            raise GroupNotFound()
        return group

    async def _save(self, group: Group) -> None:
        await self._groups.save(group)
        await self._uow.commit()


class ApproveJoinRequest(_AnswerJoinRequest):
    """The person is a Group member at once. Approving somebody already in
    changes nothing; approving somebody with nothing waiting is
    ``join_request_not_found``."""

    async def execute(self, command: AnswerJoinRequestCommand) -> None:
        group = await self._group_they_are_in(command)
        group.approve(
            command.player_id, by=command.answered_by, occurred_at=self._clock.now()
        )
        await self._save(group)


class DeclineJoinRequest(_AnswerJoinRequest):
    """The request is gone, silently, and the person may ask again. Declining
    what is not waiting changes nothing."""

    async def execute(self, command: AnswerJoinRequestCommand) -> None:
        group = await self._group_they_are_in(command)
        group.decline(
            command.player_id, by=command.answered_by, occurred_at=self._clock.now()
        )
        await self._save(group)

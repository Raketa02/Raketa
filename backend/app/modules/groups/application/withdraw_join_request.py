from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.groups.application.commands import WithdrawJoinRequestCommand
from app.modules.groups.domain.ports import GroupRepository


class WithdrawJoinRequest:
    """The player who asked to join taps *Withdraw request* on the *Asked*
    sheet (#792, ``docs/adr/0204`` §3, §11) — and their Join request leaves the
    Owner's, the Administrator's and the club's lists at once.

    **It tells nobody**: no notice, no line, no email (call 7). **Withdrawing a
    request already answered or gone changes nothing and still succeeds** — one
    approved a moment earlier leaves them a member — and they may ask again, as
    after a decline. **A group that is gone is a request that is gone**: one
    deleted while the *Asked* sheet was open took every request waiting on it,
    so the tap succeeds there too rather than meet ``group_not_found`` — a
    call, so a stale sheet never ends on an error; it names no group, so it
    tells nobody which ids are real. Answers nothing: the row is read again.
    """

    def __init__(
        self, *, groups: GroupRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._groups = groups
        self._uow = uow
        self._clock = clock

    async def execute(self, command: WithdrawJoinRequestCommand) -> None:
        group = await self._groups.load(command.group_id)
        if group is None:
            return
        group.withdraw_request(command.player_id, occurred_at=self._clock.now())
        await self._groups.save(group)
        await self._uow.commit()

"""Unblock a player: the same shape as blocking, and the same silence.

**One direction only.** This lifts the caller's own block. If the other party has
blocked back, their stream is untouched and the two of them stay invisible to
each other — which is what the directed record buys (``docs/adr/0095`` §2) and is
invisible from here by design: this use case never reads the other stream, so it
cannot accidentally report on it.

**Unblocking somebody who was never blocked is a no-op, not a 404.** There is no
stream to open and nothing to append, and answering differently would be the
response shape telling the caller something about state — the first crack in
ADR-0095 §8's promise that a block is unrepresentable in a response. The route
answers identically in all three cases: standing, already lifted, never blocked.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.blocks.application.commands import UnblockPlayerCommand
from app.modules.blocks.domain.ports import BlockRepository


class UnblockPlayer:
    def __init__(
        self,
        *,
        blocks: BlockRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._blocks = blocks
        self._uow = uow
        self._clock = clock

    async def execute(self, command: UnblockPlayerCommand) -> None:
        block = await self._blocks.load(
            blocker_id=command.blocker_id, blocked_id=command.blocked_id
        )
        if block is None:
            # Nothing to lift and nothing to record. No transaction is opened
            # for it, and the caller cannot tell this apart from the lift below.
            return

        block.unblock(occurred_at=instant(self._clock.now()))
        await self._blocks.save(block)
        await self._uow.commit()

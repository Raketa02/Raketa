"""Block a player: one command, one transaction, one direction.

**Idempotent, and answered from the stream** rather than from a table beside it.
Whether this pair is already blocked this way round is a question the aggregate
answers about itself, so a second tap appends nothing and needs no idempotency
key — which is the difference between this and the profile commit: a block is a
*state* somebody asks for, not a *request* that happens once.

**No cap, no cooldown, no rate limit** (``docs/adr/0095`` §3). There is nothing
in this use case that counts, and there is nothing for a later change to
increment: friction on the one control a person has is a tax paid to solve a
problem the platform does not have at eleven players.

**Nothing is notified of the block.** The events are appended and published like
every other event in this codebase. An audit line is written with no payload,
and Proposals takes back the blocker's yeses where the blocked player is In,
after commit and through the ordinary withdrawal (``docs/adr/0193`` §4). The one
notice that can follow is that withdrawal's own: on a game waiting for its club,
the others In are told the blocker *left*, exactly as leaving by hand tells
them, and nothing names a block.

**The blocked player is not checked for existence, deliberately.** Two reasons,
and the second is the load-bearing one. A block of an id nobody holds costs one
stream nobody reads and excludes nobody; and answering *no such player* would
make this endpoint an oracle for which ids exist, which is a worse thing to hand
out than an unused stream. The same argument the photo route makes when it
answers identically for *no such photo* and *not yours*.

**A genuinely concurrent duplicate loses a race rather than replaying.** Two
requests that both read an empty stream compute the same id, collide on version 1
and the store rejects the loser, which surfaces as ``concurrent_modification``.
The client retries and the retry is the no-op above — the same trade every
event-sourced write in this codebase makes.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.blocks.application.commands import BlockPlayerCommand
from app.modules.blocks.domain.block import Block
from app.modules.blocks.domain.errors import CannotBlockYourself
from app.modules.blocks.domain.ports import BlockRepository


class BlockPlayer:
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

    async def execute(self, command: BlockPlayerCommand) -> None:
        # Refused before the store is asked anything. The aggregate refuses it
        # too — that is the rule's real home — but a request that was going to
        # be refused should not cost a round trip first.
        if command.blocker_id == command.blocked_id:
            raise CannotBlockYourself()

        at = instant(self._clock.now())
        existing = await self._blocks.load(
            blocker_id=command.blocker_id, blocked_id=command.blocked_id
        )
        if existing is None:
            block = Block.first_blocked(
                blocker_id=command.blocker_id,
                blocked_id=command.blocked_id,
                occurred_at=at,
            )
        else:
            # A no-op while the block is standing, so this is also the path a
            # double tap takes: it saves an aggregate with nothing pending and
            # the stream does not grow.
            block = existing
            block.block(occurred_at=at)

        await self._blocks.save(block)
        await self._uow.commit()

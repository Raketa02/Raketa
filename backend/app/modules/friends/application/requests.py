"""Asking, answering and taking back — one command, one transaction each
(``docs/adr/0202`` §1–§2; the mechanics §3.2–§3.5).

**Silent but for two things.** A request is told to the person asked, and
*friends made* to whoever asked — Notifications hears both events after the
commit. *Not now*, a cancel and a removal append events nobody is told about.

**Anyone may be asked, with no daily limit** (``docs/adr/0204`` §2): the one
exception is a player who turned *Show me to new people* off, whom only people
they share a group, a game or a friendship with may ask — the record's rule (b),
asked through ``OpenToTheRequester``, so *Add friend* is offered exactly where
it would be admitted. Anybody else is refused ``player_unavailable``, one answer
for a switched-off stranger and an id nobody holds. A request made by the
requester's link (#748) is the one way in besides, and skips it.

**A request from a player the reader blocked is never shown to the reader**: one
asked while the block stands is recorded **unseen** — the requester reads
*request sent*, the reader nothing, not after an unblock either — and one asked
before a block not yet delivered is hidden at every read
(``application/reads.py``). An answer to either is refused exactly as an answer
to no request is (``friend_request_not_found``).

**The screen's group is kept only if the two share it**, so a card or a notice
never names a group a client merely sent.

**Asking somebody you blocked** is refused (``unblock_them_first``): it would
offer friendship across your own block.

**A race loses rather than replays.** Two acts on one pair that both read the
same version collide on the stream, and the loser surfaces as
``concurrent_modification``; a retry meets the rules above.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.friends.application.commands import (
    AnswerCommand,
    AskCommand,
    TakeBackCommand,
)
from app.modules.friends.domain.friendship import Friendship
from app.modules.friends.domain.errors import (
    CannotBefriendYourself,
    FriendRequestNotFound,
    PlayerUnavailable,
    UnblockThemFirst,
)
from app.modules.friends.domain.ports import (
    FriendshipRepository,
    OpenToTheRequester,
    ReadersBlocks,
    ReadersGroups,
)
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin


@final
@dataclass(frozen=True, slots=True)
class Admitted:
    """A request the rule lets through, and the groups the two share now —
    the only group a card may name."""

    shared: frozenset[UUID]


@final
class WhoMayBeAsked:
    """**Who may be asked to be friends** (``docs/adr/0204`` §2): anybody the
    record would reach — *Show me to new people* on, or a group, a game or a
    friendship shared. **The one rule**, the record's own, asked through
    ``OpenToTheRequester``.

    It reads **the requester's groups first**, because the card names a group
    only while the two share it, and a group-mate is admitted whatever the
    switch says. It knows nothing of blocks: the ask refuses its own
    (``unblock_them_first``), and swallows the other's."""

    def __init__(self, *, groups: ReadersGroups, reach: OpenToTheRequester) -> None:
        self._groups = groups
        self._reach = reach

    async def admits(self, requester: UUID, addressee: UUID) -> Admitted | None:
        """The request admitted, and the groups the two share — or ``None``:
        the addressee is out of the requester's reach."""

        shared = frozenset(
            group.group_id
            for group in await self._groups.groups_of(requester)
            if addressee in group.members
        )
        if shared or await self._reach.open_to(addressee, requester=requester):
            return Admitted(shared=shared)
        return None


@final
class AskToBeFriends:
    def __init__(
        self,
        *,
        friendships: FriendshipRepository,
        blocks: ReadersBlocks,
        who: WhoMayBeAsked,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._friendships = friendships
        self._blocks = blocks
        self._who = who
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AskCommand) -> FriendRelation:
        """The requester's relation once asked: ``SENT``, or ``FRIEND`` when the
        request crossed one the other had made of them."""

        requester, addressee = command.requester_id, command.addressee_id
        if requester == addressee:
            raise CannotBefriendYourself()
        now = instant(self._clock.now())
        where = command.where
        if where.made_from is not RequestOrigin.LINK:
            admitted = await self._who.admits(requester, addressee)
            if admitted is None:
                raise PlayerUnavailable()
            if where.group_id not in admitted.shared:
                # The screen's group, kept only if the two share it: a card or a
                # notice never names a group the client merely sent.
                where = where.without_the_group()
        if addressee in await self._blocks.blocked_by(requester):
            raise UnblockThemFirst()

        friendship = await self._friendships.load(requester, addressee)
        relation = friendship.ask(
            requester=requester,
            where=where,
            at=now,
            # Asked of somebody who blocked the requester: open, *request sent*
            # to the requester, and never shown to them (`docs/adr/0202` §2).
            # Their own blocks, read to decide and never answered.
            unseen=requester in await self._blocks.blocked_by(addressee),
        )
        await self._friendships.save(friendship)
        await self._uow.commit()
        return relation


class _Answer:
    """Accept and *Not now* share their refusal: a request hidden by the
    reader's own block is no request at all."""

    def __init__(
        self,
        *,
        friendships: FriendshipRepository,
        blocks: ReadersBlocks,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._friendships = friendships
        self._blocks = blocks
        self._uow = uow
        self._clock = clock

    async def _load(self, command: AnswerCommand) -> Friendship:
        if command.reader_id == command.requester_id:
            raise FriendRequestNotFound()
        if command.requester_id in await self._blocks.blocked_by(command.reader_id):
            raise FriendRequestNotFound()
        return await self._friendships.load(command.reader_id, command.requester_id)


@final
class AcceptFriendRequest(_Answer):
    async def execute(self, command: AnswerCommand) -> FriendRelation:
        friendship = await self._load(command)
        friendship.accept(by=command.reader_id, at=instant(self._clock.now()))
        await self._friendships.save(friendship)
        await self._uow.commit()
        return FriendRelation.FRIEND


@final
class SetAsideFriendRequest(_Answer):
    """*Not now* — the card leaves the reader's Home; the request stays open,
    theirs to accept later, and the requester is never told."""

    async def execute(self, command: AnswerCommand) -> None:
        friendship = await self._load(command)
        friendship.set_aside(by=command.reader_id, at=instant(self._clock.now()))
        await self._friendships.save(friendship)
        await self._uow.commit()


class _TakeBack:
    def __init__(
        self,
        *,
        friendships: FriendshipRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._friendships = friendships
        self._uow = uow
        self._clock = clock

    async def _load(self, command: TakeBackCommand) -> Friendship:
        if command.player_id == command.other_id:
            raise CannotBefriendYourself()
        return await self._friendships.load(command.player_id, command.other_id)


@final
class CancelFriendRequest(_TakeBack):
    """The requester takes their request back, silently. **Idempotent**: with
    no request of theirs open — never made, answered, or ended — nothing is
    recorded and the answer is the same."""

    async def execute(self, command: TakeBackCommand) -> None:
        friendship = await self._load(command)
        friendship.cancel(by=command.player_id, at=instant(self._clock.now()))
        await self._friendships.save(friendship)
        await self._uow.commit()


@final
class RemoveFriend(_TakeBack):
    """Either friend removes the other, silently, and **no game is touched**
    (the mechanics §3.4). Idempotent, as a cancel is."""

    async def execute(self, command: TakeBackCommand) -> None:
        friendship = await self._load(command)
        friendship.remove(by=command.player_id, at=instant(self._clock.now()))
        await self._friendships.save(friendship)
        await self._uow.commit()

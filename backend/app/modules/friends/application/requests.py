"""Asking, answering and taking back — one command, one transaction each
(``docs/adr/0202`` §1–§2; the mechanics §3.2–§3.5).

**Silent but for two things.** A request is told to the person asked, and
*friends made* to whoever asked — Notifications hears both events after the
commit. *Not now*, a cancel and a removal append events nobody is told about.

**A request is open to people from your groups, and to anybody the Ranking
shows everybody** (the mechanics §3.1, widened by ``docs/adr/0203`` §9, #773):
the two share a group now, **or** the addressee is listed on General in a sport
and hasn't turned *Show me in General* off — ``WhoMayBeAsked``, the one rule,
which the record asks too, so *Add friend* is offered exactly where it would be
admitted. Anybody else is refused ``player_not_in_your_groups``, one answer for
a stranger, a hidden player and an id nobody holds. A request made by the
requester's link (#748) is the one way in besides, and skips both.

**At most ten a Warsaw day to people you share no group with** (§9, Q21): a
request the rule admitted through the Ranking alone **counts**, and the
eleventh of the requester's day is refused ``daily_request_limit``. A request
to a group-mate never counts, wherever it was made — the Ranking's included —
nor does a link's, nor a crossing, which is an answer. The count is read
**only for a request that would count**, and decided by the aggregate after its
own refusals, so a request to a friend still reads ``already_friends``. **Two
requests racing from one requester** to two people are on two streams, so both
may read nine and the day end at eleven: a limit against spam, not a ledger
(a call).

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
from app.kernel import Clock, Instant, instant
from app.modules.friends.application.commands import (
    AnswerCommand,
    AskCommand,
    TakeBackCommand,
)
from app.modules.friends.domain.daily_limit import day_began
from app.modules.friends.domain.friendship import Friendship
from app.modules.friends.domain.errors import (
    CannotBefriendYourself,
    FriendRequestNotFound,
    NotInYourGroups,
    UnblockThemFirst,
)
from app.modules.friends.domain.ports import (
    FriendshipRepository,
    ShownToStrangers,
    ReadersBlocks,
    ReadersGroups,
    RequestsCounted,
)
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin


@final
@dataclass(frozen=True, slots=True)
class Admitted:
    """A request the rule lets through: the groups the two share now — none
    when the Ranking alone admitted it, which is a request that **counts**."""

    shared: frozenset[UUID]

    @property
    def counted(self) -> bool:
        return not self.shared


@final
class WhoMayBeAsked:
    """**Who may be asked to be friends** (the mechanics §3.1; ``docs/adr/0203``
    §9, #773): somebody the requester shares a group with now, or somebody the
    Ranking shows everybody — listed on General in a sport, *Show me in General*
    on. **The one rule**: the ask is admitted by it, and the record offers *Add
    friend* by it.

    It reads **the requester's groups first**, since a group-mate is admitted
    whatever the Ranking says — a hidden one too, uncounted (the mechanics §18)
    — and the Ranking only for somebody they share none with. It knows nothing
    of blocks: the ask refuses its own (``unblock_them_first``), and the record
    never opens across one."""

    def __init__(self, *, groups: ReadersGroups, shown: ShownToStrangers) -> None:
        self._groups = groups
        self._shown = shown

    async def admits(
        self, requester: UUID, addressee: UUID, *, now: Instant
    ) -> Admitted | None:
        """The request admitted, and how — or ``None``: nothing admits it."""

        shared = frozenset(
            group.group_id
            for group in await self._groups.groups_of(requester)
            if addressee in group.members
        )
        if shared:
            return Admitted(shared=shared)
        if await self._shown.shown(addressee, now=now):
            return Admitted(shared=frozenset())
        return None


@final
class AskToBeFriends:
    def __init__(
        self,
        *,
        friendships: FriendshipRepository,
        blocks: ReadersBlocks,
        who: WhoMayBeAsked,
        counted: RequestsCounted,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._friendships = friendships
        self._blocks = blocks
        self._who = who
        self._counted = counted
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
        counted = False
        if where.made_from is not RequestOrigin.LINK:
            admitted = await self._who.admits(requester, addressee, now=now)
            if admitted is None:
                raise NotInYourGroups()
            if where.group_id not in admitted.shared:
                # The screen's group, kept only if the two share it: a card or a
                # notice never names a group the client merely sent.
                where = where.without_the_group()
            counted = admitted.counted
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
            counted=counted,
            # Read only for a request that would count: the requester's own
            # requests since their Warsaw midnight (#773).
            sent_today=(
                await self._counted.counted_since(requester, day_began(now))
                if counted
                else 0
            ),
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

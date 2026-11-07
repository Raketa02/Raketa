"""**Ask for a level** — a friend with no level in a sport asked to get one, so
they can be seated (``docs/adr/0202`` §4; the mechanics §5; #749).

One command, one transaction, on the pair's Friendship stream. **Refused, in
this order**, so nothing about a stranger is ever read out:

- ``friend_not_found`` — they are not the asker's friend (never were, removed,
  ended by a block, or the asker themselves). Checked first: whether somebody
  who is no friend has a level is not the asker's to learn;
- ``not_one_of_your_groups`` — the group whose picker it was asked from is not
  the asker's now; its picker is where the answer opens;
- ``already_has_a_level`` — the friend has a level in the sport, read from the
  rating's published one (``FriendLevels``): they can be seated already;
- ``level_already_asked`` — the aggregate's: once per friend per sport, ever.

**Told after the commit**: the friend is told *level asked* (Notifications hears
``friends.level_asked``), and the asker *level got* when the rating records the
friend's first level in the sport (``handlers/level_got.py``).

**A level recorded between the check above and this commit** is caught by the
answerer, which hears the ask too and reads the level again after the commit —
so the asker is told *level got* at once. The friend is still told *level
asked*, for a level they already have: a cost of the window, not closed.
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.friends.application.commands import AskForALevelCommand
from app.modules.friends.domain.errors import (
    AlreadyHasALevel,
    FriendNotFound,
    NotOneOfYourGroups,
)
from app.modules.friends.domain.ports import (
    FriendLevels,
    FriendshipRepository,
    ReadersGroups,
)


@final
class AskForALevel:
    def __init__(
        self,
        *,
        friendships: FriendshipRepository,
        levels: FriendLevels,
        groups: ReadersGroups,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._friendships = friendships
        self._levels = levels
        self._groups = groups
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AskForALevelCommand) -> None:
        asker, friend = command.asker_id, command.friend_id
        if asker == friend:
            raise FriendNotFound()
        friendship = await self._friendships.load(asker, friend)
        # The aggregate refuses this too; asked first here so a stranger's
        # groups and level are never read.
        if not friendship.are_friends:
            raise FriendNotFound()
        if command.group_id not in {
            group.group_id for group in await self._groups.groups_of(asker)
        }:
            raise NotOneOfYourGroups()
        if friend in await self._levels.levels_in([friend], sport=command.sport):
            raise AlreadyHasALevel()
        friendship.ask_for_a_level(
            asker=asker,
            sport=command.sport,
            group_id=command.group_id,
            at=instant(self._clock.now()),
        )
        await self._friendships.save(friendship)
        await self._uow.commit()

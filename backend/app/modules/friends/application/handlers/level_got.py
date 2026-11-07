"""**A friend's level answers every ask for it** (``docs/adr/0202`` §4, §8;
#749) — ``friends.level_got`` on that pair's stream, which Notifications tells
the asker. Heard twice over, so no ask can wait on a level that already came:

- **``rating.rating_initialised``** — a rating is initialised once per player
  and sport (its stream is keyed on the two), so the event *is* the first
  level: each friend waiting on it has their ask answered;
- **``friends.level_asked``** — an ask whose friend has a level in the sport
  **already**. The use case refuses that, but a level recorded between its
  check and its commit, and delivered before the commit, finds no ask to
  answer; read again here, after the ask's commit, it is seen. Whichever of the
  two commits lands second, its delivery sees the first.

**Idempotent**: an ask answered already records nothing, so a delivery seen
twice — or an ask answered on both paths — tells nobody twice. Recorded whether
or not the two are still friends; Notifications tells only while they are.

**No commit**: the transaction is the delivery's.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.events import DeliveryContext
from app.kernel import Instant, Sport, instant
from app.modules.friends.domain.events import LevelAsked
from app.modules.friends.domain.ports import (
    AsksWaitingOnALevel,
    FriendLevels,
    FriendshipRepository,
)
from app.modules.rating.domain.events import RatingInitialised
from app.shared.domain import DomainEvent


@final
class AnswerTheAsksForALevel:
    def __init__(
        self,
        *,
        asks: AsksWaitingOnALevel,
        levels: FriendLevels,
        friendships: FriendshipRepository,
    ) -> None:
        self._asks = asks
        self._levels = levels
        self._friendships = friendships

    async def __call__(self, event: DomainEvent, context: DeliveryContext) -> None:
        at = instant(event.occurred_at)
        if isinstance(event, RatingInitialised):
            friend, sport = event.player_id, Sport(event.sport)
            for asker in await self._asks.askers_waiting_on(friend, sport):
                await self._answer(asker, friend, sport, at=at)
        elif isinstance(event, LevelAsked):
            sport = Sport(event.sport)
            if event.friend_id in await self._levels.levels_in(
                [event.friend_id], sport=sport
            ):
                await self._answer(event.asker_id, event.friend_id, sport, at=at)

    async def _answer(
        self, asker: UUID, friend: UUID, sport: Sport, *, at: Instant
    ) -> None:
        friendship = await self._friendships.load(asker, friend)
        friendship.answer_the_ask(friend=friend, sport=sport, at=at)
        await self._friendships.save(friendship)

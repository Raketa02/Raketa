"""**A notice given is pushed** — to every phone its player registered, after
the commit that gave it, from the outbox (#549; the screens A9).

**A push fails soft, and that is the one choice here that is not obvious.** The
outbox retries a delivery that raised at the head of every batch, with no
backoff, and rolls back everything delivered beside it — so a push service that
is down for an hour, raising, would hold every other event behind its notices
for that hour. A push that could not be made is logged and given up instead:
the notice is in the player's recent list whatever happens to the push, and
every notice about money is emailed as well (the mechanics §17.2).

**A phone the push service no longer knows is pushed to no more** — removed
from the player's preferences in the delivery's own transaction, so the next
notice does not ask about it again.

**At least once, like every delivery**: a push made and then a commit that
failed delivers the notice again, and its phone is pushed it twice. Nothing on
a phone can be taken back, so this is the price, not a bug to close.
"""

from __future__ import annotations

import logging
from typing import final

from app.application.events import DeliveryContext
from app.kernel import Clock, instant
from app.modules.notifications.application.reading import NoticeWords, recorded
from app.modules.notifications.domain.events import NoticeGiven
from app.modules.notifications.domain.ports import (
    NotificationPreferencesRepository,
    Push,
    PushNotifications,
    PushUnavailable,
)
from app.modules.notifications.domain.preferences import device_of

logger = logging.getLogger(__name__)


@final
class PushTheNotice:
    def __init__(
        self,
        *,
        preferences: NotificationPreferencesRepository,
        words: NoticeWords,
        push: PushNotifications,
        clock: Clock,
    ) -> None:
        self._preferences = preferences
        self._words = words
        self._push = push
        self._clock = clock

    async def __call__(self, event: NoticeGiven, context: DeliveryContext) -> None:
        tokens = await self._preferences.tokens_of(event.player_id)
        if not tokens:
            return
        [words] = await self._words.of([recorded(event)])
        data = {
            "notice_id": str(event.notice_id),
            "kind": event.kind,
            "opens": event.opens,
            "game_id": str(event.game_id),
            "pool_id": str(event.pool_id),
            "sport": event.sport,
            "game_kind": event.game_kind,
        }
        try:
            receipt = await self._push.send(
                [
                    Push(token=token, title=words.title, body=words.body, data=data)
                    for token in tokens.values()
                ]
            )
        except PushUnavailable:
            logger.warning(
                "notifications.push.unavailable",
                extra={
                    "notice_id": str(event.notice_id),
                    "player_id": str(event.player_id),
                    "event_id": str(context.event_id),
                },
            )
            return
        if not receipt.gone:
            return
        preferences = await self._preferences.load(event.player_id)
        at = instant(self._clock.now())
        for token in receipt.gone:
            preferences.remove(device_of(token), at=at)
        await self._preferences.save(preferences)

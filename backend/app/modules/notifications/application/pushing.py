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

**What a notice is pushed as is decided once** (``NoticePushes``): the pusher
sends it to every phone, and the dev console's *Sent* pane shows it for a
player with none — every seed account — as what would have been pushed (#594).
**A notice of the player's own act is pushed as nothing** (the mechanics Q102):
they saw it happen on their own screen, and it is listed, already seen.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import final
from uuid import UUID

from app.application.events import DeliveryContext
from app.kernel import Clock, instant, invariant
from app.modules.notifications.application.reading import NoticeWords, recorded
from app.modules.notifications.application.words import Words
from app.modules.notifications.domain.events import NoticeGiven
from app.modules.notifications.domain.ports import (
    NotificationPreferencesRepository,
    Push,
    PushNotifications,
    PushUnavailable,
    RecordedNotice,
)
from app.modules.notifications.domain.preferences import device_of

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PushMessage:
    """What each of a player's phones is pushed for one notice: what the
    phone's system shows, and what a tap opens the app with."""

    title: str
    body: str
    data: Mapping[str, str]


@final
class NoticePushes:
    """**What a notice is pushed as** — the one place its push's words and data
    are decided.

    **As it was given**: a notice is pushed once, the moment it is given, and
    a notice the day later gathers others into is pushed to nobody again — so
    its push is drawn as though nothing was gathered, while the list says how
    many it holds. The words are drawn from the notice's facts each time they
    are asked for, as the list's are: a name changed since reads as it stands.

    **Never the player's own** (Q102): ``None`` — it is pushed to nobody.
    """

    def __init__(self, *, words: NoticeWords) -> None:
        self._words = words

    async def of(
        self, notices: Sequence[RecordedNotice], *, reader: UUID
    ) -> list[PushMessage | None]:
        """``reader`` is whose notices these are: a friend request from *Same
        competitive level* says today's % between the two (#794)."""

        given = [replace(notice, gathered=0) for notice in notices if not notice.own]
        drawn = iter(await self._words.of(given, reader=reader))
        return [
            None if notice.own else _message(notice, next(drawn)) for notice in notices
        ]


def _message(notice: RecordedNotice, words: Words) -> PushMessage:
    return PushMessage(title=words.title, body=words.body, data=_opening(notice))


def _opening(notice: RecordedNotice) -> dict[str, str]:
    """What a tap hands the app: the notice, and where it opens — and the game
    it is about, for every notice but one about no game (*Get your level*,
    #727), which opens Home and hands nothing more — but the person it names,
    for a friend's (#745): whose record ``RECORD`` opens; and the group and the
    sport it names, for an ask for a level's (#749): the questionnaire
    ``QUESTIONNAIRE`` opens, and the picker ``PICKER`` does."""

    opening = {
        "notice_id": str(notice.notice_id),
        "kind": notice.kind,
        "opens": notice.opens,
    }
    if notice.game_id is None:
        if notice.person_named is not None:
            opening["player_id"] = str(notice.person_named)
        if notice.pool_id is not None:
            opening["pool_id"] = str(notice.pool_id)
        if notice.sport is not None:
            opening["sport"] = notice.sport.value
        return opening
    about_a_game = f"{notice.kind} is about a game"
    return {
        **opening,
        "game_id": str(notice.game_id),
        "pool_id": str(invariant(notice.pool_id, about_a_game)),
        "sport": invariant(notice.sport, about_a_game).value,
        "game_kind": invariant(notice.game_kind, about_a_game),
    }


@final
class PushTheNotice:
    def __init__(
        self,
        *,
        preferences: NotificationPreferencesRepository,
        pushes: NoticePushes,
        push: PushNotifications,
        clock: Clock,
    ) -> None:
        self._preferences = preferences
        self._pushes = pushes
        self._push = push
        self._clock = clock

    async def __call__(self, event: NoticeGiven, context: DeliveryContext) -> None:
        tokens = await self._preferences.tokens_of(event.player_id)
        if not tokens:
            return
        [message] = await self._pushes.of([recorded(event)], reader=event.player_id)
        if message is None:
            return
        try:
            receipt = await self._push.send(
                [
                    Push(
                        token=token,
                        title=message.title,
                        body=message.body,
                        data=message.data,
                    )
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

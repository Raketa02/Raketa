"""What a notice is pushed as (#594; the screens A9) — ``NoticePushes``, the one
place a push's words and data are decided: the pusher sends it, and the dev
console's *Sent* pane shows it.

**As it was given**: a notice is pushed once, the moment it is given, and the
notices the day later gathers into it push nobody. So its push says what it
said then, while the list counts what it holds now.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.kernel import Sport, instant
from app.modules.notifications.application.pushing import NoticePushes
from app.modules.notifications.application.reading import NoticeWords
from app.modules.notifications.domain.notices import NoticeKind, Opens
from app.modules.notifications.domain.ports import RecordedNotice

CLUB = uuid4()


class StandInNames:
    async def of_people(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        return {}

    async def of_clubs(self, club_ids: Collection[UUID]) -> Mapping[UUID, str]:
        return {CLUB: "Bonarka Arena"}


def a_card_that_needs_only_you(*, gathered: int) -> RecordedNotice:
    return RecordedNotice(
        notice_id=uuid4(),
        kind=NoticeKind.YOU_COMPLETE_IT.value,
        game_id=uuid4(),
        pool_id=uuid4(),
        sport=Sport.PADEL,
        game_kind="COMPETITIVE",
        club_id=CLUB,
        starts_at=instant(datetime(2026, 10, 10, 15, tzinfo=timezone.utc)),
        opens=Opens.DECK.value,
        amount_grosze=None,
        people=(),
        reason=None,
        given_at=instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc)),
        gathered=gathered,
    )


async def test_a_notice_the_day_gathered_into_is_pushed_as_it_was_given() -> None:
    words = NoticeWords(names=StandInNames())
    gathering = a_card_that_needs_only_you(gathered=2)
    as_given = replace(gathering, gathered=0)

    [pushed] = await NoticePushes(words=words).of([gathering])

    [listed] = await words.of([gathering])
    [given] = await words.of([as_given])
    assert listed.title == "3 games need only you"
    assert (pushed.title, pushed.body) == (given.title, given.body)
    assert pushed.title == "A game needs only you"


async def test_a_push_opens_the_app_on_its_notice() -> None:
    notice = a_card_that_needs_only_you(gathered=0)

    [pushed] = await NoticePushes(words=NoticeWords(names=StandInNames())).of([notice])

    assert pushed.data == {
        "notice_id": str(notice.notice_id),
        "kind": "YOU_COMPLETE_IT",
        "opens": "DECK",
        "game_id": str(notice.game_id),
        "pool_id": str(notice.pool_id),
        "sport": "PADEL",
        "game_kind": "COMPETITIVE",
    }

"""The recent notices — the list behind the bell on Home (#549; the screens A9)
— the words every notice is drawn in, for the list and for a push alike, and
**the bell's number** (#621; the mechanics Q101, Q102).

**Read, recorded nowhere**: a notice is put into words against the people's and
the clubs' names as they stand, one read of each for the whole list.

**The bell's number travels on this read and nowhere else** — never on Home's,
since no other context knows Notifications exists: the notices that reached the
list since the player last opened it (``opening.py``), none of their own,
counted whole however few rows are asked for.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from app.kernel import Instant, Sport, instant
from app.modules.notifications.application.words import Said, Words, words_for
from app.modules.notifications.domain.events import NoticeGiven
from app.modules.notifications.domain.notices import NoticeKind, Opens
from app.modules.notifications.domain.ports import (
    Names,
    NoticeDirectory,
    RecordedNotice,
)

#: The longest list a phone is handed.
MOST_RECENT: Final = 100


def recorded(given: NoticeGiven) -> RecordedNotice:
    """A notice just given, as the list will hold it."""

    return RecordedNotice(
        notice_id=given.notice_id,
        kind=given.kind,
        game_id=given.game_id,
        pool_id=given.pool_id,
        sport=Sport(given.sport),
        game_kind=given.game_kind,
        club_id=given.club_id,
        starts_at=instant(given.starts_at),
        opens=given.opens,
        amount_grosze=given.amount_grosze,
        people=given.people,
        reason=given.reason,
        given_at=instant(given.occurred_at),
        gathered=0,
        own=given.own,
        until=None if given.until is None else instant(given.until),
        you_left=given.you_left,
        kept_grosze=given.kept_grosze,
        rescue=given.rescue,
        court_name=given.court_name,
        indoor=given.indoor,
        moved_from=given.moved_from,
    )


@final
class NoticeWords:
    """Every notice's words, the names read once for all of them."""

    def __init__(self, *, names: Names) -> None:
        self._names = names

    async def of(self, notices: Sequence[RecordedNotice]) -> list[Words]:
        people = await self._names.of_people(
            {person for notice in notices for person in notice.people}
        )
        clubs = await self._names.of_clubs({notice.club_id for notice in notices})
        return [
            words_for(
                Said(
                    kind=NoticeKind(notice.kind),
                    sport=notice.sport,
                    club=clubs.get(notice.club_id, "the club"),
                    starts_at=notice.starts_at,
                    opens=Opens(notice.opens),
                    amount_grosze=notice.amount_grosze,
                    names=tuple(
                        people[person] for person in notice.people if person in people
                    ),
                    reason=notice.reason,
                    gathered=notice.gathered,
                    until=notice.until,
                    given_at=notice.given_at,
                    you_left=notice.you_left,
                    kept_grosze=notice.kept_grosze,
                    rescue=notice.rescue,
                    court_name=notice.court_name,
                    indoor=notice.indoor,
                    moved_from=notice.moved_from,
                )
            )
            for notice in notices
        ]


@dataclass(frozen=True, slots=True)
class RecentNotice:
    notice: RecordedNotice
    words: Words


@dataclass(frozen=True, slots=True)
class RecentNotices:
    """The newest notices in their words, and the bell's number."""

    notices: list[RecentNotice]
    #: How many are new — past the rows read, too.
    new_count: int
    last_opened_at: Instant | None


@final
class ReadRecentNotices:
    def __init__(self, *, notices: NoticeDirectory, words: NoticeWords) -> None:
        self._notices = notices
        self._words = words

    async def execute(self, player_id: UUID, *, limit: int) -> RecentNotices:
        recent = await self._notices.recent(
            player_id, limit=max(1, min(limit, MOST_RECENT))
        )
        return RecentNotices(
            notices=[
                RecentNotice(notice=notice, words=words)
                for notice, words in zip(
                    recent.notices, await self._words.of(recent.notices), strict=True
                )
            ],
            new_count=recent.new_count,
            last_opened_at=recent.last_opened_at,
        )

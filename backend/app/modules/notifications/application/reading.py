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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from app.kernel import Instant, Sport, instant, invariant
from app.modules.notifications.application.words import (
    Said,
    SaidOfNoGame,
    Words,
    words_about_no_game,
    words_for,
)
from app.modules.notifications.domain.events import NoticeGiven
from app.modules.notifications.domain.notices import NoticeKind, NoticeReason, Opens
from app.modules.notifications.domain.ports import (
    Friendships,
    Names,
    NoticeDirectory,
    PercentsEven,
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
        sport=None if given.sport is None else Sport(given.sport),
        game_kind=given.game_kind,
        club_id=given.club_id,
        starts_at=None if given.starts_at is None else instant(given.starts_at),
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
    """Every notice's words, the names read once for all of them — and, for a
    friend request from *Same competitive level*, today's % even between the
    reader and the requester (#794), read once for all of those."""

    def __init__(self, *, names: Names, evens: PercentsEven) -> None:
        self._names = names
        self._evens = evens

    async def of(
        self, notices: Sequence[RecordedNotice], *, reader: UUID
    ) -> list[Words]:
        people = await self._names.of_people(
            {person for notice in notices for person in notice.people}
        )
        clubs = await self._names.of_clubs(
            {notice.club_id for notice in notices if notice.club_id is not None}
        )
        # A notice about no game that names a group names the one a friend
        # request was asked from (#745); a friends game's empty seat, the group
        # it may be opened to (#751).
        groups = await self._names.of_groups(
            {
                notice.pool_id
                for notice in notices
                if notice.pool_id is not None
                and (notice.game_id is None or notice.kind in _NAMING_THE_GROUP)
            }
        )
        compared = {
            (person, notice.sport)
            for notice in notices
            if notice.reason == NoticeReason.FROM_SAME_LEVEL
            and notice.sport is not None
            and (person := notice.person_named) is not None
        }
        evens = await self._evens.between(reader, compared) if compared else {}
        return [
            _drawn(notice, people=people, clubs=clubs, groups=groups, evens=evens)
            for notice in notices
        ]


def _drawn(
    notice: RecordedNotice,
    *,
    people: Mapping[UUID, str],
    clubs: Mapping[UUID, str],
    groups: Mapping[UUID, str],
    evens: Mapping[tuple[UUID, Sport], int],
) -> Words:
    """One notice's words — from its kind and the person it names when it is
    about no game (*Get your level*, #727; a friend's two, #745), else from the
    game's facts and the names."""

    kind = NoticeKind(notice.kind)
    if notice.game_id is None:
        return words_about_no_game(
            SaidOfNoGame(
                kind=kind,
                name=next(
                    (people[one] for one in notice.people if one in people), None
                ),
                group=None if notice.pool_id is None else groups.get(notice.pool_id),
                sport=notice.sport,
                reason=notice.reason,
                percent_even=(
                    None
                    if notice.person_named is None or notice.sport is None
                    else evens.get((notice.person_named, notice.sport))
                ),
            )
        )
    club_id = invariant(notice.club_id, f"{kind} names its club")
    return words_for(
        Said(
            kind=kind,
            sport=invariant(notice.sport, f"{kind} names its sport"),
            club=clubs.get(club_id, "the club"),
            starts_at=invariant(notice.starts_at, f"{kind} names its hour"),
            opens=Opens(notice.opens),
            amount_grosze=notice.amount_grosze,
            names=tuple(people[person] for person in notice.people if person in people),
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
            game_kind=notice.game_kind,
            group=None if notice.pool_id is None else groups.get(notice.pool_id),
            named=tuple(people.get(person) for person in notice.people),
        )
    )


#: The notices about a game that name its group (#751): a friends game's
#: empty seat may be opened to it.
_NAMING_THE_GROUP: Final = frozenset(
    {NoticeKind.CANT_MAKE_IT.value, NoticeKind.DIDNT_ANSWER.value}
)


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
    """**A friend request is listed only while its card is on Home** (#745):
    answered, set aside, cancelled, ended by a block or hidden by the reader's
    own, its row leaves the list and the bell's number in the same reading. A
    row is matched to its request by whose it is and when it was asked — the
    instant the notice was given.

    **So is a *level asked*** (#764; ``docs/adr/0202`` §4's 2026-11-07
    amendment): a level got by any route, *Not now*, or the asker no longer a
    friend or blocked by the reader, and its row leaves both too — matched to
    its card by who asked and the sport, which is unique: an ask is once per
    friend per sport, ever. The push, its words and *level got* are
    untouched."""

    def __init__(
        self,
        *,
        notices: NoticeDirectory,
        words: NoticeWords,
        friendships: Friendships,
    ) -> None:
        self._notices = notices
        self._words = words
        self._friendships = friendships

    async def execute(self, player_id: UUID, *, limit: int) -> RecentNotices:
        recent = await self._notices.recent(
            player_id,
            limit=max(1, min(limit, MOST_RECENT)),
            leaving_out=(
                await self._requests_answered(player_id)
                | await self._asks_gone(player_id)
            ),
        )
        return RecentNotices(
            notices=[
                RecentNotice(notice=notice, words=words)
                for notice, words in zip(
                    recent.notices,
                    await self._words.of(recent.notices, reader=player_id),
                    strict=True,
                )
            ],
            new_count=recent.new_count,
            last_opened_at=recent.last_opened_at,
        )

    async def _requests_answered(self, player_id: UUID) -> frozenset[UUID]:
        requests = await self._notices.of_kind(player_id, NoticeKind.FRIEND_REQUEST)
        if not requests:
            return frozenset()
        waiting = {
            (request.requester_id, request.asked_at)
            for request in await self._friendships.waiting_on(player_id)
        }
        return frozenset(
            notice.notice_id
            for notice in requests
            if (notice.person_named, notice.given_at) not in waiting
        )

    async def _asks_gone(self, player_id: UUID) -> frozenset[UUID]:
        asks = await self._notices.of_kind(player_id, NoticeKind.LEVEL_ASKED)
        if not asks:
            return frozenset()
        on_home = {
            (ask.asker_id, ask.sport)
            for ask in await self._friendships.level_asks_on(player_id)
        }
        return frozenset(
            notice.notice_id
            for notice in asks
            if (notice.person_named, notice.sport) not in on_home
        )

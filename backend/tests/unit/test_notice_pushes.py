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
from app.modules.notifications.domain.notices import (
    NoticeKind,
    NoticeReason,
    Opens,
)
from app.modules.notifications.domain.ports import RecordedNotice

CLUB = uuid4()
READER = uuid4()


class StandInNames:
    async def of_people(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        return {}

    async def of_clubs(self, club_ids: Collection[UUID]) -> Mapping[UUID, str]:
        return {CLUB: "Bonarka Arena"}

    async def of_groups(self, group_ids: Collection[UUID]) -> Mapping[UUID, str]:
        return {}


class StandInEvens:
    """91% even with anybody in padel, and no level anywhere else."""

    def __init__(self) -> None:
        self.asked: list[tuple[UUID, set[tuple[UUID, Sport]]]] = []

    async def between(
        self, reader: UUID, others: Collection[tuple[UUID, Sport]]
    ) -> Mapping[tuple[UUID, Sport], int]:
        self.asked.append((reader, set(others)))
        return {one: 91 for one in others if one[1] is Sport.PADEL}


class StandInTags:
    """Ola shares three tags with the reader, Kuba one, anybody else none."""

    def __init__(self, *, ola: UUID | None = None, kuba: UUID | None = None) -> None:
        self._shared = {one: n for one, n in ((ola, 3), (kuba, 1)) if one is not None}
        self.asked: list[tuple[UUID, set[UUID]]] = []

    async def in_common(
        self, reader: UUID, others: Collection[UUID]
    ) -> Mapping[UUID, int]:
        self.asked.append((reader, set(others)))
        return {one: self._shared.get(one, 0) for one in others}


def words_of() -> NoticeWords:
    return NoticeWords(names=StandInNames(), evens=StandInEvens(), tags=StandInTags())


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
    words = words_of()
    gathering = a_card_that_needs_only_you(gathered=2)
    as_given = replace(gathering, gathered=0)

    [pushed] = await NoticePushes(words=words).of([gathering], reader=READER)

    [listed] = await words.of([gathering], reader=READER)
    [given] = await words.of([as_given], reader=READER)
    assert listed.title == "3 games need only you"
    assert (pushed.title, pushed.body) == (given.title, given.body)
    assert pushed.title == "A game needs only you"


async def test_a_push_opens_the_app_on_its_notice() -> None:
    notice = a_card_that_needs_only_you(gathered=0)

    [pushed] = await NoticePushes(words=words_of()).of([notice], reader=READER)

    assert pushed.data == {
        "notice_id": str(notice.notice_id),
        "kind": "YOU_COMPLETE_IT",
        "opens": "DECK",
        "game_id": str(notice.game_id),
        "pool_id": str(notice.pool_id),
        "sport": "PADEL",
        "game_kind": "COMPETITIVE",
    }


async def test_a_notice_of_the_player_s_own_act_is_pushed_to_nobody() -> None:
    """The filler saw *It's a game!* on their own screen (the mechanics Q102):
    their notice is listed, already seen, and never announced back."""

    own = replace(a_card_that_needs_only_you(gathered=0), own=True)
    theirs = a_card_that_needs_only_you(gathered=0)

    pushed = await NoticePushes(words=words_of()).of([own, theirs], reader=READER)

    assert pushed[0] is None
    assert pushed[1] is not None and pushed[1].title == "A game needs only you"


def a_same_level_request(sport: Sport) -> RecordedNotice:
    return RecordedNotice(
        notice_id=uuid4(),
        kind=NoticeKind.FRIEND_REQUEST.value,
        game_id=None,
        pool_id=None,
        sport=sport,
        game_kind=None,
        club_id=None,
        starts_at=None,
        opens=Opens.HOME.value,
        amount_grosze=None,
        people=(uuid4(),),
        reason=NoticeReason.FROM_SAME_LEVEL.value,
        given_at=instant(datetime(2026, 11, 14, 9, tzinfo=timezone.utc)),
        gathered=0,
    )


async def test_a_same_level_request_says_today_s_percent_between_the_two() -> None:
    """The words §31.10: *Your level in padel · 91% even*, worked out for the
    notice's own reader — or *Found you at your squash level* when either holds
    no level there (#794)."""

    evens = StandInEvens()
    padel = a_same_level_request(Sport.PADEL)
    squash = a_same_level_request(Sport.SQUASH)

    pushed = await NoticePushes(
        words=NoticeWords(names=StandInNames(), evens=evens, tags=StandInTags())
    ).of([padel, squash], reader=READER)

    assert [(one.title, one.body) for one in pushed if one is not None] == [
        ("Somebody wants to be your friend", "Your level in padel · 91% even"),
        ("Somebody wants to be your friend", "Found you at your squash level"),
    ]
    assert evens.asked == [
        (
            READER,
            {(padel.people[0], Sport.PADEL), (squash.people[0], Sport.SQUASH)},
        )
    ]


async def test_no_percent_is_asked_for_a_list_without_a_same_level_request() -> None:
    evens = StandInEvens()
    tags = StandInTags()

    await NoticeWords(names=StandInNames(), evens=evens, tags=tags).of(
        [a_card_that_needs_only_you(gathered=0)], reader=READER
    )

    assert evens.asked == []
    assert tags.asked == []


def a_same_vibe_request(requester: UUID) -> RecordedNotice:
    return replace(
        a_same_level_request(Sport.PADEL),
        notice_id=uuid4(),
        sport=None,
        people=(requester,),
        reason=NoticeReason.FROM_SAME_VIBE.value,
    )


async def test_a_same_vibe_request_counts_today_s_tags_in_common() -> None:
    """The words §31.10: *3 things in common*, *1 thing in common*, or *Found
    you through your tags* once none is shared — counted for the notice's own
    reader, once for the whole list (#795)."""

    ola, kuba, ewa = uuid4(), uuid4(), uuid4()
    tags = StandInTags(ola=ola, kuba=kuba)

    pushed = await NoticePushes(
        words=NoticeWords(names=StandInNames(), evens=StandInEvens(), tags=tags)
    ).of(
        [a_same_vibe_request(one) for one in (ola, kuba, ewa)],
        reader=READER,
    )

    assert [one.body for one in pushed if one is not None] == [
        "3 things in common",
        "1 thing in common",
        "Found you through your tags",
    ]
    assert tags.asked == [(READER, {ola, kuba, ewa})]

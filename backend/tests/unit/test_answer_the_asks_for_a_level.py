"""**A friend's level answers every ask for it**, at the answerer's seam
(``handlers/level_got.py``; #749): on the rating's first level in a sport, and
on an ask made of somebody whose level is already there — the level recorded
between the use case's check and its commit, which no first-level delivery can
find an ask for.

The ports are hand-written stubs implementing each ``Protocol``.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import datetime, timezone
from uuid import UUID

from app.application.events import DeliveryContext
from app.kernel import Sport, instant
from app.modules.friends.application.handlers import AnswerTheAsksForALevel
from app.modules.friends.domain.events import LevelAsked, LevelGot
from app.modules.friends.domain.friendship import Friendship, Where
from app.modules.friends.domain.ports import FriendLevel
from app.modules.friends.domain.relation import RequestOrigin
from app.modules.rating.domain.events import RatingInitialised
from app.shared.domain import DomainEvent
from app.shared.ids import new_uuid

AT = instant(datetime(2026, 11, 11, 18, tzinfo=timezone.utc))
TOMEK, EWA, ZOFIA = new_uuid(), new_uuid(), new_uuid()
OGRODY = new_uuid()
CONTEXT = DeliveryContext(event_id=new_uuid(), attempt=1, occurred_at=AT)


class Streams:
    """``FriendshipRepository`` in memory: every pair's events, appended."""

    def __init__(self) -> None:
        self.events: dict[frozenset[UUID], list[DomainEvent]] = {}

    async def load(self, one: UUID, other: UUID) -> Friendship:
        return Friendship.from_history(
            one, other, list(self.events.get(frozenset((one, other)), []))
        )

    async def save(self, friendship: Friendship) -> None:
        pair = frozenset((friendship.first_id, friendship.second_id))
        self.events.setdefault(pair, []).extend(friendship.pull_events())

    def appended(self, one: UUID, other: UUID) -> list[type[DomainEvent]]:
        return [type(event) for event in self.events.get(frozenset((one, other)), [])]


class Waiting:
    """``AsksWaitingOnALevel`` over a fixed list of askers."""

    def __init__(self, *askers: UUID) -> None:
        self._askers = askers

    async def askers_waiting_on(self, friend: UUID, sport: Sport) -> tuple[UUID, ...]:
        return self._askers


class Levels:
    """``FriendLevels`` with a padel level for whoever is named."""

    def __init__(self, *rated: UUID) -> None:
        self._rated = rated

    async def levels_in(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, FriendLevel]:
        return {
            player: FriendLevel(sport=sport, level=2.5, band="Established")
            for player in player_ids
            if player in self._rated and sport is Sport.PADEL
        }


async def friends_who_asked(streams: Streams, *askers: UUID) -> None:
    for asker in askers:
        friendship = await streams.load(asker, ZOFIA)
        friendship.ask(requester=asker, where=Where(RequestOrigin.MEMBERS), at=AT)
        friendship.accept(by=ZOFIA, at=AT)
        friendship.ask_for_a_level(
            asker=asker, sport=Sport.PADEL, group_id=OGRODY, at=AT
        )
        await streams.save(friendship)


def first_level(player: UUID, sport: Sport = Sport.PADEL) -> RatingInitialised:
    return RatingInitialised(
        rating_id=new_uuid(),
        player_id=player,
        sport=sport.value,
        mu=2.5,
        sigma=1.0,
        confidence=40,
        range_low=2.0,
        range_high=3.0,
        band_name="Established",
        band_lower=2.0,
        band_upper=3.0,
        status="PROVISIONAL",
        engine_version="v3",
        source_assessment_id=new_uuid(),
        occurred_at=AT,
    )


def asked_of(friend: UUID, by: UUID) -> LevelAsked:
    return LevelAsked(
        asker_id=by, friend_id=friend, sport="PADEL", group_id=OGRODY, occurred_at=AT
    )


async def test_the_first_level_answers_every_friend_waiting_on_it():
    streams = Streams()
    await friends_who_asked(streams, TOMEK, EWA)
    answerer = AnswerTheAsksForALevel(
        asks=Waiting(TOMEK, EWA), levels=Levels(), friendships=streams
    )

    await answerer(first_level(ZOFIA), CONTEXT)

    for asker in (TOMEK, EWA):
        assert streams.appended(asker, ZOFIA)[-1] is LevelGot


async def test_an_ask_of_somebody_with_the_level_already_is_answered_at_once():
    """The level landed between the use case's check and its commit: its own
    delivery found no ask, so the ask's delivery answers it."""

    streams = Streams()
    await friends_who_asked(streams, TOMEK)
    answerer = AnswerTheAsksForALevel(
        asks=Waiting(), levels=Levels(ZOFIA), friendships=streams
    )

    await answerer(asked_of(ZOFIA, by=TOMEK), CONTEXT)

    assert streams.appended(TOMEK, ZOFIA)[-1] is LevelGot


async def test_an_ask_of_somebody_still_without_a_level_waits():
    streams = Streams()
    await friends_who_asked(streams, TOMEK)
    answerer = AnswerTheAsksForALevel(
        asks=Waiting(), levels=Levels(), friendships=streams
    )

    await answerer(asked_of(ZOFIA, by=TOMEK), CONTEXT)

    assert LevelGot not in streams.appended(TOMEK, ZOFIA)


async def test_an_ask_answered_on_both_paths_is_answered_once():
    streams = Streams()
    await friends_who_asked(streams, TOMEK)
    answerer = AnswerTheAsksForALevel(
        asks=Waiting(TOMEK), levels=Levels(ZOFIA), friendships=streams
    )

    await answerer(first_level(ZOFIA), CONTEXT)
    await answerer(asked_of(ZOFIA, by=TOMEK), CONTEXT)
    await answerer(first_level(ZOFIA), CONTEXT)

    assert streams.appended(TOMEK, ZOFIA).count(LevelGot) == 1

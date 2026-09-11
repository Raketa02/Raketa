"""Which cards are open, and the three reasons one is not.

The use case does exactly two things the two ports do not: it applies **the
window** — the day after, and for a week — and it takes out the cards this
player has already closed. Everything else about *may I be asked about this
evening at all* is the ``SettledCourts`` port's shape and is pinned in
``test_sportsmanship_settled_courts.py``; a game nobody ever said was played is
not offered here at all, which is why this file stubs the port with courts rather
than with games.

**The join is one question about a whole list**, and that is asserted rather than
assumed: a card per query would be the same answer at a cost that grows with how
much somebody has played, and nothing about the response would look different.

**Nothing here reads a rating.** The ledger is asked which of these cards are
closed and never what anybody said, which is the port's whole discipline — a read
that could answer the second question is one a route could later render.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Collection
from uuid import UUID

from app.kernel import Instant, instant
from app.modules.sportsmanship.application.read_the_open_cards import ReadTheOpenCards
from app.modules.sportsmanship.domain.card import SettledCourt
from app.shared.ids import new_uuid

NOW = instant(datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc))
ME = new_uuid()


@dataclass
class Clock:
    at: Instant

    def now(self) -> Instant:
        return self.at


@dataclass
class Courts:
    """``SettledCourts`` over a list. It answers only about the player asked
    about, which is the real port's shape — the read is *which games are mine*."""

    courts: tuple[SettledCourt, ...] = ()
    asked_at: list[Instant] = field(default_factory=list)

    async def court_of(
        self, game_id: UUID, *, player_id: UUID, now: Instant
    ) -> SettledCourt | None:
        raise AssertionError("the list read never asks about one game")

    async def courts_of(
        self, player_id: UUID, *, now: Instant
    ) -> tuple[SettledCourt, ...]:
        self.asked_at.append(now)
        return tuple(one for one in self.courts if one.rater_id == player_id)


@dataclass
class Ledger:
    closed: set[UUID] = field(default_factory=set)
    asked: list[frozenset[UUID]] = field(default_factory=list)

    async def answered_among(
        self, *, rater_id: UUID, game_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        self.asked.append(frozenset(game_ids))
        return frozenset(self.closed & set(game_ids))

    async def record(self, card) -> None:
        raise AssertionError("a read writes nothing")


def a_court(*, played_at: Instant, others: int = 3, rater: UUID = ME) -> SettledCourt:
    return SettledCourt(
        game_id=new_uuid(),
        rater_id=rater,
        others=tuple(new_uuid() for _ in range(others)),
        played_at=played_at,
    )


def days_ago(days: float) -> Instant:
    return instant(NOW - timedelta(days=days))


def read(courts: Courts, ledger: Ledger) -> ReadTheOpenCards:
    return ReadTheOpenCards(clock=Clock(NOW), courts=courts, ledger=ledger)


async def test_an_open_card_comes_back_with_everybody_else_on_that_court():
    court = a_court(played_at=days_ago(2))
    courts, ledger = Courts(courts=(court,)), Ledger()

    (found,) = await read(courts, ledger).execute(ME)

    assert found.game_id == court.game_id
    assert found.others == court.others


async def test_a_game_played_today_is_not_asked_about_yet():
    """The card opens the day after, and *not asked yet* is spelled by absence
    — the same spelling as every other reason a card is not on this list."""

    courts = Courts(courts=(a_court(played_at=days_ago(0.5)),))

    assert await read(courts, Ledger()).execute(ME) == ()


async def test_a_card_older_than_its_week_has_expired():
    courts = Courts(courts=(a_court(played_at=days_ago(9)),))

    assert await read(courts, Ledger()).execute(ME) == ()


async def test_a_card_already_answered_never_appears_again():
    court = a_court(played_at=days_ago(2))
    ledger = Ledger(closed={court.game_id})

    assert await read(Courts(courts=(court,)), ledger).execute(ME) == ()


async def test_a_game_that_never_settled_is_never_offered_at_all():
    """It is absent from the port's answer rather than filtered here — *which
    games may I be asked about* is one question, asked in one place."""

    assert await read(Courts(), Ledger()).execute(ME) == ()


async def test_somebody_elses_court_is_not_on_my_list():
    theirs = a_court(played_at=days_ago(2), rater=new_uuid())

    assert await read(Courts(courts=(theirs,)), Ledger()).execute(ME) == ()


async def test_the_card_closest_to_expiring_comes_first():
    """A deterministic order, and the one that is useful: the card that will be
    gone tomorrow is the one worth answering now."""

    older = a_court(played_at=days_ago(7))
    newer = a_court(played_at=days_ago(2))
    middle = a_court(played_at=days_ago(4))
    courts = Courts(courts=(newer, older, middle))

    found = await read(courts, Ledger()).execute(ME)

    assert [one.game_id for one in found] == [
        older.game_id,
        middle.game_id,
        newer.game_id,
    ]


async def test_the_ledger_is_asked_once_about_the_whole_list():
    """One question about every open card, never one per card."""

    open_ones = tuple(a_court(played_at=days_ago(days)) for days in (2, 3, 4))
    shut = a_court(played_at=days_ago(30))
    ledger = Ledger()

    await read(Courts(courts=open_ones + (shut,)), ledger).execute(ME)

    assert ledger.asked == [frozenset(one.game_id for one in open_ones)]


async def test_a_player_with_no_open_card_costs_the_ledger_no_question():
    ledger = Ledger()

    assert await read(Courts(), ledger).execute(ME) == ()
    assert ledger.asked == []


async def test_the_clock_is_read_once_and_handed_down():
    """The window and the port's *has it settled* are folded against the same
    instant, so a card cannot be open against one clock and unsettled against
    another."""

    courts = Courts(courts=(a_court(played_at=days_ago(2)),))

    await read(courts, Ledger()).execute(ME)

    assert courts.asked_at == [NOW]

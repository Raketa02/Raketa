"""Composing Now: what `all` resolves to, and what a stamp is.

Two behaviours are real in this ticket and both are asserted here rather than
inferred from a shape. The regions ship **empty** — later tickets fill them — so
what is genuinely under test is the envelope's shape, the resolution of the sport
filter, and the stamps.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.kernel import Instant, Sport
from app.modules.now.application.commands import ComposeNowQuery, SportFilter
from app.modules.now.application.compose_now import ComposeNow, stamp_at
from app.modules.now.domain.ports import RatedSports

AT = datetime(2026, 8, 22, 17, 30, tzinfo=timezone.utc)


class FakeRatedSports(RatedSports):
    """Hand-written stub over the port, per the repo's testing rule."""

    def __init__(self, **held: frozenset[Sport]) -> None:
        self._held = held
        self.asked: list[UUID] = []

    async def for_player(self, player_id: UUID) -> frozenset[Sport]:
        self.asked.append(player_id)
        return self._held.get(str(player_id), frozenset())


class SteppingClock:
    """A clock that answers a fixed sequence, so two composes cannot tie."""

    def __init__(self, *moments: datetime) -> None:
        self._moments = list(moments)
        self.reads = 0

    def now(self) -> Instant:
        moment = self._moments[min(self.reads, len(self._moments) - 1)]
        self.reads += 1
        return moment


def _compose(rated: RatedSports, clock) -> ComposeNow:
    return ComposeNow(rated_sports=rated, clock=clock)


async def test_all_is_the_sports_the_player_holds_a_rating_at() -> None:
    player = uuid4()
    rated = FakeRatedSports(**{str(player): frozenset({Sport.PADEL, Sport.TENNIS})})
    screen = await _compose(rated, SteppingClock(AT)).execute(
        ComposeNowQuery(player_id=player, sport=SportFilter.ALL)
    )

    assert screen.sports == frozenset({Sport.PADEL, Sport.TENNIS})
    assert rated.asked == [player]


async def test_all_with_no_rating_is_nothing_rather_than_everything() -> None:
    # The whole point of defining `all` as a rating: a shelf called *Best fit for
    # you* that ranks squash for somebody who has never held a racket is a claim
    # about inventory wearing the words of a claim about her.
    player = uuid4()
    screen = await _compose(FakeRatedSports(), SteppingClock(AT)).execute(
        ComposeNowQuery(player_id=player, sport=SportFilter.ALL)
    )

    assert screen.sports == frozenset()


@pytest.mark.parametrize(
    "chip,sport",
    [
        (SportFilter.PADEL, Sport.PADEL),
        (SportFilter.TENNIS, Sport.TENNIS),
        (SportFilter.SQUASH, Sport.SQUASH),
        (SportFilter.BADMINTON, Sport.BADMINTON),
    ],
)
async def test_a_named_chip_resolves_to_itself_and_asks_nothing(
    chip: SportFilter, sport: Sport
) -> None:
    rated = FakeRatedSports()
    screen = await _compose(rated, SteppingClock(AT)).execute(
        ComposeNowQuery(player_id=uuid4(), sport=chip)
    )

    assert screen.sports == frozenset({sport})
    # A named sport needs no rating read at all — one fewer replay on the busiest
    # path in the product.
    assert rated.asked == []


async def test_an_unrated_sport_still_resolves_to_that_sport() -> None:
    # Not an oversight: tapping a chip for an unrated sport is the moment the app
    # owes her a door into that questionnaire, and a filter that quietly resolved
    # to nothing would make the door indistinguishable from an empty city.
    screen = await _compose(FakeRatedSports(), SteppingClock(AT)).execute(
        ComposeNowQuery(player_id=uuid4(), sport=SportFilter.SQUASH)
    )

    assert screen.sports == frozenset({Sport.SQUASH})


async def test_the_default_chip_is_all() -> None:
    assert ComposeNowQuery(player_id=uuid4()).sport is SportFilter.ALL


async def test_all_three_regions_are_present_and_empty() -> None:
    screen = await _compose(FakeRatedSports(), SteppingClock(AT)).execute(
        ComposeNowQuery(player_id=uuid4())
    )

    # Present, not absent. A region makes no claim, so an empty one is an ordinary
    # render rather than an absence for the client to interpret.
    assert screen.offers.cards == ()
    assert screen.your_matches.cards == ()
    assert screen.shelves.shelves == ()


async def test_a_player_who_owes_nothing_has_no_debt_line_rather_than_a_zero() -> None:
    screen = await _compose(FakeRatedSports(), SteppingClock(AT)).execute(
        ComposeNowQuery(player_id=uuid4())
    )

    assert screen.debt is None


async def test_one_compose_reads_the_clock_once() -> None:
    # Two reads inside one command can disagree, and three regions that
    # half-disagree about when they were composed is exactly what a stamp is for
    # arbitrating.
    clock = SteppingClock(AT, AT + timedelta(seconds=5))
    screen = await _compose(FakeRatedSports(), clock).execute(
        ComposeNowQuery(player_id=uuid4())
    )

    assert clock.reads == 1
    assert screen.offers.stamp == screen.your_matches.stamp == screen.shelves.stamp


async def test_a_later_compose_stamps_higher() -> None:
    clock = SteppingClock(AT, AT + timedelta(milliseconds=1))
    compose = _compose(FakeRatedSports(), clock)
    first = await compose.execute(ComposeNowQuery(player_id=uuid4()))
    second = await compose.execute(ComposeNowQuery(player_id=uuid4()))

    assert second.offers.stamp > first.offers.stamp


def test_a_stamp_is_the_composition_instant_in_whole_milliseconds() -> None:
    assert stamp_at(AT) == int(AT.timestamp() * 1000)
    assert stamp_at(AT + timedelta(milliseconds=1)) - stamp_at(AT) == 1


def test_a_stamp_stays_inside_what_a_javascript_number_holds_exactly() -> None:
    # Both clients are TypeScript and neither parses a bigint. A millisecond
    # epoch is comfortably inside 2^53 and stays there for a quarter of a million
    # years, which is what makes an integer stamp safe to ship.
    far_future = datetime(2500, 1, 1, tzinfo=timezone.utc)
    assert stamp_at(far_future) < 2**53

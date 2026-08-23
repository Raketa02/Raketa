"""Composing Now: what `all` resolves to, what a stamp is, and what it reaches.

What is under test here is the envelope's shape, the resolution of the sport
filter, the stamps, and **the door**. The offers region and the enrolled strip
still ship empty — later tickets fill them — while the shelves region carries
whatever shelves 4 and 5 composed, so this file also asserts the *reach*: the
resolved sports, the one clock reading and the one stamp all arrive at the
arrivals composer, and the region's emptiness is now a fact about the city rather
than about the ticket.

The door's half is mostly about **what is not asked and what is not composed**. A
chip the viewer is rated at must not pay for a parked-run read; `all` must not
produce a door however little the viewer holds; and a door must be a block the
server put in the list rather than something the phone could conclude from what
is missing.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.kernel import Instant, Sport
from app.modules.now.application.commands import ComposeNowQuery, SportFilter
from app.modules.now.application.compose_enrolled import ComposeEnrolled
from app.modules.now.application.compose_now import ComposeNow, stamp_at
from app.modules.now.application.new_arrivals import ComposeNewArrivals
from app.modules.now.domain.enrolled import Enrolment
from app.modules.now.domain.ports import EnrolledMatches, ParkedRuns, RatedSports
from app.modules.now.domain.screen import Block, Door, Shelf, Stamp
from app.modules.now.domain.vocabulary import BlockType, DoorCode, ShelfCode

AT = datetime(2026, 8, 22, 17, 30, tzinfo=timezone.utc)


class FakeRatedSports(RatedSports):
    """Hand-written stub over the port, per the repo's testing rule.

    The two reads are recorded separately because they cost differently and the
    composer is expected to choose between them: `asked` is the whole-set replay,
    `asked_one` the by-pair lookup a named chip makes.
    """

    def __init__(self, **held: frozenset[Sport]) -> None:
        self._held = held
        self.asked: list[UUID] = []
        self.asked_one: list[tuple[UUID, Sport]] = []

    async def for_player(self, player_id: UUID) -> frozenset[Sport]:
        self.asked.append(player_id)
        return self._held.get(str(player_id), frozenset())

    async def holds(self, *, player_id: UUID, sport: Sport) -> bool:
        self.asked_one.append((player_id, sport))
        return sport in self._held.get(str(player_id), frozenset())


class FakeParkedRuns(ParkedRuns):
    """Whose questionnaire is part-answered, and what was asked about it."""

    def __init__(self, *parked: tuple[UUID, Sport]) -> None:
        self._parked = set(parked)
        self.asked: list[tuple[UUID, Sport]] = []

    async def parked_at(self, *, player_id: UUID, sport: Sport) -> bool:
        self.asked.append((player_id, sport))
        return (player_id, sport) in self._parked


class SteppingClock:
    """A clock that answers a fixed sequence, so two composes cannot tie."""

    def __init__(self, *moments: datetime) -> None:
        self._moments = list(moments)
        self.reads = 0

    def now(self) -> Instant:
        moment = self._moments[min(self.reads, len(self._moments) - 1)]
        self.reads += 1
        return moment


class RecordingNewArrivals(ComposeNewArrivals):
    """Shelves 4 and 5, recorded rather than composed.

    Subclasses the real collaborator rather than duplicating its signature: the
    thing worth catching is a call whose arguments have drifted, and a
    hand-written double with its own signature is the one shape that could not.
    """

    def __init__(self, *shelves: Shelf) -> None:
        self._shelves = shelves
        self.calls: list[dict] = []

    async def compose(
        self,
        *,
        viewer: UUID,
        sports: frozenset[Sport],
        now: Instant,
        stamp: Stamp,
        city: str | None = None,
    ) -> tuple[Shelf, ...]:
        self.calls.append(
            {
                "viewer": viewer,
                "sports": sports,
                "now": now,
                "stamp": stamp,
                "city": city,
            }
        )
        return self._shelves


class RecordingEnrolled(EnrolledMatches):
    """The strip's port, answering nothing and remembering what it was asked.

    A player with no matches is the ordinary case and it is the one this file
    wants: what is under test here is the *reach* — which viewer, which sport
    and which clock reading arrive — where the cards themselves are
    `tests/unit/test_compose_enrolled.py`'s subject.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def for_player(
        self, *, player_id: UUID, now: Instant
    ) -> tuple[Enrolment, ...]:
        self.calls.append({"player_id": player_id, "now": now})
        return ()


def _compose(
    rated: RatedSports,
    clock,
    arrivals: ComposeNewArrivals | None = None,
    parked: ParkedRuns | None = None,
    enrolled: EnrolledMatches | None = None,
) -> ComposeNow:
    return ComposeNow(
        rated_sports=rated,
        parked_runs=parked or FakeParkedRuns(),
        new_arrivals=arrivals or RecordingNewArrivals(),
        enrolled=ComposeEnrolled(enrolled=enrolled or RecordingEnrolled()),
        clock=clock,
    )


def _doors(blocks: tuple[Block, ...]) -> list[Door]:
    return [block for block in blocks if isinstance(block, Door)]


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
    # A named sport still needs no *set* read — one fewer replay on the busiest
    # path in the product. What it does ask is the by-pair question, because the
    # door depends on it, and that is one lookup rather than a replay of every
    # rating she holds.
    assert rated.asked == []
    assert [pair[1] for pair in rated.asked_one] == [sport]


async def test_an_unrated_sport_still_resolves_to_that_sport() -> None:
    # Not an oversight: tapping a chip for an unrated sport is the moment the app
    # owes her a door into that questionnaire, and a filter that quietly resolved
    # to nothing would make the door indistinguishable from an empty city.
    screen = await _compose(FakeRatedSports(), SteppingClock(AT)).execute(
        ComposeNowQuery(player_id=uuid4(), sport=SportFilter.SQUASH)
    )

    assert screen.sports == frozenset({Sport.SQUASH})


async def test_an_unrated_chip_composes_a_door_the_client_never_infers() -> None:
    # ADR-0084: the door is a *block on the wire, in the list, in order*. An
    # inference drawn from absent shelves would fire wrongly on any day the city
    # genuinely has nothing in a sport she *is* rated at.
    screen = await _compose(FakeRatedSports(), SteppingClock(AT)).execute(
        ComposeNowQuery(player_id=uuid4(), sport=SportFilter.SQUASH)
    )

    assert _doors(screen.shelves.shelves) == [Door(code=DoorCode.NO_RUN_YET)]


async def test_a_chip_the_player_is_rated_at_composes_no_door() -> None:
    player = uuid4()
    rated = FakeRatedSports(**{str(player): frozenset({Sport.PADEL})})
    screen = await _compose(rated, SteppingClock(AT)).execute(
        ComposeNowQuery(player_id=player, sport=SportFilter.PADEL)
    )

    assert _doors(screen.shelves.shelves) == []


async def test_a_parked_run_changes_which_sentence_the_door_shows() -> None:
    # One block type with two codes, so the client holds one row per sentence and
    # never learns that two states produced them.
    player = uuid4()
    parked = FakeParkedRuns((player, Sport.SQUASH))
    screen = await _compose(
        FakeRatedSports(), SteppingClock(AT), parked=parked
    ).execute(ComposeNowQuery(player_id=player, sport=SportFilter.SQUASH))

    assert _doors(screen.shelves.shelves) == [Door(code=DoorCode.RUN_PARKED)]


async def test_a_run_parked_at_another_sport_does_not_answer_for_this_one() -> None:
    player = uuid4()
    parked = FakeParkedRuns((player, Sport.TENNIS))
    screen = await _compose(
        FakeRatedSports(), SteppingClock(AT), parked=parked
    ).execute(ComposeNowQuery(player_id=player, sport=SportFilter.SQUASH))

    assert _doors(screen.shelves.shelves) == [Door(code=DoorCode.NO_RUN_YET)]
    assert parked.asked == [(player, Sport.SQUASH)]


async def test_a_rated_chip_never_pays_for_the_parked_run_read() -> None:
    # The second read exists only when a door is being drawn. A player rated at
    # the sport is answered and gone, which is the overwhelmingly common path.
    player = uuid4()
    rated = FakeRatedSports(**{str(player): frozenset({Sport.PADEL})})
    parked = FakeParkedRuns()
    await _compose(rated, SteppingClock(AT), parked=parked).execute(
        ComposeNowQuery(player_id=player, sport=SportFilter.PADEL)
    )

    assert parked.asked == []


async def test_all_never_composes_a_door_even_for_a_player_with_no_rating() -> None:
    # `all` is *the sports she holds a rating at*, so it names no sport she is
    # unrated at and there is nothing for a door to be about. ADR-0084 puts a
    # player holding no rating at all into the run itself rather than onto Now.
    parked = FakeParkedRuns()
    screen = await _compose(
        FakeRatedSports(), SteppingClock(AT), parked=parked
    ).execute(ComposeNowQuery(player_id=uuid4(), sport=SportFilter.ALL))

    assert _doors(screen.shelves.shelves) == []
    assert parked.asked == []


async def test_the_door_takes_the_position_the_ranked_shelves_would_occupy() -> None:
    # Above *New on Raketa* and *New clubs*, which still compose beneath it: the
    # clubs are the argument for spending the two minutes, so they belong under
    # the ask (ADR-0084).
    arrivals = RecordingNewArrivals(
        Shelf(code=ShelfCode.NEW_PLAYERS), Shelf(code=ShelfCode.NEW_CLUBS)
    )
    screen = await _compose(FakeRatedSports(), SteppingClock(AT), arrivals).execute(
        ComposeNowQuery(player_id=uuid4(), sport=SportFilter.SQUASH)
    )

    blocks = screen.shelves.shelves
    assert isinstance(blocks[0], Door)
    assert [shelf.code for shelf in blocks[1:]] == [
        ShelfCode.NEW_PLAYERS,
        ShelfCode.NEW_CLUBS,
    ]


async def test_a_door_leaves_the_ranked_shelves_absent_rather_than_empty() -> None:
    # A player with no rating at squash cannot be ranked against squash matches,
    # so there is nothing for those two shelves to hold — and an empty shelf is
    # a row claiming there is nothing worth waiting for.
    arrivals = RecordingNewArrivals(Shelf(code=ShelfCode.NEW_CLUBS))
    screen = await _compose(FakeRatedSports(), SteppingClock(AT), arrivals).execute(
        ComposeNowQuery(player_id=uuid4(), sport=SportFilter.SQUASH)
    )

    codes = {
        block.code for block in screen.shelves.shelves if isinstance(block, Shelf)
    }
    assert codes.isdisjoint(
        {ShelfCode.BEST_FIT, ShelfCode.SAME_LEVEL, ShelfCode.FULL_WORTH_WAITING}
    )


async def test_a_door_carries_which_sentence_and_nothing_else() -> None:
    # Not the sport: the client named it on the request and still holds it, and a
    # second copy on the answer is a second thing that can disagree.
    door = Door(code=DoorCode.NO_RUN_YET)

    assert {field for field in vars(door)} == {"code", "block_type"}
    assert door.block_type is BlockType.DOOR
    assert Shelf(code=ShelfCode.NEW_CLUBS).block_type is BlockType.SHELF


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


async def test_the_shelves_region_carries_whatever_composed() -> None:
    arrivals = RecordingNewArrivals(Shelf(code=ShelfCode.NEW_CLUBS))
    screen = await _compose(FakeRatedSports(), SteppingClock(AT), arrivals).execute(
        ComposeNowQuery(player_id=uuid4())
    )

    assert [shelf.code for shelf in screen.shelves.shelves] == [ShelfCode.NEW_CLUBS]


async def test_the_arrivals_composer_is_asked_with_the_resolved_sports() -> None:
    # Not with the chip: `all` is *the sports she holds a rating at*, and a shelf
    # composed against the four the registry knows would introduce her to squash
    # players she can never be ranked against.
    player = uuid4()
    rated = FakeRatedSports(**{str(player): frozenset({Sport.PADEL})})
    arrivals = RecordingNewArrivals()
    await _compose(rated, SteppingClock(AT), arrivals).execute(
        ComposeNowQuery(player_id=player, sport=SportFilter.ALL)
    )

    assert arrivals.calls[0]["sports"] == frozenset({Sport.PADEL})
    assert arrivals.calls[0]["viewer"] == player


async def test_the_arrivals_composer_shares_the_composes_one_clock_reading() -> None:
    arrivals = RecordingNewArrivals()
    clock = SteppingClock(AT, AT + timedelta(seconds=5))
    screen = await _compose(FakeRatedSports(), clock, arrivals).execute(
        ComposeNowQuery(player_id=uuid4())
    )

    assert clock.reads == 1
    assert arrivals.calls[0]["now"] == AT
    assert arrivals.calls[0]["stamp"] == screen.shelves.stamp


async def test_no_compose_can_name_the_viewers_city_yet() -> None:
    # ADR-0063 makes *where you play* a declared fact about the player and no
    # context stores one (#102). It is threaded as `None` rather than invented
    # downstream, so the day the fact has a source this is the whole change.
    arrivals = RecordingNewArrivals()
    await _compose(FakeRatedSports(), SteppingClock(AT), arrivals).execute(
        ComposeNowQuery(player_id=uuid4())
    )

    assert arrivals.calls[0]["city"] is None


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

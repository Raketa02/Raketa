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
from zoneinfo import ZoneInfo

import pytest

from app.kernel import Cover, Instant, MatchRecord, OfferKind, Sport, grosze
from app.modules.now.application.commands import ComposeNowQuery, SportFilter
from app.engines.matchfit.v1 import MatchFitEngineV1
from app.engines.pairing.v1 import PairingEngineV1
from app.modules.now.application.compose_enrolled import ComposeEnrolled
from app.modules.now.application.compose_shelves import ComposeShelves
from app.modules.now.application.scoring import MatchScorer
from tests.unit.shelf_doubles import (
    STAMP as STAMP_FOR_ARRIVALS,
    FakeCityMatches,
    FakeCommitments,
    FakeRatings,
    FakeStandbyPlaces,
    a_context,
    a_match,
    rated,
)
from app.modules.now.application.compose_now import ComposeNow, stamp_at
from app.modules.now.application.new_arrivals import ComposeNewArrivals
from app.modules.now.application.compose_offers import ComposeOffers
from app.modules.now.domain.enrolled import Enrolment
from app.modules.now.domain.cascade import Rung
from app.modules.now.domain.offers import OfferedSeat
from app.modules.now.domain.ports import (
    EnrolledMatches,
    OfferedSeats,
    ParkedRuns,
    RatedSports,
)
from app.modules.now.domain.screen import (
    Block,
    ClubCard,
    Door,
    Level,
    MatchCard,
    Money,
    PersonCard,
    Place,
    Shelf,
    Stamp,
)
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

    def __init__(self, *rows: Enrolment) -> None:
        self._rows = rows
        self.calls: list[dict[str, object]] = []

    async def for_player(
        self, *, player_id: UUID, now: Instant
    ) -> tuple[Enrolment, ...]:
        self.calls.append({"player_id": player_id, "now": now})
        return self._rows


class RecordingOffered(OfferedSeats):
    """The offers region's port, answering nothing and remembering the ask.

    A player who has been told about no seat is the ordinary case and it is the
    one this file wants: what is under test here is the *reach* — which viewer
    and which clock reading arrive — where the cards themselves are
    `tests/unit/test_compose_offers.py`'s subject.
    """

    def __init__(self, *rows: OfferedSeat) -> None:
        self._rows = rows
        self.calls: list[dict[str, object]] = []

    async def for_player(
        self, *, player_id: UUID, now: Instant
    ) -> tuple[OfferedSeat, ...]:
        self.calls.append({"player_id": player_id, "now": now})
        return self._rows

    async def one(
        self, *, player_id: UUID, match_id: UUID, now: Instant
    ) -> OfferedSeat | None:  # pragma: no cover - the compose never asks
        raise AssertionError("a compose never asks about one match")


def a_place() -> Place:
    return Place(
        club_id=uuid4(),
        club_name="Sport Club Kraków",
        zone=ZoneInfo("Europe/Warsaw"),
        cover=Cover.INDOOR,
    )


def an_offer(
    *, match_id: UUID | None = None, record: MatchRecord | None = None
) -> OfferedSeat:
    """One live offer, which is the whole of what this file needs about them."""

    return OfferedSeat(
        match_id=match_id or uuid4(),
        vacancy_id=uuid4(),
        record=record if record is not None else a_match(paid=3, starts=600),
        where=a_place(),
        kind=OfferKind.OPEN,
        rung=Rung.IN_THE_BAND,
        share=Money(amount=grosze(3800)),
        court_total=Money(amount=grosze(15200)),
        offered_at=AT,
    )


def an_enrolment(
    *, match_id: UUID, record: MatchRecord, **kwargs
) -> Enrolment:
    return Enrolment(
        match_id=match_id,
        record=record,
        where=a_place(),
        share=Money(amount=grosze(3800)),
        court_total=Money(amount=grosze(15200)),
        **kwargs,
    )


def _empty_shelves() -> ComposeShelves:
    """The ranked funnel over an empty city, which composes nothing at all.

    This file's subject is the envelope and the reach — which viewer, which
    sport, which clock reading, and which blocks come back in which order — and
    the funnel's own answers are `tests/unit/test_compose_shelves.py`'s. An empty
    city is the cheapest way to have a real one here rather than a stand-in, so
    a signature change reaches this file rather than passing it.
    """

    return ComposeShelves(
        city=FakeCityMatches(),
        commitments=FakeCommitments(),
        standby=FakeStandbyPlaces(),
        ratings=FakeRatings(),
        scorer=MatchScorer(pairing=PairingEngineV1(), matchfit=MatchFitEngineV1()),
    )


def _compose(
    rated: RatedSports,
    clock,
    arrivals: ComposeNewArrivals | None = None,
    parked: ParkedRuns | None = None,
    enrolled: EnrolledMatches | None = None,
    shelves: ComposeShelves | None = None,
    offered: OfferedSeats | None = None,
) -> ComposeNow:
    return ComposeNow(
        rated_sports=rated,
        parked_runs=parked or FakeParkedRuns(),
        new_arrivals=arrivals or RecordingNewArrivals(),
        shelves=shelves or _empty_shelves(),
        enrolled=ComposeEnrolled(enrolled=enrolled or RecordingEnrolled()),
        offers=ComposeOffers(offered=offered or RecordingOffered()),
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


async def test_the_offers_composer_is_asked_with_the_named_chip() -> None:
    # The **named chip** and never the resolved set, exactly as the strip takes
    # it. The two readings of `all` coincide here rather than merely agreeing
    # today — the cascade's pool excludes anybody holding no rating at the
    # match's sport, so no offer can exist outside *the sports she holds a
    # rating at*.
    player = uuid4()
    offered = RecordingOffered()
    await _compose(
        FakeRatedSports(), SteppingClock(AT), offered=offered
    ).execute(ComposeNowQuery(player_id=player, sport=SportFilter.PADEL))

    assert offered.calls == [{"player_id": player, "now": AT}]


async def test_the_region_takes_the_chip_and_never_the_resolved_set() -> None:
    """The case that tells the two apart, which one rated sport cannot.

    `all` resolves to *the sports she holds a rating at*, and a player rated at
    two sports resolves to a set of two — where the chip is `None` and hides
    nothing. Passing the resolved set would make the region show one of her
    sports and drop the other, chosen by whatever the set iterates first.
    """

    player = uuid4()
    rated_at = FakeRatedSports(
        **{str(player): frozenset({Sport.PADEL, Sport.TENNIS})}
    )
    padel = an_offer(record=a_match(paid=3, starts=600, sport=Sport.PADEL))
    tennis = an_offer(record=a_match(paid=1, starts=600, sport=Sport.TENNIS))
    screen = await _compose(
        rated_at, SteppingClock(AT), offered=RecordingOffered(padel, tennis)
    ).execute(ComposeNowQuery(player_id=player, sport=SportFilter.ALL))

    assert len(screen.offers.cards) == 2


async def test_the_offers_region_shares_the_composes_one_clock_reading() -> None:
    offered = RecordingOffered()
    clock = SteppingClock(AT, AT + timedelta(seconds=5))
    screen = await _compose(
        FakeRatedSports(), clock, offered=offered
    ).execute(ComposeNowQuery(player_id=uuid4()))

    assert clock.reads == 1
    assert offered.calls[0]["now"] == AT
    assert screen.offers.stamp == stamp_at(AT)


async def test_a_match_the_offers_region_speaks_for_leaves_the_queue_card() -> None:
    """One match, one card, and the region that holds it is the ladder's answer.

    Rung 1's own audience: a player on a match's standby queue is the first
    person the cascade tells, so she holds a queue place *and* a live offer. Rung
    6 sits above rung 7 — *"telling her she is still queueing while the seat is
    hers to take would be the one sentence that makes standby worthless"* — and
    the strip is where that ruling is applied, because two regions cannot each
    apply it to their own.
    """

    match_id = uuid4()
    record = a_match(paid=3, starts=600)
    screen = await _compose(
        FakeRatedSports(),
        SteppingClock(AT),
        enrolled=RecordingEnrolled(
            an_enrolment(match_id=match_id, record=record, on_standby=True)
        ),
        offered=RecordingOffered(an_offer(match_id=match_id, record=record)),
    ).execute(ComposeNowQuery(player_id=uuid4()))

    assert [card.match_id for card in screen.offers.cards] == [match_id]
    assert screen.your_matches.cards == ()


async def test_a_seat_of_her_own_is_never_taken_off_the_strip_by_a_region() -> None:
    """Narrowed to the one membership that confers nothing.

    A seat, a departure or a live claim is money or a clock of her own, and no
    region above may take that card off the strip. The two answers are computed
    in two files off two reads, so if they ever disagree the cost is a duplicate
    card rather than a missing one.
    """

    match_id = uuid4()
    record = a_match(paid=3, starts=600)
    screen = await _compose(
        FakeRatedSports(),
        SteppingClock(AT),
        enrolled=RecordingEnrolled(
            an_enrolment(match_id=match_id, record=record, holds_seat=True)
        ),
        offered=RecordingOffered(an_offer(match_id=match_id, record=record)),
    ).execute(ComposeNowQuery(player_id=uuid4()))

    assert [card.match_id for card in screen.your_matches.cards] == [match_id]


async def test_an_offer_silences_emphasis_across_the_whole_screen() -> None:
    """ADR-0037's rule, composed end to end rather than asserted on a stand-in.

    An offer is a seat with a clock on it at the very top of Now and it is the
    loudest thing the product has to say; a suggestion shouting underneath it
    would be two things competing to be the one thing she does next.
    """

    player = uuid4()
    rated_at = FakeRatedSports(**{str(player): frozenset({Sport.PADEL})})
    city = FakeCityMatches(a_context(record=a_match(paid=3, starts=600)))
    shelves = ComposeShelves(
        city=city,
        commitments=FakeCommitments(),
        standby=FakeStandbyPlaces(),
        ratings=FakeRatings(PADEL=rated(240)),
        scorer=MatchScorer(pairing=PairingEngineV1(), matchfit=MatchFitEngineV1()),
    )

    loud = await _compose(rated_at, SteppingClock(AT), shelves=shelves).execute(
        ComposeNowQuery(player_id=player, sport=SportFilter.PADEL)
    )
    quiet = await _compose(
        rated_at,
        SteppingClock(AT),
        shelves=shelves,
        offered=RecordingOffered(an_offer()),
    ).execute(ComposeNowQuery(player_id=player, sport=SportFilter.PADEL))

    assert any(_emphatic(loud)), "the negative control never shouted"
    assert not any(_emphatic(quiet))


def _emphatic(screen) -> list[bool]:
    return [
        card.emphasis
        for block in screen.shelves.shelves
        if isinstance(block, Shelf)
        for card in block.cards
        if isinstance(card, MatchCard)
    ]


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


# --- the two passes over the composed screen --------------------------------


def _shelves_over(*contexts, level: int = 240) -> ComposeShelves:
    """The real funnel over a city, so the scores emphasis reads are real ones.

    A stub answering a hand-made `Ranked` would let this file assert that a
    number reached the pass without ever asserting that the funnel produced one,
    which is the half `#77` inherits rather than owns.
    """

    return ComposeShelves(
        city=FakeCityMatches(*contexts),
        commitments=FakeCommitments(),
        standby=FakeStandbyPlaces(),
        ratings=FakeRatings(PADEL=rated(level)),
        scorer=MatchScorer(pairing=PairingEngineV1(), matchfit=MatchFitEngineV1()),
    )


def _emphatic(screen) -> list[UUID]:
    found: list[UUID] = []
    for block in screen.shelves.shelves:
        if not isinstance(block, Shelf):
            continue
        found.extend(card.match_id for card in block.cards if card.emphasis)
    return found


async def test_the_composed_screen_carries_at_most_one_emphatic_card() -> None:
    """Three matches that each clear all three gates, one flag between them.

    The cap is the guarantee ADR-0037 rests the screen's one loud colour on, and
    it is a property of the *screen* — so it is asserted where a screen exists
    rather than where a shelf does.
    """

    player = uuid4()
    rated_at = FakeRatedSports(**{str(player): frozenset({Sport.PADEL})})
    contexts = [
        a_context(record=a_match(paid=3, starts=n * 180)) for n in range(3)
    ]
    screen = await _compose(
        rated_at, SteppingClock(AT), shelves=_shelves_over(*contexts)
    ).execute(ComposeNowQuery(player_id=player, sport=SportFilter.PADEL))

    assert len(_emphatic(screen)) == 1


async def test_a_screen_with_nothing_over_the_gates_shouts_about_nothing() -> None:
    # A quiet screen is the ordinary one: 4,3 % of realistic scores reach 90, and
    # emphasis means something only because it is rare.
    player = uuid4()
    rated_at = FakeRatedSports(**{str(player): frozenset({Sport.PADEL})})
    screen = await _compose(
        rated_at,
        SteppingClock(AT),
        shelves=_shelves_over(a_context(record=a_match(paid=1)), level=300),
    ).execute(ComposeNowQuery(player_id=player, sport=SportFilter.PADEL))

    assert _emphatic(screen) == []


async def test_the_repeat_guard_runs_over_the_composed_list() -> None:
    """Two arrival shelves saying the same thing, and the lower one goes.

    Composed rather than hand-built, so the pass is asserted where it actually
    runs: a session that dropped the call from `execute` fails here and nowhere
    in `test_now_composition.py`.
    """

    twice = PersonCard(
        player_id=uuid4(),
        stamp=STAMP_FOR_ARRIVALS,
        nickname="ala",
        level=Level(value=2.7, provisional=True),
    )
    arrivals = RecordingNewArrivals(
        Shelf(code=ShelfCode.NEW_PLAYERS, cards=(twice,)),
        Shelf(code=ShelfCode.NEW_CLUBS, cards=(twice,)),
    )
    screen = await _compose(FakeRatedSports(), SteppingClock(AT), arrivals).execute(
        ComposeNowQuery(player_id=uuid4(), sport=SportFilter.ALL)
    )

    assert [block.code for block in screen.shelves.shelves] == [ShelfCode.NEW_PLAYERS]


async def test_two_arrival_shelves_that_differ_both_stand() -> None:
    arrivals = RecordingNewArrivals(
        Shelf(
            code=ShelfCode.NEW_PLAYERS,
            cards=(
                PersonCard(
                    player_id=uuid4(),
                    stamp=STAMP_FOR_ARRIVALS,
                    nickname="ala",
                    level=Level(value=2.7, provisional=True),
                ),
            ),
        ),
        Shelf(
            code=ShelfCode.NEW_CLUBS,
            cards=(
                ClubCard(
                    club_id=uuid4(), stamp=STAMP_FOR_ARRIVALS, name="Sport Club"
                ),
            ),
        ),
    )
    screen = await _compose(FakeRatedSports(), SteppingClock(AT), arrivals).execute(
        ComposeNowQuery(player_id=uuid4(), sport=SportFilter.ALL)
    )

    assert [block.code for block in screen.shelves.shelves] == [
        ShelfCode.NEW_PLAYERS,
        ShelfCode.NEW_CLUBS,
    ]

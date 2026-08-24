"""The offers region: the order, the four seat rules, and the refusal path.

The region above everything. Three of its claims are structural — no floor, no
cap, no caption — and the rest are rules over one row: which seats are still
takeable, what order they are in, which situation the ladder answers for a viewer
carrying an offer, and what a card prints when the seat has gone.

The composer is driven through its port with a hand-written stub, so everything
below is about the *rules* and nothing about a database. What the adapter reads is
`tests/unit/test_offered_adapter.py`'s.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.kernel import (
    Cover,
    Instant,
    Minutes,
    MatchKind,
    MatchRecord,
    OfferKind,
    PayModel,
    SeatShare,
    Situation,
    Sport,
    deadlines,
    grosze,
    hours,
    minutes,
    seat_price,
    shifted,
    situation,
)
from app.modules.now.application.compose_offers import (
    ComposeOffers,
    offer_card_of,
    offered_matches,
)
from app.modules.now.domain.cascade import Rung
from app.modules.now.domain.offers import OfferedSeat
from app.modules.now.domain.ports import OfferedSeats
from app.modules.now.domain.screen import Money, Place
from app.modules.now.domain.vocabulary import ActCode, CardHoldReason

from tests.unit.match_records import START, a_match, at

WARSAW = ZoneInfo("Europe/Warsaw")
STAMP = 1_771_000_000_000
SHARE = grosze(3800)
COURT = grosze(15200)

#: Half an hour before the start, which is the default club's join cutoff and
#: therefore the moment every offer below dies.
CUTOFF = at(-30)


class StubOffered(OfferedSeats):
    """The port, hand-written, answering whatever a case set up."""

    def __init__(self, *rows: OfferedSeat) -> None:
        self._rows = rows
        self.asked: list[tuple[UUID, Instant]] = []

    async def for_player(
        self, *, player_id: UUID, now: Instant
    ) -> tuple[OfferedSeat, ...]:
        self.asked.append((player_id, now))
        return self._rows

    async def one(
        self, *, player_id: UUID, match_id: UUID, now: Instant
    ) -> OfferedSeat | None:
        return next(
            (row for row in self._rows if row.match_id == match_id), None
        )


def a_place(**kwargs) -> Place:
    return Place(
        **{
            "club_id": uuid4(),
            "club_name": "Sport Club Kraków",
            "zone": WARSAW,
            "cover": Cover.INDOOR,
            **kwargs,
        }
    )


def offered(record: MatchRecord | None = None, **kwargs) -> OfferedSeat:
    return OfferedSeat(
        **{
            "match_id": uuid4(),
            "vacancy_id": uuid4(),
            "record": record if record is not None else a_match(paid=3),
            "where": a_place(),
            "kind": OfferKind.OPEN,
            "rung": Rung.IN_THE_BAND,
            "share": Money(amount=SHARE),
            "court_total": Money(amount=COURT),
            "offered_at": at(-600),
            **kwargs,
        }
    )


async def compose(*rows: OfferedSeat, now: Instant, sport: Sport | None = None):
    return await ComposeOffers(offered=StubOffered(*rows)).compose(
        viewer=uuid4(), sport=sport, now=now, stamp=STAMP
    )


# -- what is still there ------------------------------------------------------


async def test_a_seat_that_is_still_free_is_on_the_region() -> None:
    row = offered(a_match(paid=3))
    region = await compose(row, now=at(-600))

    assert [card.match_id for card in region.cards] == [row.match_id]
    assert region.stamp == STAMP


async def test_a_match_that_filled_is_no_longer_on_the_region() -> None:
    # Somebody else was faster. Nothing was withdrawn and nothing was deleted —
    # the offer row is exactly where the cascade wrote it, and the region is
    # answering *is the seat still there* about the match (ADR-0061).
    region = await compose(offered(a_match(paid=4)), now=at(-600))

    assert region.cards == ()


async def test_a_cancelled_match_is_no_longer_on_the_region() -> None:
    region = await compose(
        offered(a_match(paid=3, club_cancelled=True)), now=at(-600)
    )

    assert region.cards == ()


async def test_the_join_cutoff_is_the_moment_the_offer_dies() -> None:
    # A minute either side, because the cutoff is the one clock an open call
    # runs out on — `Match.open_claim` enforces exactly this instant and no
    # other, so a region drawing a card past it is offering a door that will not
    # open.
    row = offered(a_match(paid=3))

    assert (await compose(row, now=shifted(CUTOFF, minutes(-1)))).cards != ()
    assert (await compose(row, now=CUTOFF)).cards == ()


async def test_a_match_that_is_already_hers_is_not_offered_to_her_again() -> None:
    # A seat, a live claim or a departure of her own: the three the pool means by
    # *already mine*, and the state a player is in the moment after she takes the
    # seat. Her card belongs to the strip then, and one match is one card.
    region = await compose(offered(already_mine=True), now=at(-600))

    assert region.cards == ()


# -- the order ----------------------------------------------------------------


async def test_the_region_is_ordered_soonest_to_expire() -> None:
    # Never soonest-to-play. The two orders agree at one club, so the case that
    # tells them apart needs two: the match played **second** closes joining four
    # hours before it starts, and therefore dies **first**. Sorting by the hour of
    # the game would put the seat with an hour left below the one with ten.
    played_first = offered(a_match(paid=3), match_id=UUID(int=1))
    dies_first = offered(_dying_first(), match_id=UUID(int=2))
    region = await compose(played_first, dies_first, now=at(-600))

    assert [card.match_id for card in region.cards] == [
        UUID(int=2),
        UUID(int=1),
    ]


async def test_two_seats_dying_together_are_ordered_by_when_she_was_told() -> None:
    first = offered(match_id=UUID(int=2), offered_at=at(-600))
    second = offered(match_id=UUID(int=1), offered_at=at(-300))
    region = await compose(second, first, now=at(-200))

    assert [card.match_id for card in region.cards] == [
        UUID(int=2),
        UUID(int=1),
    ]


async def test_the_last_comparator_is_total() -> None:
    # Without one the order is the query plan, and two identical requests
    # reshuffle the region under her thumb (`FEED_ORDER`'s fourth comparator,
    # made about this region).
    one = offered(match_id=UUID(int=1), offered_at=at(-600))
    two = offered(match_id=UUID(int=2), offered_at=at(-600))
    forwards = await compose(one, two, now=at(-500))
    backwards = await compose(two, one, now=at(-500))

    assert [card.match_id for card in forwards.cards] == [
        UUID(int=1),
        UUID(int=2),
    ]
    assert [card.match_id for card in backwards.cards] == [
        card.match_id for card in forwards.cards
    ]


async def test_the_region_has_no_cap() -> None:
    # Every shelf has one and this must not: the row is uncapped (ADR-0052), and
    # hiding an offer somebody waited weeks for costs her a game to save a
    # scroll.
    rows = [offered(match_id=UUID(int=index)) for index in range(1, 13)]
    region = await compose(*rows, now=at(-600))

    assert len(region.cards) == 12


# -- the two situations -------------------------------------------------------


async def test_an_open_call_resolves_to_seat_opened() -> None:
    region = await compose(offered(kind=OfferKind.OPEN), now=at(-600))

    assert region.cards[0].situation.situation is Situation.SEAT_OPENED


async def test_an_exclusive_offer_resolves_to_seat_offered() -> None:
    # ADR-0061 retired the exclusive offer and the kernel kept the name, *"because
    # the ladder must be able to say the sentence the moment an exclusive offer
    # exists, not a release later"*. The store carries the kind, so the two are
    # two situations rather than one with a comment.
    region = await compose(offered(kind=OfferKind.EXCLUSIVE), now=at(-600))

    assert region.cards[0].situation.situation is Situation.SEAT_OFFERED


async def test_a_seat_that_has_gone_says_so_rather_than_going_on_offering() -> None:
    # The refusal path, on the card rather than in the region. Rung 6 answers an
    # offer situation for anybody carrying an offer and never looks at whether
    # the match is full, so the judgement is made once, here — and the recomposed
    # card resolves to what the match is actually doing.
    row = offered(a_match(paid=4))
    card = offer_card_of(row, now=at(-600), stamp=STAMP)

    assert card.situation.situation is not Situation.SEAT_OPENED
    assert card.situation.situation is situation(row.record, None, at(-600))
    assert card.act is None


# -- the card -----------------------------------------------------------------


async def test_the_card_names_take_seat() -> None:
    region = await compose(offered(), now=at(-600))

    assert region.cards[0].act is ActCode.TAKE_SEAT


async def test_the_card_offers_no_exit() -> None:
    region = await compose(offered(), now=at(-600))

    assert region.cards[0].may_depart is False
    assert region.cards[0].seat_claim is None


async def test_the_card_carries_no_fit_and_never_shouts() -> None:
    # A badge is a judgement about a *suggestion* and this is not one; emphasis is
    # at most one card on the whole screen and an offer silences it entirely.
    region = await compose(offered(), now=at(-600))

    assert region.cards[0].fit is None
    assert region.cards[0].emphasis is False


async def test_the_price_is_the_rescue_tier_running_now() -> None:
    # ADR-0061 prices the open call *"full from the vacancy, 50 % from the rescue
    # deadline"*, and the two differ exactly when that deadline passed between
    # the telling and the tap. A card quoting the older, dearer number would take
    # her money at a price the platform has stopped charging.
    record = a_match(paid=3, committed_at=at(-2000))
    row = offered(record)
    rescue = _rescue(record)

    before = offer_card_of(row, now=shifted(rescue, minutes(-1)), stamp=STAMP)
    after = offer_card_of(row, now=shifted(rescue, minutes(1)), stamp=STAMP)

    assert int(before.price.amount) == int(SHARE)
    assert int(after.price.amount) == int(
        seat_price(record, SeatShare(SHARE), shifted(rescue, minutes(1)))
    )
    assert int(after.price.amount) < int(before.price.amount)


async def test_the_card_counts_in_money_and_names_the_court_total() -> None:
    region = await compose(offered(a_match(paid=2, held=1)), now=at(-600))
    facts = region.cards[0].situation.facts

    assert (facts.counts.seats, facts.counts.paid, facts.counts.held) == (4, 2, 1)
    assert facts.court_total == Money(amount=COURT)


async def test_the_card_names_why_a_court_is_being_kept_aside() -> None:
    """The hold note is the strip's line and an offer card draws the same one.

    A seat freeing on a match that is *holding a court* is exactly the seat worth
    racing for — the court is already aside and one player is what stands between
    the evening and a game — so a card that dropped the note would lose the half
    of the sentence that says why the offer matters.
    """

    held = offered(a_match(paid=3, committed_at=at(-2000)))
    card = offer_card_of(held, now=at(-600), stamp=STAMP)

    assert card.situation.facts.hold is not None
    assert card.situation.facts.hold.reason is CardHoldReason.COMMITTED


async def test_a_card_describing_no_court_names_no_hold() -> None:
    """The negative half: a full match is not describing a court at all."""

    card = offer_card_of(offered(a_match(paid=4)), now=at(-600), stamp=STAMP)

    assert card.situation.facts.hold is None


async def test_a_private_court_offers_a_seat_and_names_nobody_elses_money() -> None:
    # `guaranteed` and `recovered` are what a private court's *buyer* has at
    # stake. She is not the buyer, and a card offering her a seat would be
    # printing somebody else's liability beside the price she is being asked for.
    record = a_match(
        paid=1, kind=MatchKind.PRIVATE, pay_model=PayModel.SPLIT, open_seats=2
    )
    card = offer_card_of(offered(record), now=at(-600), stamp=STAMP)

    assert card.situation.facts.owner is None


async def test_the_court_is_named_only_once_it_is_hers_to_know() -> None:
    # Unlike a shelf card — which can never reach the naming window, because
    # eligibility stops at the join cutoff — an offer can: a club with a short
    # cutoff leaves a seat takeable inside it, and a player racing for a seat
    # starting in ten minutes is exactly who wants the court number.
    row = offered(_cutoff(minutes(5)), court="Court 3")

    assert offer_card_of(row, now=at(-60), stamp=STAMP).situation.facts.court is None
    assert (
        offer_card_of(row, now=at(-10), stamp=STAMP).situation.facts.court == "Court 3"
    )


async def test_the_card_counts_down_to_the_ladders_next_boundary() -> None:
    row = offered(a_match(paid=3))
    card = offer_card_of(row, now=at(-600), stamp=STAMP)

    assert card.clock is not None
    assert card.clock > at(-600)


# -- the sport bar ------------------------------------------------------------


async def test_a_named_chip_hides_the_other_sports() -> None:
    padel = offered(a_match(paid=3, sport=Sport.PADEL))
    tennis = offered(a_match(paid=1, sport=Sport.TENNIS))
    region = await compose(padel, tennis, now=at(-600), sport=Sport.TENNIS)

    assert [card.match_id for card in region.cards] == [tennis.match_id]


async def test_all_hides_nothing() -> None:
    padel = offered(a_match(paid=3, sport=Sport.PADEL))
    tennis = offered(a_match(paid=1, sport=Sport.TENNIS))
    region = await compose(padel, tennis, now=at(-600), sport=None)

    assert len(region.cards) == 2


# -- what the strip is told ---------------------------------------------------


async def test_the_matches_this_region_speaks_for_are_named_for_the_strip() -> None:
    row = offered()
    region = await compose(row, now=at(-600))

    assert offered_matches(region) == frozenset({row.match_id})


async def test_a_seat_that_has_gone_leaves_nothing_for_the_strip_to_yield_to() -> None:
    region = await compose(offered(a_match(paid=4)), now=at(-600))

    assert offered_matches(region) == frozenset()


# -- the port -----------------------------------------------------------------


async def test_the_port_is_asked_for_this_viewer_at_this_instant() -> None:
    port = StubOffered()
    player = uuid4()
    await ComposeOffers(offered=port).compose(
        viewer=player, sport=None, now=at(-600), stamp=STAMP
    )

    assert port.asked == [(player, at(-600))]


def _dying_first() -> MatchRecord:
    """A match played three hours later whose joining closes four hours before it.

    The one shape that separates *soonest to expire* from *soonest to play*: at
    one club the two orders agree, and a suite built only of those could not tell
    which rule the region was following.
    """

    return _with_cutoff(
        replace(a_match(paid=3), start=shifted(START, hours(3))), hours(4)
    )


def _cutoff(cut: Minutes) -> MatchRecord:
    """A match at the fixed start whose club closes joining ``cut`` before it."""

    return _with_cutoff(a_match(paid=3), cut)


def _with_cutoff(record: MatchRecord, cut: Minutes) -> MatchRecord:
    return replace(record, policy=replace(record.policy, join_cut=cut))


def _rescue(record: MatchRecord) -> Instant:
    return deadlines(record).rescue

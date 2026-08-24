"""Taking a seat: what applied, what came back, and what a refusal looks like.

The act the offers region exists to make possible, and the first thing in the
product that moves a card **between** two regions. Three claims are under test
here and the third is the ticket's own point:

- a tap that applied answers ``claimed`` with both viewer-owned regions, whole;
- a tap that did not moved nothing, so neither region rides back;
- **a refusal is what a success returns** — the corrected card, in place, saying
  the seat has gone rather than an error saying so.

The use case is driven through hand-written stubs, so nothing below is about a
database. What the adapter does to the aggregate is
`tests/unit/test_claims_adapter.py`'s.
"""

from __future__ import annotations

from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.kernel import (
    Cover,
    Instant,
    MatchRecord,
    OfferKind,
    Situation,
    grosze,
    minutes,
    shifted,
)
from app.modules.matches.domain.errors import (
    ClaimCoolingDown,
    MatchIsFull,
    MatchNotFound,
    PlayerAlreadyClaiming,
    SeatAlreadyClaimed,
)
from app.modules.now.application.commands import SportFilter
from app.modules.now.application.compose_enrolled import ComposeEnrolled
from app.modules.now.application.compose_offers import ComposeOffers
from app.modules.now.application.seat import TakeSeatCommand, TakeTheSeat
from app.modules.now.domain.enrolled import Enrolment
from app.modules.now.domain.cascade import Rung
from app.modules.now.domain.offers import OfferedSeat
from app.modules.now.domain.ports import Claims, EnrolledMatches, OfferedSeats
from app.modules.now.domain.screen import CardChanged, CardGone, Money, Place
from app.modules.now.domain.vocabulary import ActCode

from tests.unit.match_records import a_match, at

WARSAW = ZoneInfo("Europe/Warsaw")
SHARE = grosze(3800)
COURT = grosze(15200)
NOW = at(-600)


class FixedClock:
    def __init__(self, moment: Instant = NOW) -> None:
        self._moment = moment

    def now(self) -> Instant:
        return self._moment


class RecordingUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:  # pragma: no cover - never taken here
        raise AssertionError("nothing here rolls back")


class StubClaims(Claims):
    """The write, hand-written: it takes the seat, or refuses in a named way."""

    def __init__(self, *, refusal: Exception | None = None) -> None:
        self._refusal = refusal
        self.taken: list[tuple[UUID, UUID, Instant]] = []

    async def take(
        self, *, match_id: UUID, player_id: UUID, at: Instant
    ) -> Instant:
        self.taken.append((match_id, player_id, at))
        if self._refusal is not None:
            raise self._refusal
        return shifted(at, minutes(5))


class StubOffered(OfferedSeats):
    def __init__(self, *rows: OfferedSeat) -> None:
        self._rows = rows

    async def for_player(
        self, *, player_id: UUID, now: Instant
    ) -> tuple[OfferedSeat, ...]:
        return self._rows

    async def one(
        self, *, player_id: UUID, match_id: UUID, now: Instant
    ) -> OfferedSeat | None:
        return next((row for row in self._rows if row.match_id == match_id), None)


class StubEnrolled(EnrolledMatches):
    def __init__(self, *rows: Enrolment) -> None:
        self._rows = rows
        self.asked_one: list[tuple[UUID, UUID]] = []

    async def for_player(
        self, *, player_id: UUID, now: Instant
    ) -> tuple[Enrolment, ...]:
        return self._rows

    async def one(
        self, *, player_id: UUID, match_id: UUID, now: Instant
    ) -> Enrolment | None:
        self.asked_one.append((player_id, match_id))
        return next((row for row in self._rows if row.match_id == match_id), None)


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
            "offered_at": at(-700),
            **kwargs,
        }
    )


def enrolled(record: MatchRecord | None = None, **kwargs) -> Enrolment:
    return Enrolment(
        **{
            "match_id": uuid4(),
            "record": record if record is not None else a_match(paid=3),
            "where": a_place(),
            "share": Money(amount=SHARE),
            "court_total": Money(amount=COURT),
            "holds_seat": False,
            **kwargs,
        }
    )


def a_use_case(
    *,
    claims: StubClaims | None = None,
    offers: tuple[OfferedSeat, ...] = (),
    rows: tuple[Enrolment, ...] = (),
    uow: RecordingUnitOfWork | None = None,
    enrolled_port: StubEnrolled | None = None,
) -> TakeTheSeat:
    offered_port = StubOffered(*offers)
    strip_port = enrolled_port if enrolled_port is not None else StubEnrolled(*rows)
    return TakeTheSeat(
        claims=claims or StubClaims(),
        offered=offered_port,
        enrolled=strip_port,
        offers=ComposeOffers(offered=offered_port),
        strip=ComposeEnrolled(enrolled=strip_port),
        uow=uow or RecordingUnitOfWork(),
        clock=FixedClock(),
    )


def a_command(match_id: UUID, **kwargs) -> TakeSeatCommand:
    return TakeSeatCommand(
        **{"player_id": uuid4(), "match_id": match_id, **kwargs}
    )


# -- the tap applied ----------------------------------------------------------


async def test_taking_a_free_seat_claims_it_and_says_so() -> None:
    row = offered()
    claim = enrolled(
        row.record,
        match_id=row.match_id,
        claim_expires_at=shifted(NOW, minutes(5)),
    )
    answer = await a_use_case(offers=(row,), rows=(claim,)).execute(
        a_command(row.match_id)
    )

    assert answer.claimed is True
    assert isinstance(answer.update, CardChanged)
    assert answer.update.card.match_id == row.match_id


async def test_a_claim_puts_its_five_minutes_on_the_card() -> None:
    # ADR-0081's window, and the clock a card counts down to while it runs: her
    # own claim is the next thing that happens to her whether she acts or not.
    row = offered()
    expires = shifted(NOW, minutes(5))
    claim = enrolled(row.record, match_id=row.match_id, claim_expires_at=expires)
    answer = await a_use_case(offers=(row,), rows=(claim,)).execute(
        a_command(row.match_id)
    )

    assert isinstance(answer.update, CardChanged)
    assert answer.update.card.seat_claim is not None
    assert answer.update.card.seat_claim.expires_at == expires
    assert answer.update.card.clock == expires


async def test_a_card_under_a_live_claim_shows_no_exit_control() -> None:
    row = offered()
    claim = enrolled(
        row.record,
        match_id=row.match_id,
        claim_expires_at=shifted(NOW, minutes(5)),
    )
    answer = await a_use_case(offers=(row,), rows=(claim,)).execute(
        a_command(row.match_id)
    )

    assert isinstance(answer.update, CardChanged)
    assert answer.update.card.may_depart is False


async def test_both_viewer_owned_regions_come_back_whole() -> None:
    # ADR-0070: *"an accepted offer changes three things at once — the offer is
    # gone, the match belongs in the strip"*. This is the first act in the product
    # that moves a card between two regions, and therefore the first that needs
    # them.
    row = offered()
    claim = enrolled(
        row.record,
        match_id=row.match_id,
        claim_expires_at=shifted(NOW, minutes(5)),
    )
    answer = await a_use_case(offers=(row,), rows=(claim,)).execute(
        a_command(row.match_id)
    )

    assert answer.your_matches is not None
    assert [card.match_id for card in answer.your_matches.cards] == [row.match_id]
    assert answer.offers is not None


async def test_the_offer_leaves_the_offers_region_the_moment_it_is_hers() -> None:
    row = offered(already_mine=True)
    claim = enrolled(
        row.record,
        match_id=row.match_id,
        claim_expires_at=shifted(NOW, minutes(5)),
    )
    answer = await a_use_case(offers=(row,), rows=(claim,)).execute(
        a_command(row.match_id)
    )

    assert answer.offers is not None
    assert answer.offers.cards == ()


async def test_the_strip_yields_to_the_region_in_the_write_too() -> None:
    """The same ruling the compose applies, applied to the same tap.

    A player who was on the queue and then told about the seat holds a queue
    place *and* a live offer, and both answers here would draw a card for one
    match. It is the write that has to say so as well: a screen corrected off a
    tap that showed the match twice would be a screen the next compose disagrees
    with.
    """

    row = offered()
    queued = enrolled(row.record, match_id=row.match_id, on_standby=True)
    answer = await a_use_case(
        claims=StubClaims(refusal=MatchIsFull()),
        offers=(row,),
        rows=(queued,),
    ).execute(a_command(row.match_id))
    # A refusal sends no region, so the claim is asserted on a tap that applied:
    # the seat is free and she takes it.
    applied = await a_use_case(offers=(row,), rows=(queued,)).execute(
        a_command(row.match_id)
    )

    assert answer.claimed is False
    assert applied.offers is not None
    assert [card.match_id for card in applied.offers.cards] == [row.match_id]
    assert applied.your_matches is not None
    assert applied.your_matches.cards == ()


async def test_the_regions_are_recomposed_under_the_chip_she_is_looking_at() -> None:
    # A region recomposed under a different filter would replace her filtered
    # screen with somebody else's.
    padel = offered(a_match(paid=3))
    answer = await a_use_case(offers=(padel,), rows=()).execute(
        a_command(padel.match_id, sport=SportFilter.TENNIS)
    )

    assert answer.offers is not None
    assert answer.offers.cards == ()


async def test_the_write_commits_exactly_once() -> None:
    uow = RecordingUnitOfWork()
    row = offered()
    await a_use_case(offers=(row,), uow=uow).execute(a_command(row.match_id))

    assert uow.commits == 1


async def test_the_claim_is_taken_for_this_viewer_at_this_instant() -> None:
    claims = StubClaims()
    row = offered()
    command = a_command(row.match_id)
    await a_use_case(claims=claims, offers=(row,)).execute(command)

    assert claims.taken == [(command.match_id, command.player_id, NOW)]


# -- the refusal path ---------------------------------------------------------


@pytest.mark.parametrize(
    "refusal", [MatchIsFull(), SeatAlreadyClaimed()], ids=["full", "claimed"]
)
async def test_a_seat_that_has_gone_answers_what_a_success_answers(
    refusal: Exception,
) -> None:
    # ADR-0070's rule, and the reason this route has no error path for the ordinary
    # race: *"tapping an offer somebody else already took returns what a success
    # returns: what is true now."*
    row = offered(a_match(paid=4))
    answer = await a_use_case(
        claims=StubClaims(refusal=refusal), offers=(row,)
    ).execute(a_command(row.match_id))

    assert answer.claimed is False
    assert isinstance(answer.update, CardChanged)
    assert answer.update.card.match_id == row.match_id


async def test_the_corrected_card_says_the_seat_is_gone() -> None:
    row = offered(a_match(paid=4))
    answer = await a_use_case(
        claims=StubClaims(refusal=MatchIsFull()), offers=(row,)
    ).execute(a_command(row.match_id))

    assert isinstance(answer.update, CardChanged)
    assert answer.update.card.situation.situation is not Situation.SEAT_OPENED
    assert answer.update.card.situation.situation is not Situation.SEAT_OFFERED
    assert answer.update.card.act is not ActCode.TAKE_SEAT


async def test_a_refusal_moved_no_region_and_sends_none() -> None:
    # What leaves the corrected card exactly where it is, so the client can draw
    # its own fading line over a seat that has gone rather than watching the card
    # vanish under her thumb.
    row = offered(a_match(paid=4))
    answer = await a_use_case(
        claims=StubClaims(refusal=MatchIsFull()), offers=(row,)
    ).execute(a_command(row.match_id))

    assert answer.offers is None
    assert answer.your_matches is None


async def test_a_refusal_commits_nothing() -> None:
    uow = RecordingUnitOfWork()
    row = offered(a_match(paid=4))
    await a_use_case(
        claims=StubClaims(refusal=MatchIsFull()), offers=(row,), uow=uow
    ).execute(a_command(row.match_id))

    assert uow.commits == 0


async def test_being_already_in_the_match_is_answered_with_her_own_card() -> None:
    # The answer a second phone gets. She is something to the match, so the strip's
    # card is what comes back — which is the correction: *you are in this*.
    row = enrolled(holds_seat=True)
    answer = await a_use_case(
        claims=StubClaims(refusal=MatchIsFull()), rows=(row,)
    ).execute(a_command(row.match_id))

    assert answer.claimed is False
    assert isinstance(answer.update, CardChanged)
    assert answer.update.card.match_id == row.match_id


# -- the two refusals that are about her -------------------------------------


@pytest.mark.parametrize(
    "refusal",
    [PlayerAlreadyClaiming, ClaimCoolingDown],
    ids=["already-claiming", "cooling-down"],
)
async def test_a_refusal_about_her_rather_than_the_seat_is_not_swallowed(
    refusal: type[Exception],
) -> None:
    # Neither can be said by recomposing a card about *this* match — the first is
    # a sentence about a different one and the second is about a moment — so a
    # card that went on saying *first to take it* would be a button she taps for
    # ever. They are ADR-0081's own two structural limits on a serial claimant.
    row = offered()
    with pytest.raises(refusal):
        await a_use_case(claims=StubClaims(refusal=refusal()), offers=(row,)).execute(
            a_command(row.match_id)
        )


async def test_an_unknown_match_is_the_only_address_refusal() -> None:
    with pytest.raises(MatchNotFound):
        await a_use_case(claims=StubClaims(refusal=MatchNotFound())).execute(
            a_command(uuid4())
        )


# -- which card comes back ----------------------------------------------------


async def test_the_strip_is_asked_before_the_offer() -> None:
    # Two composers and one order. A viewer who is something to the match gets the
    # strip's card, because that is the region the match is in now; the offer card
    # is for somebody who is nothing to it but was told about it.
    row = offered()
    seat = enrolled(row.record, match_id=row.match_id, holds_seat=True)
    port = StubEnrolled(seat)
    answer = await a_use_case(offers=(row,), enrolled_port=port).execute(
        a_command(row.match_id)
    )

    assert port.asked_one != []
    assert isinstance(answer.update, CardChanged)
    assert answer.update.card.may_depart is True


async def test_a_viewer_who_is_nothing_to_the_match_is_told_the_card_is_gone() -> None:
    # ADR-0070's second form, and it is the honest answer rather than a fallback:
    # there is no card about this match anywhere on her screen, so *this card is
    # no longer on your screen* is literally what is true.
    match_id = uuid4()
    answer = await a_use_case(claims=StubClaims(refusal=MatchIsFull())).execute(
        a_command(match_id)
    )

    assert isinstance(answer.update, CardGone)
    assert answer.update.match_id == match_id

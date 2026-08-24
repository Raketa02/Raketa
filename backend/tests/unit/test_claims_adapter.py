"""``Claims`` over the Matches aggregate: two rules, one order, and no commit.

What the aggregate refuses is `tests/unit/test_seat_claims.py`'s and what the
route answers is `tests/api/test_now_offers.py`'s. What is here is the seam
between them, and every claim it makes is invisible from either end:

- the **cross-match** question is asked first, so the sentence she gets is the
  one that tells her what to do rather than one about this match;
- the **hold ladder** is asked before the save, like every other Matches write —
  a claim holds no seat, so the answer is *stand* on every path, and *almost
  always* is not a reason for a write path to be the one that does not ask;
- it **does not commit**, so the claim, the ladder's answer and the outbox row
  belong to the use case's transaction.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.kernel import (
    Cover,
    Instant,
    SeatShare,
    Sport,
    grosze,
    hours,
    instant,
    minutes,
    shifted,
)
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.policy import ClubPolicy
from app.modules.clubs.domain.value_objects import (
    CategoryName,
    ClubName,
    ClubPricing,
    CourtLabel,
    GeoPoint,
    PayoutDestination,
    StreetAddress,
    zone_named,
)
from app.modules.matches.domain.errors import MatchNotFound, PlayerAlreadyClaiming
from app.modules.matches.domain.match import Match
from app.modules.now.infrastructure.claims_through_matches import ClaimsThroughMatches

AT: Instant = instant(datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc))
START: Instant = instant(datetime(2026, 8, 28, 18, 30, tzinfo=timezone.utc))
SHARE = SeatShare(grosze(3800))


def a_club() -> Club:
    club = Club.found(
        club_id=uuid4(),
        name=ClubName("Zabłocie Sport"),
        address=StreetAddress(
            line="ul. Zabłocie 25", city="Kraków", postal_code="30-701"
        ),
        point=GeoPoint(latitude=Decimal("50.048100"), longitude=Decimal("19.958500")),
        timezone=zone_named("Europe/Warsaw"),
        pricing=ClubPricing(),
        policy=ClubPolicy(),
        payout=PayoutDestination(
            account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
        ),
        at=AT,
    )
    category = club.add_category(
        category_id=uuid4(),
        name=CategoryName("Padel · indoor"),
        sport=Sport.PADEL,
        cover=Cover.INDOOR,
        rate=grosze(15200),
    )
    club.add_court(
        court_id=uuid4(),
        category_id=category.id,
        label=CourtLabel("Court 1"),
        at=AT,
    )
    return club


def a_match(club: Club, *, paid: int = 1) -> Match:
    match = Match.post(
        match_id=uuid4(),
        club_id=club.id,
        category_id=club.live_categories[0].id,
        sport=Sport.PADEL,
        start=START,
        duration=hours(1),
        share=SHARE,
        policy=ClubPolicy().hold_policy(),
        at=AT,
    )
    for _ in range(paid):
        player = uuid4()
        match.take_seat(player, at=AT)
        match.pay_seat(player, at=AT)
    match.pull_events()
    return match


class Matches:
    def __init__(self, *matches: Match) -> None:
        self._matches = {match.id: match for match in matches}
        self.saved: list[UUID] = []

    async def get(self, match_id: UUID) -> Match | None:
        return self._matches.get(match_id)

    async def save(self, match: Match) -> Match:
        self.saved.append(match.id)
        return match


class SeatClaims:
    """The cross-match read: the match she is already buying a seat in."""

    def __init__(self, match_id: UUID | None = None) -> None:
        self._match_id = match_id
        self.asks: list[tuple[UUID, Instant]] = []

    async def live_for(self, player_id: UUID, *, at: Instant) -> UUID | None:
        self.asks.append((player_id, at))
        return self._match_id


class Holds:
    """The ladder, which every Matches write asks before the save."""

    def __init__(self) -> None:
        self.applied: list[tuple[UUID, Instant]] = []

    async def apply(self, match: Match, *, at: Instant) -> None:
        self.applied.append((match.id, at))


def an_adapter(
    *,
    matches: Matches,
    claims: SeatClaims | None = None,
    holds: Holds | None = None,
) -> ClaimsThroughMatches:
    return ClaimsThroughMatches(
        matches=matches,
        claims=claims or SeatClaims(),
        holds=holds or Holds(),  # type: ignore[arg-type]
    )


async def test_taking_a_seat_opens_a_claim_and_answers_when_it_lapses() -> None:
    club, alice = a_club(), uuid4()
    match = a_match(club)
    matches = Matches(match)

    expires = await an_adapter(matches=matches).take(
        match_id=match.id, player_id=alice, at=AT
    )

    assert match.live_claim_of(alice, AT) is not None
    assert expires == match.live_claim_of(alice, AT).expires_at
    assert expires > AT
    assert matches.saved == [match.id]


async def test_the_cross_match_question_is_asked_before_the_match_is_touched() -> None:
    """`ClaimSeat`'s own ordering, and it is about what she reads.

    A player mid-payment elsewhere should be told *that* rather than told this
    match is full: the first refusal she gets should be the one that explains
    what to do. It is one indexed lookup where the aggregate's questions are
    free, which is the wrong order on cost and the right one on the sentence.
    """

    club, alice = a_club(), uuid4()
    # Full, so the aggregate would refuse it too — and with a different sentence.
    match = a_match(club, paid=4)
    matches = Matches(match)
    claims = SeatClaims(uuid4())

    with pytest.raises(PlayerAlreadyClaiming):
        await an_adapter(matches=matches, claims=claims).take(
            match_id=match.id, player_id=alice, at=AT
        )

    assert claims.asks == [(alice, AT)]
    assert matches.saved == []


async def test_a_claim_in_another_match_refuses_this_one() -> None:
    """The rule no aggregate can see: one live claim per player, anywhere."""

    club, alice = a_club(), uuid4()
    here, elsewhere = a_match(club), a_match(club)
    matches = Matches(here, elsewhere)

    with pytest.raises(PlayerAlreadyClaiming):
        await an_adapter(matches=matches, claims=SeatClaims(elsewhere.id)).take(
            match_id=here.id, player_id=alice, at=AT
        )

    assert here.live_claim_of(alice, AT) is None


async def test_the_hold_ladder_runs_before_the_save() -> None:
    """Every Matches write asks it, and a claim moves no count it reads.

    The answer is *stand* on every path — a claim holds no seat (ADR-0081), so
    the ladder sees the same tier it saw before. *Almost always* is not a reason
    for a write path to be the one that does not ask: run afterwards, or on the
    outbox, there is a window in which the stored record is in the one
    combination the kernel refuses to read.
    """

    club, alice = a_club(), uuid4()
    match = a_match(club)
    holds = Holds()

    await an_adapter(matches=Matches(match), holds=holds).take(
        match_id=match.id, player_id=alice, at=AT
    )

    assert holds.applied == [(match.id, AT)]


async def test_an_unknown_match_is_refused_on_its_address() -> None:
    with pytest.raises(MatchNotFound):
        await an_adapter(matches=Matches()).take(
            match_id=uuid4(), player_id=uuid4(), at=AT
        )


async def test_the_claim_is_opened_at_the_instant_it_was_given() -> None:
    """One reading of the clock, threaded from the use case.

    The five minutes are measured from *this* moment, so an adapter reading a
    clock of its own would put a card's countdown and its claim's expiry a
    round-trip apart.
    """

    club, alice = a_club(), uuid4()
    match = a_match(club)
    later = shifted(AT, minutes(30))

    expires = await an_adapter(matches=Matches(match)).take(
        match_id=match.id, player_id=alice, at=later
    )

    assert expires > later
    assert match.live_claim_of(alice, later).claimed_at == later

"""``OfferedSeats`` over four contexts, and the claims no composed screen shows.

Everything the offers region *renders* is `tests/unit/test_compose_offers.py`'s
subject. What is here is the half a composed screen cannot see:

- an offer whose match is loaded **once**, however many holes it names;
- the clubs read in **one batch**;
- the fifteen-minute rule **not** applied here — the adapter answers *which court
  is reserved* and the composer decides whether it may be printed;
- a player who has been told about no seat pays for no match read, no club read
  and no reservation loop at all;
- *already mine* composed against the **composing instant**, so a claim of hers
  stops counting at the moment it lapses rather than when a reaper writes the
  receipt.

The first two are claims about *cost*, the rest are claims about *rules*, and all
of them are satisfied by an answer that looks identical on screen. So the fakes
below refuse the read that was not supposed to happen and count the ones that
were — the shape `test_enrolled_adapter.py` established.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence
from uuid import UUID, uuid4

from app.kernel import (
    Cover,
    Instant,
    OfferKind,
    SeatShare,
    Sport,
    grosze,
    hours,
    instant,
    live_outcome,
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
from app.modules.matches.domain.match import Match
from app.modules.now.domain.cascade import Offer, Rung
from app.modules.now.infrastructure.offered_seats import OfferedFromTheCascade

AT: Instant = instant(datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc))
START: Instant = instant(datetime(2026, 8, 28, 18, 30, tzinfo=timezone.utc))
SHARE = SeatShare(grosze(3800))


# --- the world ------------------------------------------------------------


def a_club(*, courts: int = 2) -> Club:
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
    for index in range(courts):
        club.add_court(
            court_id=uuid4(),
            category_id=category.id,
            label=CourtLabel(f"Court {index + 1}"),
            at=AT,
        )
    return club


def a_match(
    club: Club, *, players: Sequence[UUID] = (), start: Instant = START
) -> Match:
    match = Match.post(
        match_id=uuid4(),
        club_id=club.id,
        category_id=club.live_categories[0].id,
        sport=Sport.PADEL,
        start=start,
        duration=hours(1),
        share=SHARE,
        policy=ClubPolicy().hold_policy(),
        at=AT,
    )
    for player in players:
        match.take_seat(player, at=AT)
        match.pay_seat(player, at=AT)
    match.pull_events()
    return match


def an_offer(match: Match, player_id: UUID, **kwargs) -> Offer:
    return Offer(
        **{
            "match_id": match.id,
            "vacancy_id": uuid4(),
            "player_id": player_id,
            "player_rung": Rung.STANDBY,
            "fit": 84,
            "price": SHARE,
            "kind": OfferKind.OPEN,
            "offered_at": AT,
            **kwargs,
        }
    )


class Reservation:
    def __init__(self, court_id: UUID, released_at: Instant | None = None) -> None:
        self.court_id = court_id
        self.released_at = released_at


# --- the fakes ------------------------------------------------------------


class Offers:
    """The store, answering one player's offers newest first — like the real one."""

    def __init__(self, *offers: Offer) -> None:
        self._offers = list(offers)
        self.asks: list[UUID] = []

    async def held_by(self, player_id: UUID) -> tuple[Offer, ...]:
        self.asks.append(player_id)
        return tuple(
            sorted(
                (one for one in self._offers if one.player_id == player_id),
                key=lambda one: (one.offered_at, one.vacancy_id),
                reverse=True,
            )
        )

    async def record(self, offers) -> None:  # pragma: no cover
        raise AssertionError("a screen never writes an offer")

    async def offered_for(self, **_: object):  # pragma: no cover
        raise AssertionError("the region asks by player, never by hole")

    async def reached_on(self, **_: object):  # pragma: no cover
        raise AssertionError("the region asks by player, never by match")


class Matches:
    def __init__(self, *matches: Match) -> None:
        self._matches = {match.id: match for match in matches}
        self.gets: list[UUID] = []

    async def get(self, match_id: UUID) -> Match | None:
        self.gets.append(match_id)
        return self._matches.get(match_id)


class Clubs:
    def __init__(self, *clubs: Club) -> None:
        self._clubs = {club.id: club for club in clubs}
        self.batches: list[tuple[UUID, ...]] = []
        self.gets: list[UUID] = []

    async def find_by_ids(self, club_ids: Sequence[UUID]) -> list[Club]:
        self.batches.append(tuple(club_ids))
        return [self._clubs[one] for one in club_ids if one in self._clubs]

    async def get(self, club_id: UUID):
        self.gets.append(club_id)
        return self._clubs.get(club_id)

    async def find_all(self):  # pragma: no cover
        raise AssertionError("the region never walks every club on the platform")


class Reservations:
    def __init__(self, **held: Reservation) -> None:
        self._held = held
        self.asks: list[UUID] = []

    async def for_match(self, match_id: UUID) -> Reservation | None:
        self.asks.append(match_id)
        return self._held.get(str(match_id))


def an_adapter(
    *,
    offers: Offers,
    matches: Matches,
    clubs: Clubs,
    reservations: Reservations | None = None,
) -> OfferedFromTheCascade:
    return OfferedFromTheCascade(
        offers=offers,
        matches=matches,
        clubs=clubs,
        reservations=reservations or Reservations(),
    )


# --- the claims -----------------------------------------------------------


async def test_an_offer_becomes_a_row_carrying_the_match_and_its_club() -> None:
    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    rows = await an_adapter(
        offers=Offers(an_offer(match, alice)),
        matches=Matches(match),
        clubs=Clubs(club),
    ).for_player(player_id=alice, now=AT)

    assert [row.match_id for row in rows] == [match.id]
    assert rows[0].where.club_name == "Zabłocie Sport"
    assert rows[0].where.cover is Cover.INDOOR
    assert int(rows[0].share.amount) == int(SHARE)
    assert int(rows[0].court_total.amount) == int(SHARE) * 4


async def test_the_row_carries_the_matchs_share_and_not_the_quoted_price() -> None:
    """The two differ once the rescue deadline has passed, and the card wants both.

    `Offer.price` is what she was quoted **when she was told**; the composer
    applies `kernel.seat_price` to the match's share at the composing instant, so
    a row carrying the stored figure would freeze the tier she was told about and
    quote her a price the platform has since stopped charging.
    """

    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    half = SeatShare(grosze(int(SHARE) // 2))
    rows = await an_adapter(
        offers=Offers(an_offer(match, alice, price=half)),
        matches=Matches(match),
        clubs=Clubs(club),
    ).for_player(player_id=alice, now=AT)

    assert int(rows[0].share.amount) == int(SHARE)
    assert int(rows[0].share.amount) != int(half)


async def test_a_match_with_two_holes_is_loaded_once_and_is_one_row() -> None:
    """A card is about the match, so two holes are one card, not two.

    Deduplication happens **before** the loop rather than after it, so a match
    that lost two players costs one read rather than two.
    """

    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    matches = Matches(match)
    rows = await an_adapter(
        offers=Offers(
            an_offer(match, alice, offered_at=AT),
            an_offer(match, alice, offered_at=shifted(AT, minutes(-20))),
        ),
        matches=matches,
        clubs=Clubs(club),
    ).for_player(player_id=alice, now=AT)

    assert len(rows) == 1
    assert matches.gets == [match.id]


async def test_the_newest_offer_per_match_is_the_one_kept() -> None:
    """The price she was **last** quoted is the sentence she was last shown."""

    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    newest = an_offer(match, alice, offered_at=AT, kind=OfferKind.EXCLUSIVE)
    oldest = an_offer(match, alice, offered_at=shifted(AT, minutes(-20)))
    rows = await an_adapter(
        offers=Offers(oldest, newest),
        matches=Matches(match),
        clubs=Clubs(club),
    ).for_player(player_id=alice, now=AT)

    assert rows[0].kind is OfferKind.EXCLUSIVE
    assert rows[0].vacancy_id == newest.vacancy_id


async def test_the_clubs_are_read_in_one_batch() -> None:
    club, alice = a_club(), uuid4()
    one = a_match(club, players=[uuid4()])
    two = a_match(club, players=[uuid4()], start=shifted(START, hours(2)))
    clubs = Clubs(club)
    await an_adapter(
        offers=Offers(an_offer(one, alice), an_offer(two, alice)),
        matches=Matches(one, two),
        clubs=clubs,
    ).for_player(player_id=alice, now=AT)

    assert clubs.batches == [(club.id,)]
    assert clubs.gets == []


async def test_a_player_told_about_no_seat_pays_for_nothing_downstream() -> None:
    club = a_club()
    matches, clubs, reservations = (
        Matches(a_match(club, players=[uuid4()])),
        Clubs(club),
        Reservations(),
    )
    rows = await an_adapter(
        offers=Offers(), matches=matches, clubs=clubs, reservations=reservations
    ).for_player(player_id=uuid4(), now=AT)

    assert rows == ()
    assert (matches.gets, clubs.batches, reservations.asks) == ([], [], [])


async def test_the_adapter_names_the_court_whatever_the_clock_says() -> None:
    """The fifteen-minute rule is the composer's, and this is the read under it.

    A court is assigned and may be reassigned until fifteen minutes before play;
    an adapter that applied that rule would make what it reads out of the
    database depend on when it was asked.
    """

    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    rows = await an_adapter(
        offers=Offers(an_offer(match, alice)),
        matches=Matches(match),
        clubs=Clubs(club),
        reservations=Reservations(
            **{str(match.id): Reservation(club.live_courts[0].id)}
        ),
    ).for_player(player_id=alice, now=AT)

    assert rows[0].court == "Court 1"


async def test_a_released_reservation_names_no_court() -> None:
    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    rows = await an_adapter(
        offers=Offers(an_offer(match, alice)),
        matches=Matches(match),
        clubs=Clubs(club),
        reservations=Reservations(
            **{
                str(match.id): Reservation(
                    club.live_courts[0].id, released_at=AT
                )
            }
        ),
    ).for_player(player_id=alice, now=AT)

    assert rows[0].court is None


async def test_a_match_at_a_club_this_read_cannot_see_is_dropped_not_broken() -> None:
    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    rows = await an_adapter(
        offers=Offers(an_offer(match, alice)),
        matches=Matches(match),
        clubs=Clubs(),
    ).for_player(player_id=alice, now=AT)

    assert rows == ()


# --- already mine ---------------------------------------------------------


async def test_a_seat_of_her_own_makes_the_match_already_hers() -> None:
    club, alice = a_club(), uuid4()
    match = a_match(club, players=[alice])
    rows = await an_adapter(
        offers=Offers(an_offer(match, alice)),
        matches=Matches(match),
        clubs=Clubs(club),
    ).for_player(player_id=alice, now=AT)

    assert rows[0].already_mine is True


async def test_a_live_claim_makes_the_match_already_hers() -> None:
    """The read that keeps one match to one card the moment she takes the seat."""

    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    match.open_claim(alice, at=AT)
    rows = await an_adapter(
        offers=Offers(an_offer(match, alice)),
        matches=Matches(match),
        clubs=Clubs(club),
    ).for_player(player_id=alice, now=AT)

    assert rows[0].already_mine is True


async def test_a_claim_that_has_lapsed_stops_counting_at_its_own_instant() -> None:
    """ADR-0081's *"live is composed, never latched"*, read from the reading end.

    A player who let a claim lapse is nothing to the match again, and if the seat
    is still free her offer is live again — the correct answer rather than a
    lenient one, since the seat genuinely went back on the market.
    """

    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    claim = match.open_claim(alice, at=AT)
    adapter = an_adapter(
        offers=Offers(an_offer(match, alice)),
        matches=Matches(match),
        clubs=Clubs(club),
    )

    live = await adapter.for_player(
        player_id=alice, now=shifted(claim.expires_at, minutes(-1))
    )
    lapsed = await adapter.for_player(player_id=alice, now=claim.expires_at)

    assert live[0].already_mine is True
    assert lapsed[0].already_mine is False


async def test_a_departure_of_her_own_makes_the_match_already_hers() -> None:
    club, alice = a_club(), uuid4()
    match = a_match(club, players=[alice, uuid4()])
    match.depart(alice, quote=live_outcome(match.as_record(), AT), at=AT)
    rows = await an_adapter(
        offers=Offers(an_offer(match, alice)),
        matches=Matches(match),
        clubs=Clubs(club),
    ).for_player(player_id=alice, now=AT)

    assert rows[0].already_mine is True


async def test_a_stranger_to_the_match_is_not_already_in_it() -> None:
    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    rows = await an_adapter(
        offers=Offers(an_offer(match, alice)),
        matches=Matches(match),
        clubs=Clubs(club),
    ).for_player(player_id=alice, now=AT)

    assert rows[0].already_mine is False


# --- the one-match read ---------------------------------------------------


async def test_one_match_answers_the_offer_she_holds_on_it() -> None:
    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    row = await an_adapter(
        offers=Offers(an_offer(match, alice)),
        matches=Matches(match),
        clubs=Clubs(club),
    ).one(player_id=alice, match_id=match.id, now=AT)

    assert row is not None
    assert row.match_id == match.id


async def test_one_match_answers_nothing_for_a_match_she_was_never_told_about() -> None:
    club, alice = a_club(), uuid4()
    mine = a_match(club, players=[uuid4()])
    other = a_match(club, players=[uuid4()], start=shifted(START, hours(2)))
    matches = Matches(mine, other)
    row = await an_adapter(
        offers=Offers(an_offer(mine, alice)),
        matches=matches,
        clubs=Clubs(club),
    ).one(player_id=alice, match_id=other.id, now=AT)

    assert row is None
    # And it never loaded the match to find out: the offer read answered first.
    assert matches.gets == []


async def test_one_match_answers_nothing_for_a_match_that_is_gone() -> None:
    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    row = await an_adapter(
        offers=Offers(an_offer(match, alice)), matches=Matches(), clubs=Clubs(club)
    ).one(player_id=alice, match_id=match.id, now=AT)

    assert row is None


async def test_the_offers_are_asked_for_by_player() -> None:
    club, alice = a_club(), uuid4()
    match = a_match(club, players=[uuid4()])
    offers = Offers(an_offer(match, alice))
    await an_adapter(
        offers=offers, matches=Matches(match), clubs=Clubs(club)
    ).for_player(player_id=alice, now=AT)

    assert offers.asks == [alice]

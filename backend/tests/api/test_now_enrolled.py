"""The enrolled strip over HTTP: a real match, a real club, a real card.

The unit suite asserts the rules against stubs and the adapter suite asserts the
reads against fakes. What this file adds is the half neither can reach — that a
seat really is a row a player holds, that the roof really is the category's, that
the price really is the share the match was posted with, and that a leaver really
does keep a card after her seat is gone.

Matches and clubs are written through the real repositories rather than through a
route, because neither has a player-facing endpoint to write one with: `POST
/matches` does not exist and `app/api/v1/club.py` carries nothing. The `client`
fixture overrides `get_db` with the same factory, so what is written here is what
the request sees.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.infrastructure.clock import SystemClock
from app.kernel import (
    Cover,
    Instant,
    SeatShare,
    Sport,
    grosze,
    hours,
    instant,
    live_outcome,
    zloty,
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
    zone_named as _zone,
)
from app.modules.clubs.infrastructure.sqlalchemy_club_repository import (
    SqlAlchemyClubRepository,
)
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.score import Score, SetScore
from app.modules.matches.infrastructure.sqlalchemy_match_repository import (
    SqlAlchemyMatchRepository,
)

ALICE = {
    "email": "alice@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "alice",
}
BOB = {
    "email": "bob@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "bob",
}

ADDRESS = StreetAddress(line="ul. Zabłocie 25", city="Kraków", postal_code="30-701")
POINT = GeoPoint(latitude=Decimal("50.048100"), longitude=Decimal("19.958500"))
PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
)
SHARE = SeatShare(grosze(3800))


class _Silent:
    """The publisher, for a write that is being staged rather than announced.

    Nothing in this file reacts to a match event, and an outbox row per seat
    would make these cases about the event runtime rather than about a card.
    """

    async def publish(self, event) -> None:
        return None

    async def publish_many(self, events) -> None:
        return None


async def _register(client, payload) -> str:
    created = await client.post("/api/v1/users", json=payload)
    assert created.status_code in (200, 201), created.text
    return created.json()["id"]


async def _sign_in(client, payload) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password1"]},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _join(client, payload) -> tuple[str, dict[str, str]]:
    who = await _register(client, payload)
    return who, await _sign_in(client, payload)


async def _write_club(session_factory, *, cover: Cover = Cover.INDOOR) -> Club:
    club = Club.found(
        club_id=uuid4(),
        name=ClubName(f"Zabłocie {uuid4().hex[:6]}"),
        address=ADDRESS,
        point=POINT,
        timezone=_zone("Europe/Warsaw"),
        pricing=ClubPricing(),
        policy=ClubPolicy(),
        payout=PAYOUT,
        at=SystemClock().now(),
    )
    category = club.add_category(
        category_id=uuid4(),
        name=CategoryName("Padel · hall"),
        sport=Sport.PADEL,
        cover=cover,
        rate=zloty(152),
    )
    club.add_court(
        court_id=uuid4(),
        category_id=category.id,
        label=CourtLabel("Court 1"),
        at=SystemClock().now(),
    )
    async with session_factory() as session:
        await SqlAlchemyClubRepository(session).add(club)
        await session.commit()
    return club


def _soon(days: int = 4) -> Instant:
    """A start far enough out that nothing has committed and nothing has lapsed."""

    return instant(
        datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=days)
    )


async def _write_match(
    session_factory,
    club: Club,
    *,
    start: Instant | None = None,
    seated: tuple[UUID, ...] = (),
    paid: tuple[UUID, ...] = (),
    left: UUID | None = None,
    score: Score | None = None,
    cancelled_at: Instant | None = None,
) -> Match:
    at = instant(datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=7))
    match = Match.post(
        match_id=uuid4(),
        club_id=club.id,
        category_id=club.live_categories[0].id,
        sport=Sport.PADEL,
        start=start or _soon(),
        duration=hours(1),
        share=SHARE,
        policy=club.policy_now.hold_policy(),
        at=at,
    )
    for player in seated:
        match.take_seat(player, at=at)
    for player in paid:
        match.pay_seat(player, at=at)
    if left is not None:
        match.depart(left, quote=live_outcome(match.as_record(), at), at=at)
    if score is not None:
        match.score = score
        match.result_agreed = True
    if cancelled_at is not None:
        match.cancel_by_club(at=cancelled_at)
    async with session_factory() as session:
        repository = SqlAlchemyMatchRepository(
            session, events=_Silent(), clock=SystemClock()
        )
        await repository.add(match)
        await session.commit()
    return match


def _strip(body) -> list[dict]:
    return body["your_matches"]["cards"]


# --- a card for a match she is on -------------------------------------------


async def test_a_seat_she_holds_puts_the_match_on_her_strip(
    client, session_factory
) -> None:
    alice_id, alice = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, seated=(UUID(alice_id),), paid=(UUID(alice_id),)
    )

    body = (await client.get("/api/v1/now", headers=alice)).json()
    cards = _strip(body)

    assert [card["match_id"] for card in cards] == [str(match.id)]
    card = cards[0]
    assert card["card_type"] == "match"
    assert card["where"]["club_name"] == club.name.value
    assert card["where"]["zone"] == "Europe/Warsaw"
    assert card["where"]["cover"] == "indoor"
    assert card["price"] == {"amount": 3800, "currency": "PLN"}


async def test_the_card_counts_the_seats_that_are_paid_for(
    client, session_factory
) -> None:
    alice_id, alice = await _join(client, ALICE)
    bob_id, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory,
        club,
        seated=(UUID(alice_id), UUID(bob_id)),
        paid=(UUID(alice_id),),
    )

    card = _strip((await client.get("/api/v1/now", headers=alice)).json())[0]

    assert card["situation"]["facts"]["counts"] == {
        "seats": 4,
        "paid": 1,
        "held": 1,
        "turned_up": None,
    }
    # A seat somebody holds and nobody has paid for is the whole of `formingHeld`.
    assert card["situation"]["situation"] == "formingHeld"


async def test_the_courts_total_rides_beside_her_own_share(
    client, session_factory
) -> None:
    alice_id, alice = await _join(client, ALICE)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, seated=(UUID(alice_id),), paid=(UUID(alice_id),)
    )

    card = _strip((await client.get("/api/v1/now", headers=alice)).json())[0]

    assert card["situation"]["facts"]["court_total"]["amount"] == 3800 * 4


async def test_a_card_counts_down_to_the_next_thing_that_happens(
    client, session_factory
) -> None:
    alice_id, alice = await _join(client, ALICE)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, seated=(UUID(alice_id),), paid=(UUID(alice_id),)
    )

    card = _strip((await client.get("/api/v1/now", headers=alice)).json())[0]

    assert card["clock"] is not None
    assert card["seat_claim"] is None


async def test_a_card_names_no_court_days_before_the_match(
    client, session_factory
) -> None:
    alice_id, alice = await _join(client, ALICE)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, seated=(UUID(alice_id),), paid=(UUID(alice_id),)
    )

    card = _strip((await client.get("/api/v1/now", headers=alice)).json())[0]

    assert card["situation"]["facts"]["court"] is None


# --- the sport bar -----------------------------------------------------------


async def test_a_chip_for_another_sport_hides_her_padel_match(
    client, session_factory
) -> None:
    alice_id, alice = await _join(client, ALICE)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, seated=(UUID(alice_id),), paid=(UUID(alice_id),)
    )

    padel = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    squash = (await client.get("/api/v1/now?sport=SQUASH", headers=alice)).json()

    assert len(_strip(padel)) == 1
    assert _strip(squash) == []


async def test_all_shows_the_match_even_though_she_holds_no_rating(
    client, session_factory
) -> None:
    """The filter must not hide a match she has paid for and is playing.

    `all` resolves to *the sports she holds a rating at* for the shelves; alice
    holds none here, and her own match is on the screen regardless.
    """

    alice_id, alice = await _join(client, ALICE)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, seated=(UUID(alice_id),), paid=(UUID(alice_id),)
    )

    body = (await client.get("/api/v1/now", headers=alice)).json()

    # She holds no rating anywhere, so `all` resolves to nothing and every
    # ranked shelf is absent — and her own match is on the screen regardless.
    assert body["shelves"]["shelves"] == []
    assert len(_strip(body)) == 1


# --- the other two audiences -------------------------------------------------


async def test_somebody_elses_match_is_not_on_her_strip(
    client, session_factory
) -> None:
    _, alice = await _join(client, ALICE)
    bob_id, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, seated=(UUID(bob_id),), paid=(UUID(bob_id),)
    )

    assert _strip((await client.get("/api/v1/now", headers=alice)).json()) == []


async def test_a_leaver_keeps_a_card_and_it_names_no_amount(
    client, session_factory
) -> None:
    """She took a seat and never paid, so there is nothing to name (ADR-0030)."""

    alice_id, alice = await _join(client, ALICE)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, seated=(UUID(alice_id),), left=UUID(alice_id)
    )

    cards = _strip((await client.get("/api/v1/now", headers=alice)).json())

    assert len(cards) == 1
    departure = cards[0]["situation"]["facts"]["departure"]
    assert departure == {"form": "nothingTaken"}


async def test_a_settled_result_prints_both_sides_with_hers_first(
    client, session_factory
) -> None:
    alice_id, alice = await _join(client, ALICE)
    bob_id, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    others = (uuid4(), uuid4())
    # Alice takes the third seat, so she is on side B and her side goes first.
    seated = (UUID(bob_id), others[0], UUID(alice_id), others[1])
    await _write_match(
        session_factory,
        club,
        start=instant(datetime.now(timezone.utc) - timedelta(hours=3)),
        seated=seated,
        paid=seated,
        score=Score(sets=(SetScore(side_a=6, side_b=4),)),
    )

    card = _strip((await client.get("/api/v1/now", headers=alice)).json())[0]
    score = card["situation"]["facts"]["score"]

    assert card["situation"]["situation"] == "completed"
    assert score["sets"] == [{"first": 4, "second": 6}]
    assert score["sides"][0]["players"] == ["alice"]
    assert score["sides"][1]["players"] == ["bob"]


# --- the twenty-four hours ---------------------------------------------------


async def test_a_match_cancelled_over_a_day_ago_is_gone_from_the_strip(
    client, session_factory
) -> None:
    alice_id, alice = await _join(client, ALICE)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory,
        club,
        seated=(UUID(alice_id),),
        paid=(UUID(alice_id),),
        cancelled_at=instant(datetime.now(timezone.utc) - timedelta(days=2)),
    )

    assert _strip((await client.get("/api/v1/now", headers=alice)).json()) == []


async def test_a_match_cancelled_an_hour_ago_still_says_so(
    client, session_factory
) -> None:
    alice_id, alice = await _join(client, ALICE)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory,
        club,
        seated=(UUID(alice_id),),
        paid=(UUID(alice_id),),
        cancelled_at=instant(datetime.now(timezone.utc) - timedelta(hours=1)),
    )

    card = _strip((await client.get("/api/v1/now", headers=alice)).json())[0]

    assert card["situation"]["situation"] == "cancelledClub"
    assert card["situation"]["facts"]["cause"] == "clubCancelled"
    # Nothing moved through her ledger, so there is nothing to give back.
    assert card["situation"]["facts"]["refund"] is None
    # Over counts to nothing rather than to zero.
    assert card["clock"] is None


# --- what the strip still does not carry -------------------------------------


async def test_no_card_names_an_act_no_surface_can_receive(
    client, session_factory
) -> None:
    """Of the six receiving surfaces exactly one exists, and it is not an act.

    The departure route landed (`Raketa02/Raketa#80`) and its control is a
    **spine boolean**, not a seventh act code — leaving is not the card's act.
    The seat claim and its payment, the result route and leaving standby are
    still unbuilt, so `act` stays absent: a card naming an act that opens
    nothing is a door offered that will not open.
    """

    alice_id, alice = await _join(client, ALICE)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, seated=(UUID(alice_id),), paid=(UUID(alice_id),)
    )

    card = _strip((await client.get("/api/v1/now", headers=alice)).json())[0]

    assert card["act"] is None
    assert card["fit"] is None
    assert card["emphasis"] is False
    # The one control that now has somewhere to go.
    assert card["may_depart"] is True


async def test_a_leavers_card_offers_no_exit_and_a_started_matchs_offers_none(
    client, session_factory
) -> None:
    """`may_depart` is the kernel's, so the strip and the route agree by
    construction — and both are false wherever `Match.depart` would refuse."""

    alice_id, alice = await _join(client, ALICE)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory,
        club,
        seated=(UUID(alice_id),),
        paid=(UUID(alice_id),),
        left=UUID(alice_id),
    )

    card = _strip((await client.get("/api/v1/now", headers=alice)).json())[0]

    assert card["may_depart"] is False
    assert card["situation"]["facts"]["departure"] is not None

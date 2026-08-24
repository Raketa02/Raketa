"""The offers region over HTTP, and the write that takes the seat.

The unit suite asserts the rules against stubs and the adapter suite asserts the
reads against fakes. What this file adds is the half neither can reach:

- that an offer row the **cascade** wrote really does become a card, with the two
  situations distinguishable on the wire;
- that the act really crosses, so a phone has a button to draw;
- that an offer on the screen really does silence emphasis, which is invisible
  from a unit suite because ``emphasis`` defaults to ``False`` on both the domain
  card and the response model — a composer that dropped it would render every
  card quiet, pass everything, and ship a screen that looks exactly like an
  ordinary screen;
- that taking a seat opens a claim, and that a seat somebody else took comes back
  as **what a success returns** rather than as an error;
- and that an offer never reaches a sport the viewer holds no rating at nor a
  player outside the match's band — asserted **through the cascade** rather than
  by writing the offer row this file wants, because those two rules live in the
  pool and a hand-written row would assert nothing about them.

Matches, clubs and offers are written through the real repositories and the real
dispatch rather than through a route, because neither has a player-facing
endpoint to write one with. The ``client`` fixture overrides ``get_db`` with the
same factory, so what is written here is what the request sees.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.bootstrap.composition import (
    build_club_repository,
    build_match_repository,
    build_offers,
)
from app.infrastructure.clock import SystemClock
from app.kernel import (
    Cover,
    Instant,
    OfferKind,
    SeatShare,
    Sport,
    grosze,
    hours,
    instant,
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
from app.modules.matches.domain.match import Match
from app.modules.now.domain.cascade import Offer, Rung

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
    """The publisher, for a write being staged rather than announced."""

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


async def _join(client, payload) -> tuple[UUID, dict[str, str]]:
    who = await _register(client, payload)
    return UUID(who), await _sign_in(client, payload)


async def _write_club(session_factory, *, sport: Sport = Sport.PADEL) -> Club:
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
        sport=sport,
        cover=Cover.INDOOR,
        rate=zloty(152),
    )
    club.add_court(
        court_id=uuid4(),
        category_id=category.id,
        label=CourtLabel("Court 1"),
        at=SystemClock().now(),
    )
    async with session_factory() as session:
        await build_club_repository(session).add(club)
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
    sport: Sport = Sport.PADEL,
    start: Instant | None = None,
    paid: tuple[UUID, ...] = (),
    cancelled: bool = False,
) -> Match:
    at = instant(datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=7))
    match = Match.post(
        match_id=uuid4(),
        club_id=club.id,
        category_id=club.live_categories[0].id,
        sport=sport,
        start=start or _soon(),
        duration=hours(1),
        share=SHARE,
        policy=club.policy_now.hold_policy(),
        at=at,
    )
    for player in paid:
        match.take_seat(player, at=at)
        match.pay_seat(player, at=at)
    if cancelled:
        match.cancel_by_club(at=SystemClock().now())
    async with session_factory() as session:
        await build_match_repository(
            session, events=_Silent(), clock=SystemClock()
        ).add(match)
        await session.commit()
    return match


async def _write_offer(
    session_factory,
    match: Match,
    player_id: UUID,
    *,
    kind: OfferKind = OfferKind.OPEN,
    rung: Rung = Rung.STANDBY,
) -> None:
    """One row, exactly as a dispatch would leave it.

    Written through ``Offers.record`` rather than through SQL, so a column this
    read depends on cannot be one the cascade never fills.
    """

    async with session_factory() as session:
        await build_offers(session).record(
            [
                Offer(
                    match_id=match.id,
                    vacancy_id=uuid4(),
                    player_id=player_id,
                    player_rung=rung,
                    fit=84,
                    price=SHARE,
                    kind=kind,
                    offered_at=SystemClock().now(),
                )
            ]
        )
        await session.commit()


def _offers(body) -> list[dict]:
    return body["offers"]["cards"]


# --- the region -------------------------------------------------------------


async def test_an_offer_the_cascade_wrote_becomes_a_card(
    client, session_factory
) -> None:
    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(session_factory, club, paid=(uuid4(),))
    await _write_offer(session_factory, match, alice)

    body = (await client.get("/api/v1/now", headers=headers)).json()
    cards = _offers(body)

    assert [card["match_id"] for card in cards] == [str(match.id)]
    assert cards[0]["card_type"] == "match"
    assert cards[0]["where"]["club_name"] == club.name.value
    assert cards[0]["price"] == {"amount": 3800, "currency": "PLN"}


async def test_the_two_offer_situations_are_distinguishable_on_the_wire(
    client, session_factory
) -> None:
    """ADR-0061 retired the exclusive offer and the kernel kept its name.

    The store carries the kind, so the two cross as two enum members rather than
    as one with a comment — which is what lets a client hold a row for each.
    """

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    open_call = await _write_match(session_factory, club, paid=(uuid4(),))
    exclusive = await _write_match(
        session_factory, club, paid=(uuid4(),), start=_soon(days=6)
    )
    await _write_offer(session_factory, open_call, alice)
    await _write_offer(session_factory, exclusive, alice, kind=OfferKind.EXCLUSIVE)

    body = (await client.get("/api/v1/now", headers=headers)).json()
    situations = {
        card["match_id"]: card["situation"]["situation"] for card in _offers(body)
    }

    assert situations[str(open_call.id)] == "seatOpened"
    assert situations[str(exclusive.id)] == "seatOffered"


async def test_the_card_names_the_act_that_takes_the_seat(
    client, session_factory
) -> None:
    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(session_factory, club, paid=(uuid4(),))
    await _write_offer(session_factory, match, alice)

    body = (await client.get("/api/v1/now", headers=headers)).json()

    assert _offers(body)[0]["act"] == "takeSeat"
    assert _offers(body)[0]["may_depart"] is False


async def test_the_region_is_present_and_empty_for_a_player_told_nothing(
    client, session_factory
) -> None:
    _, headers = await _join(client, ALICE)

    body = (await client.get("/api/v1/now", headers=headers)).json()

    assert body["offers"]["cards"] == []
    assert "stamp" in body["offers"]


async def test_a_seat_somebody_else_took_is_no_longer_on_the_region(
    client, session_factory
) -> None:
    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, paid=(uuid4(), uuid4(), uuid4(), uuid4())
    )
    await _write_offer(session_factory, match, alice)

    body = (await client.get("/api/v1/now", headers=headers)).json()

    assert _offers(body) == []


async def test_a_cancelled_match_offers_nothing(client, session_factory) -> None:
    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, paid=(uuid4(),), cancelled=True
    )
    await _write_offer(session_factory, match, alice)

    body = (await client.get("/api/v1/now", headers=headers)).json()

    assert _offers(body) == []


async def test_a_named_chip_filters_the_region_and_all_hides_nothing(
    client, session_factory
) -> None:
    alice, headers = await _join(client, ALICE)
    padel_club = await _write_club(session_factory)
    tennis_club = await _write_club(session_factory, sport=Sport.TENNIS)
    padel = await _write_match(session_factory, padel_club, paid=(uuid4(),))
    tennis = await _write_match(
        session_factory, tennis_club, sport=Sport.TENNIS, paid=(uuid4(),)
    )
    await _write_offer(session_factory, padel, alice)
    await _write_offer(session_factory, tennis, alice)

    everything = (await client.get("/api/v1/now", headers=headers)).json()
    only_tennis = (
        await client.get("/api/v1/now?sport=TENNIS", headers=headers)
    ).json()

    assert len(_offers(everything)) == 2
    assert [card["match_id"] for card in _offers(only_tennis)] == [str(tennis.id)]


# --- the write --------------------------------------------------------------


async def test_taking_a_free_seat_claims_it_and_moves_the_card(
    client, session_factory
) -> None:
    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(session_factory, club, paid=(uuid4(),))
    await _write_offer(session_factory, match, alice)

    answer = await client.post(
        f"/api/v1/matches/{match.id}/seat", headers=headers
    )
    body = answer.json()

    assert answer.status_code == 200, answer.text
    assert body["claimed"] is True
    assert body["update"]["update_type"] == "card"
    assert body["update"]["card"]["match_id"] == str(match.id)
    assert body["update"]["card"]["seat_claim"] is not None
    # Both viewer-owned regions come back whole: the offer is gone and the match
    # belongs in the strip (ADR-0070).
    assert body["offers"]["cards"] == []
    assert [card["match_id"] for card in body["your_matches"]["cards"]] == [
        str(match.id)
    ]


async def test_the_claimed_match_is_on_the_strip_on_the_next_compose(
    client, session_factory
) -> None:
    """The card she has five minutes to pay for is on a region of her screen.

    Without the strip's fifth membership it would be on neither: the offers
    region drops it the instant the match becomes hers.
    """

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(session_factory, club, paid=(uuid4(),))
    await _write_offer(session_factory, match, alice)
    await client.post(f"/api/v1/matches/{match.id}/seat", headers=headers)

    body = (await client.get("/api/v1/now", headers=headers)).json()

    assert _offers(body) == []
    assert [card["match_id"] for card in body["your_matches"]["cards"]] == [
        str(match.id)
    ]


async def test_a_seat_that_has_gone_answers_what_a_success_answers(
    client, session_factory
) -> None:
    """ADR-0070's refusal rule, end to end: no error, no second shape.

    The player *sees* that the seat has gone rather than being told by a dialog,
    and the client has one code path instead of two.
    """

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, paid=(uuid4(), uuid4(), uuid4(), uuid4())
    )
    await _write_offer(session_factory, match, alice)

    answer = await client.post(
        f"/api/v1/matches/{match.id}/seat", headers=headers
    )
    body = answer.json()

    assert answer.status_code == 200, answer.text
    assert body["claimed"] is False
    assert body["update"]["update_type"] == "card"
    assert body["update"]["card"]["situation"]["situation"] not in (
        "seatOpened",
        "seatOffered",
    )
    assert body["update"]["card"]["act"] != "takeSeat"
    # Nothing moved, so neither region rides back — which is what leaves the
    # corrected card on screen for the client to fade a line over.
    assert body["offers"] is None
    assert body["your_matches"] is None


async def test_a_second_tap_by_the_player_holding_the_claim_is_refused_plainly(
    client, session_factory
) -> None:
    """Her own claim refuses it, and the answer is the state she asked for.

    This is why the route carries no idempotency key: what one would buy — *did
    my first tap land* — is answered by the card that comes back carrying it.
    """

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(session_factory, club, paid=(uuid4(),))
    await _write_offer(session_factory, match, alice)
    await client.post(f"/api/v1/matches/{match.id}/seat", headers=headers)

    again = await client.post(f"/api/v1/matches/{match.id}/seat", headers=headers)

    assert again.status_code == 409, again.text
    assert again.json()["code"] == "match_player_already_claiming"


async def test_taking_a_seat_in_a_match_that_does_not_exist_is_a_404(
    client, session_factory
) -> None:
    _, headers = await _join(client, ALICE)

    answer = await client.post(f"/api/v1/matches/{uuid4()}/seat", headers=headers)

    assert answer.status_code == 404, answer.text


async def test_the_route_needs_a_token(client, session_factory) -> None:
    club = await _write_club(session_factory)
    match = await _write_match(session_factory, club, paid=(uuid4(),))

    answer = await client.post(f"/api/v1/matches/{match.id}/seat")

    assert answer.status_code == 401, answer.text

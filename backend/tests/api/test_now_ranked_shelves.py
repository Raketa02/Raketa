"""Shelves 1 and 2 over HTTP: a real match, ranked by the real engines.

The unit suite asserts the funnel's rules against values and the composer's reach
against stubs. What this file adds is the half neither can reach — that a
candidate really is a `matches` row at a real club, that the badge really is the
shipped `matchfit` engine's number, that a reason really carries the quantities
the engine scored on, and that a match a player already holds a seat in really
does drop out of a suggestion she is being made.

Matches and clubs are written through the real repositories rather than through a
route, because neither has a player-facing endpoint: `POST /matches` does not
exist and `app/api/v1/club.py` carries nothing. The `client` fixture overrides
`get_db` with the same factory, so what is written here is what the request sees.
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
    zone_named,
)
from app.modules.clubs.infrastructure.sqlalchemy_club_repository import (
    SqlAlchemyClubRepository,
)
from app.modules.matches.domain.match import Match
from app.modules.matches.infrastructure.sqlalchemy_match_repository import (
    SqlAlchemyMatchRepository,
)
from app.modules.matches.infrastructure.sqlalchemy_standby_list import (
    SqlAlchemyStandbyPlaces,
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

#: The two codes shelf 1 can wear. Which one it is depends on whether anything
#: cleared 70, which is the engine's answer about a real roster and not this
#: file's business — what matters here is that the shelf is **there**.
RANKED = {"bestFit", "sameLevel"}


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


async def _join(client, payload) -> tuple[str, dict[str, str]]:
    who = await _register(client, payload)
    return who, await _sign_in(client, payload)


async def _rate_as_beginner(client, headers, sport: str = "PADEL") -> None:
    """The shortest honest path to a stored rating: answer *never played*."""

    created = (
        await client.post("/api/v1/assessments", json={"sport": sport}, headers=headers)
    ).json()
    stopped = await client.post(
        f"/api/v1/assessments/{created['assessment_id']}/answers",
        json={"question_id": created["question"]["id"], "option_id": "never-played"},
        headers=headers,
    )
    assert stopped.status_code == 200, stopped.text
    done = await client.post(
        f"/api/v1/assessments/{created['assessment_id']}/completion", headers=headers
    )
    assert done.status_code == 200, done.text


async def _write_club(session_factory, *, name: str = "Zabłocie Sport") -> Club:
    club = Club.found(
        club_id=uuid4(),
        name=ClubName(name),
        address=ADDRESS,
        point=POINT,
        timezone=zone_named("Europe/Warsaw"),
        pricing=ClubPricing(),
        policy=ClubPolicy(),
        payout=PAYOUT,
        at=SystemClock().now(),
    )
    category = club.add_category(
        category_id=uuid4(),
        name=CategoryName("Padel · hall"),
        sport=Sport.PADEL,
        cover=Cover.INDOOR,
        rate=zloty(80),
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
    """Far enough out that nothing has committed and nothing has lapsed."""

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
    async with session_factory() as session:
        repository = SqlAlchemyMatchRepository(
            session, events=_Silent(), clock=SystemClock()
        )
        await repository.add(match)
        await session.commit()
    return match


async def _queue(session_factory, match: Match, player_id: UUID) -> None:
    """Put a player on a match's standby queue, through the real store.

    There is no join route in v1 (ADR-0087), so this is the same line the seed
    catalog is the only other user of.
    """

    async with session_factory() as session:
        await SqlAlchemyStandbyPlaces(session).join(
            match_id=match.id,
            player_id=player_id,
            at=instant(datetime.now(timezone.utc).replace(microsecond=0)),
        )
        await session.commit()


def _blocks(body) -> list[dict]:
    return body["shelves"]["shelves"]


def _ranked(body) -> dict | None:
    for block in _blocks(body):
        if block["block_type"] == "shelf" and block["code"] in RANKED:
            return block
    return None


def _shelf(body, code: str) -> dict | None:
    for block in _blocks(body):
        if block["block_type"] == "shelf" and block["code"] == code:
            return block
    return None


# --- shelf 1 ----------------------------------------------------------------


async def test_an_open_match_in_her_city_reaches_the_ranked_shelf(
    client, session_factory
) -> None:
    _, alice = await _join(client, ALICE)
    bob_id, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice)
    await _rate_as_beginner(client, bob)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, seated=(UUID(bob_id),), paid=(UUID(bob_id),)
    )

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    shelf = _ranked(body)

    assert shelf is not None
    assert [card["match_id"] for card in shelf["cards"]] == [str(match.id)]
    card = shelf["cards"][0]
    assert card["card_type"] == "match"
    assert card["where"]["club_name"] == club.name.value
    assert card["where"]["cover"] == "indoor"
    assert card["price"]["amount"] == 3800


async def test_the_ranked_shelf_precedes_the_arrival_shelves(
    client, session_factory
) -> None:
    """The server's fixed order, seen from outside.

    ADR-0070 put shelf order on the server so it can move without a client
    release; this is the order it currently is, over the wire.
    """

    _, alice = await _join(client, ALICE)
    bob_id, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice)
    await _rate_as_beginner(client, bob)
    club = await _write_club(session_factory)
    await _write_match(session_factory, club, seated=(UUID(bob_id),))

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    codes = [block["code"] for block in _blocks(body)]

    assert codes[0] in RANKED
    assert "newPlayers" in codes
    assert codes.index("newPlayers") > 0


async def test_a_match_she_already_holds_a_seat_in_is_never_suggested(
    client, session_factory
) -> None:
    """`NotAlreadyMine`, over HTTP. It is on her strip and nowhere else."""

    alice_id, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, seated=(UUID(alice_id),), paid=(UUID(alice_id),)
    )

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    assert _ranked(body) is None
    assert [card["match_id"] for card in body["your_matches"]["cards"]] == [
        str(match.id)
    ]


async def test_a_match_in_another_sport_never_reaches_a_padel_chip(
    client, session_factory
) -> None:
    _, alice = await _join(client, ALICE)
    _, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice, "PADEL")
    await _rate_as_beginner(client, alice, "TENNIS")
    await _rate_as_beginner(client, bob, "PADEL")
    club = await _write_club(session_factory)
    match = await _write_match(session_factory, club)

    padel = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    tennis = (await client.get("/api/v1/now?sport=TENNIS", headers=alice)).json()

    assert _ranked(padel) is not None
    assert [card["match_id"] for card in _ranked(padel)["cards"]] == [str(match.id)]
    assert _ranked(tennis) is None


async def test_a_match_that_has_already_started_is_not_a_suggestion(
    client, session_factory
) -> None:
    _, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory,
        club,
        start=instant(
            datetime.now(timezone.utc).replace(microsecond=0) - timedelta(hours=2)
        ),
    )

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    assert _ranked(body) is None


# --- shelf 2 ----------------------------------------------------------------


async def test_a_full_future_match_reaches_the_waitlist_shelf(
    client, session_factory
) -> None:
    """*Full, but worth waiting for* — the shelf whose whole claim is the 80.

    A full match outranks the joinable version of itself, which is why the two
    lanes cannot be one ordered list: it would be topped by matches nobody can
    join.
    """

    _, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice)
    club = await _write_club(session_factory)
    others = tuple(uuid4() for _ in range(4))
    full = await _write_match(session_factory, club, seated=others, paid=others)

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    shelf = _shelf(body, "fullWorthWaiting")

    assert shelf is not None
    assert [card["match_id"] for card in shelf["cards"]] == [str(full.id)]
    assert shelf["cards"][0]["situation"]["facts"]["counts"] == {
        "seats": 4,
        "paid": 4,
        "held": 0,
        "turned_up": None,
    }


async def test_the_two_lanes_never_hold_the_same_match(
    client, session_factory
) -> None:
    """One rule apart, and the rule is exclusive: free seat against full."""

    _, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice)
    club = await _write_club(session_factory)
    others = tuple(uuid4() for _ in range(4))
    await _write_match(session_factory, club, seated=others, paid=others)
    await _write_match(session_factory, club, start=_soon(days=5))

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    ranked = _ranked(body)
    waiting = _shelf(body, "fullWorthWaiting")

    assert ranked is not None and waiting is not None
    assert not {card["match_id"] for card in ranked["cards"]} & {
        card["match_id"] for card in waiting["cards"]
    }


# --- the badge --------------------------------------------------------------


async def test_the_badge_crosses_with_a_number_reasons_and_no_coverage(
    client, session_factory
) -> None:
    """Everything ADR-0037 says a card may say about its score, and nothing else.

    Coverage ranks, gates emphasis and may become words in a reason line. It
    never becomes a second gauge, and the way that is guaranteed is that it does
    not cross at all.
    """

    _, alice = await _join(client, ALICE)
    bob_id, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice)
    await _rate_as_beginner(client, bob)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, seated=(UUID(bob_id),), paid=(UUID(bob_id),)
    )

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    fit = _ranked(body)["cards"][0]["fit"]

    assert 20 <= fit["score"] <= 99
    assert set(fit) == {"score", "unsure", "reasons", "target"}
    assert 0 < len(fit["reasons"]) <= 3
    assert "coverage" not in fit


async def test_a_reason_carries_its_own_typed_quantities_and_no_sentence(
    client, session_factory
) -> None:
    """The delta's §3: *the term code and its typed fact payload*.

    Not the weight, not the value, not the contribution — and never a sentence,
    because the two clients do not share a language or a currency symbol.
    """

    _, alice = await _join(client, ALICE)
    bob_id, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice)
    await _rate_as_beginner(client, bob)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, seated=(UUID(bob_id),), paid=(UUID(bob_id),)
    )

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    reasons = _ranked(body)["cards"][0]["fit"]["reasons"]

    for reason in reasons:
        assert set(reason) == {"code", "fact"}
        assert reason["fact"]["code"] == reason["code"]
        assert not {"weight", "value", "contribution"} & set(reason["fact"])
    codes = {reason["code"] for reason in reasons}
    # The sentinel may rank and may never be printed: no player has a location,
    # so a travel reason would print minutes nobody measured.
    assert "travel" not in codes


async def test_a_skill_overlap_reason_says_which_side_she_fell_on(
    client, session_factory
) -> None:
    """*You would be the strongest here* and *you would be stretched* differ.

    The term is symmetric, so its value cannot say — and choosing a sentence from
    the sign of a subtraction is a rule the phone does not hold.
    """

    _, alice = await _join(client, ALICE)
    bob_id, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice)
    await _rate_as_beginner(client, bob)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, seated=(UUID(bob_id),), paid=(UUID(bob_id),)
    )

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    reasons = _ranked(body)["cards"][0]["fit"]["reasons"]
    overlap = [one for one in reasons if one["code"] == "skill_overlap"]

    if overlap:
        fact = overlap[0]["fact"]
        assert fact["side"] in {"stretched", "strongest", "even"}
        assert set(fact) >= {"level", "target", "side"}


async def test_a_shelf_card_names_no_act_and_offers_no_exit(
    client, session_factory
) -> None:
    """ADR-0083: a card names an act when a v1 surface can receive it.

    The seat claim a suggestion's *take a seat* would open is #89, so this goes
    red the day that lands — which is when the act is composed.
    """

    _, alice = await _join(client, ALICE)
    _, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice)
    await _rate_as_beginner(client, bob)
    club = await _write_club(session_factory)
    await _write_match(session_factory, club)

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    card = _ranked(body)["cards"][0]

    assert card["act"] is None
    assert card["may_depart"] is False
    assert card["seat_claim"] is None
    assert card["emphasis"] is False


# --- the door takes their place --------------------------------------------


async def test_a_sport_she_holds_no_rating_at_composes_a_door_and_no_shelves(
    client, session_factory
) -> None:
    """A player with no rating cannot be ranked, so the two shelves are absent.

    Not empty and not beneath the door — there is nothing for them to hold, and
    ADR-0084 puts the door in exactly their position.
    """

    _, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice, "PADEL")
    club = await _write_club(session_factory)
    await _write_match(session_factory, club)

    body = (await client.get("/api/v1/now?sport=SQUASH", headers=alice)).json()
    blocks = _blocks(body)

    assert [block["block_type"] for block in blocks][0] == "door"
    assert _ranked(body) is None
    assert _shelf(body, "fullWorthWaiting") is None


async def test_a_match_she_is_queued_for_is_never_suggested_to_her(
    client, session_factory
) -> None:
    """`NotOnStandby`, firing for the first time in the product.

    The rule has been one of the funnel's eight since the funnel shipped, and it
    was evaluated against an adapter that answered the empty set for everybody,
    because standby had no store (`Raketa02/Raketa#81`). The defect it exists for
    is a screen suggesting a player the match she has already asked about.
    """

    alice_id, alice = await _join(client, ALICE)
    bob_id, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice)
    await _rate_as_beginner(client, bob)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, seated=(UUID(bob_id),), paid=(UUID(bob_id),)
    )

    before = _ranked(
        (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    )
    assert before is not None
    assert [card["match_id"] for card in before["cards"]] == [str(match.id)]

    await _queue(session_factory, match, UUID(alice_id))

    after = _ranked(
        (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    )
    assert after is None or str(match.id) not in {
        card["match_id"] for card in after["cards"]
    }


async def test_somebody_else_s_queue_place_suggests_her_nothing_less(
    client, session_factory
) -> None:
    """The rule is about the viewer's own queue and not about the match's.

    A read that dropped the player from its predicate would take a popular
    match off everybody's shelves the moment one person queued for it.
    """

    _, alice = await _join(client, ALICE)
    bob_id, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice)
    await _rate_as_beginner(client, bob)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, seated=(UUID(bob_id),), paid=(UUID(bob_id),)
    )
    await _queue(session_factory, match, UUID(bob_id))

    shelf = _ranked(
        (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    )

    assert shelf is not None
    assert [card["match_id"] for card in shelf["cards"]] == [str(match.id)]

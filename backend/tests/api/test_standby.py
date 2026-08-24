"""The standby route over HTTP: the card, the button, the write, the gap it leaves.

The unit suite asserts the rules against stubs. What this file adds is the half
neither it nor the store suite can reach — that the route is really mounted,
that a queued player's card really arrives on `GET /api/v1/now` with its act on
it, that the `DELETE` really takes the card off the next screen, and that the
wire really carries ADR-0070's *this card is gone* rather than an emptied card.

That last one is the reason this file exists rather than a case in the unit
suite. `NowUpdate` is a union of two frozen dataclasses and `NowUpdateResponse`
is a discriminated union over two Pydantic models; a `from_domain` that rendered
the wrong member, or dropped the discriminator, would pass every rule test in
the tree and ship a client an update it cannot narrow.

Matches and clubs are written through the real repositories, exactly as
`tests/api/test_departure.py` does and for the same reason: neither has a
player-facing endpoint to write one with.
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
    zone_named as _zone,
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


class _Silent:
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


async def _write_club(session_factory) -> Club:
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
        await SqlAlchemyClubRepository(session).add(club)
        await session.commit()
    return club


def _now() -> Instant:
    return instant(datetime.now(timezone.utc).replace(microsecond=0))


def _in(hours_ahead: float) -> Instant:
    return instant(_now() + timedelta(hours=hours_ahead))


async def _write_match(
    session_factory,
    club: Club,
    *,
    start: Instant,
    seated: tuple[UUID, ...] = (),
    paid: tuple[UUID, ...] = (),
) -> Match:
    at = instant(datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=7))
    match = Match.post(
        match_id=uuid4(),
        club_id=club.id,
        category_id=club.live_categories[0].id,
        sport=Sport.PADEL,
        start=start,
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


async def _queue(session_factory, match: Match, player: UUID) -> None:
    """The only way onto a queue in v1: there is no join route (ADR-0087).

    The waitlist toggle is a match-screen control and the match screen is out of
    scope, so the seed catalog and this line are the whole set of writers. It
    goes through the real adapter rather than an `INSERT`, so what these cases
    are drawn against is the row a `JoinStandby` produces.
    """

    async with session_factory() as session:
        await SqlAlchemyStandbyPlaces(session).join(
            match_id=match.id, player_id=player, at=_now()
        )
        await session.commit()


def _url(match: Match) -> str:
    return f"/api/v1/matches/{match.id}/standby"


def _cards(body) -> list[dict]:
    return body["your_matches"]["cards"]


# --- the card the act arrives on --------------------------------------------


async def test_a_queued_match_is_on_the_strip_and_names_the_act(
    client, session_factory
) -> None:
    """The half ADR-0087 needed before its write meant anything.

    `waitlisted` is the one situation only a viewer can be in, and the strip is
    the only region on Now that could hold its card: the offers region is seats
    offered to her, and the ranked shelves exclude a match she is queued for.
    """

    alice, headers = await _join(client, ALICE)
    bob, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(72), seated=(bob,), paid=(bob,)
    )
    await _queue(session_factory, match, alice)

    body = (await client.get("/api/v1/now", headers=headers)).json()

    assert [card["match_id"] for card in _cards(body)] == [str(match.id)]
    assert _cards(body)[0]["situation"]["situation"] == "waitlisted"
    assert _cards(body)[0]["act"] == "leaveStandby"


async def test_a_seat_holder_on_the_same_match_sees_her_own_card(
    client, session_factory
) -> None:
    """One record, two viewers, two situations — and only one names an act."""

    alice, alice_headers = await _join(client, ALICE)
    bob, bob_headers = await _join(client, BOB)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(72), seated=(bob,), paid=(bob,)
    )
    await _queue(session_factory, match, alice)

    body = (await client.get("/api/v1/now", headers=bob_headers)).json()

    assert _cards(body)[0]["situation"]["situation"] != "waitlisted"
    assert _cards(body)[0]["act"] is None


async def test_a_queued_match_is_not_suggested_on_a_ranked_shelf(
    client, session_factory
) -> None:
    """`NotOnStandby` shipped against an adapter that answered nobody.

    This is the first case in the tree where that rule can fire at all, and it
    is the defect the empty adapter was written to make impossible: a screen
    suggesting a player the match she is already queued for.
    """

    alice, headers = await _join(client, ALICE)
    bob, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(72), seated=(bob,), paid=(bob,)
    )
    await _queue(session_factory, match, alice)

    body = (await client.get("/api/v1/now", headers=headers)).json()

    suggested = {
        card["match_id"]
        for block in body["shelves"]["shelves"]
        if block["block_type"] == "shelf"
        for card in block["cards"]
        if card["card_type"] == "match"
    }
    assert str(match.id) not in suggested


# --- the write --------------------------------------------------------------


async def test_leaving_answers_the_gone_form_and_takes_the_card_off_now(
    client, session_factory
) -> None:
    """ADR-0070's *this card is no longer on your screen*, over the wire.

    Both halves, because either alone can be right while the other is wrong: the
    update says the card has gone, and the next compose no longer draws it.
    """

    alice, headers = await _join(client, ALICE)
    bob, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(72), seated=(bob,), paid=(bob,)
    )
    await _queue(session_factory, match, alice)

    answer = await client.delete(_url(match), headers=headers)

    assert answer.status_code == 200, answer.text
    assert answer.json()["update"] == {
        "update_type": "gone",
        "match_id": str(match.id),
    }

    body = (await client.get("/api/v1/now", headers=headers)).json()
    assert _cards(body) == []


async def test_the_gone_form_carries_no_card_at_all(client, session_factory) -> None:
    """Asserted as the *absence of a key*, not as a null.

    A nullable card would leave *it is gone* and *this build sent none* looking
    identical, which is the blank ADR-0072 refuses for the leaver's money. The
    discriminated union is what makes reading one a narrowing error, and it is
    only true if the member genuinely has no field for it.
    """

    alice, headers = await _join(client, ALICE)
    bob, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(72), seated=(bob,), paid=(bob,)
    )
    await _queue(session_factory, match, alice)

    answer = await client.delete(_url(match), headers=headers)

    assert "card" not in answer.json()["update"]


async def test_leaving_twice_answers_what_leaving_once_answered(
    client, session_factory
) -> None:
    """The acceptance criterion, and the reason there is no idempotency key.

    *A repeated delete of a standby place a player no longer holds is the state
    they asked for* — so the second answer is not merely a success, it is the
    same document.
    """

    alice, headers = await _join(client, ALICE)
    bob, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(72), seated=(bob,), paid=(bob,)
    )
    await _queue(session_factory, match, alice)

    first = await client.delete(_url(match), headers=headers)
    second = await client.delete(_url(match), headers=headers)

    assert second.status_code == 200, second.text
    assert second.json() == first.json()


async def test_a_player_who_never_queued_gets_what_a_success_gets(
    client, session_factory
) -> None:
    """Anybody may queue for any match, so there is nobody to be a stranger to.

    The one thing a membership gate would buy here is a refusal, and ADR-0087
    has nothing to refuse: nothing is lost, so there is nothing to report.
    """

    alice, headers = await _join(client, ALICE)
    bob, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(72), seated=(bob,), paid=(bob,)
    )

    answer = await client.delete(_url(match), headers=headers)

    assert answer.status_code == 200, answer.text
    assert answer.json()["update"]["update_type"] == "gone"


async def test_a_seat_holder_who_also_queued_keeps_her_card(
    client, session_factory
) -> None:
    """She is still something to the match, so the *changed* form comes back.

    The card is the one the strip draws, off the same `card_of`, so an action
    cannot correct Now onto a card that disagrees with the screen it came from.
    """

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(72), seated=(alice,), paid=(alice,)
    )
    await _queue(session_factory, match, alice)

    answer = await client.delete(_url(match), headers=headers)

    update = answer.json()["update"]
    assert update["update_type"] == "card"
    assert update["card"]["match_id"] == str(match.id)
    assert update["card"]["act"] is None


async def test_the_route_takes_no_body_and_no_idempotency_key(
    client, session_factory
) -> None:
    """ADR-0030's log is for *destructive* commands, and this one is not.

    A key is what manufactures idempotency for an act that has none of its own;
    this one is idempotent by nature, so a key would be a field with nothing to
    do and a table row per tap.
    """

    alice, headers = await _join(client, ALICE)
    bob, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(72), seated=(bob,), paid=(bob,)
    )
    await _queue(session_factory, match, alice)

    answer = await client.delete(_url(match), headers=headers)

    assert answer.status_code == 200, answer.text
    assert set(answer.json()) == {"update"}


async def test_a_match_that_does_not_exist_is_a_404(client, session_factory) -> None:
    """The only refusal, and it is about the address rather than about the act."""

    _, headers = await _join(client, ALICE)

    answer = await client.delete(f"/api/v1/matches/{uuid4()}/standby", headers=headers)

    assert answer.status_code == 404, answer.text


async def test_the_route_needs_a_signed_in_player(client, session_factory) -> None:
    club = await _write_club(session_factory)
    match = await _write_match(session_factory, club, start=_in(72))

    answer = await client.delete(_url(match))

    assert answer.status_code == 401, answer.text


async def test_leaving_takes_off_this_player_and_leaves_the_queue_standing(
    client, session_factory
) -> None:
    """One tap empties one pair, never a match's queue.

    The cascade reads the list when a seat frees, so a delete that widened by
    one column would silently unsubscribe everybody who had asked.
    """

    alice, alice_headers = await _join(client, ALICE)
    bob, bob_headers = await _join(client, BOB)
    club = await _write_club(session_factory)
    match = await _write_match(session_factory, club, start=_in(72))
    await _queue(session_factory, match, alice)
    await _queue(session_factory, match, bob)

    await client.delete(_url(match), headers=alice_headers)

    body = (await client.get("/api/v1/now", headers=bob_headers)).json()
    assert [card["match_id"] for card in _cards(body)] == [str(match.id)]

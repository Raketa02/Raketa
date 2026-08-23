"""The departure route over HTTP: the quote, the table, and leaving.

The unit suite asserts the rules against stubs. What this file adds is the half
neither it nor the adapter suite can reach — that the route really is mounted,
that the wire really carries every field the decisions name, that a leaver's
`GET` really resolves where a stranger's 404s, and that a second `POST` under
one key really leaves one departure on the match rather than two.

Matches and clubs are written through the real repositories, exactly as
`tests/api/test_now_enrolled.py` does and for the same reason: neither has a
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
    MatchKind,
    PayModel,
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
CAROL = {
    "email": "carol@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "carol",
}
DAVE = {
    "email": "dave@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "dave",
}
ERIN = {
    "email": "erin@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "erin",
}

ADDRESS = StreetAddress(line="ul. Zabłocie 25", city="Kraków", postal_code="30-701")
POINT = GeoPoint(latitude=Decimal("50.048100"), longitude=Decimal("19.958500"))
PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
)
SHARE = SeatShare(grosze(3800))
KEY = "3f0d2f7e-0000-4000-8000-000000000001"


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


def _moment(value: str) -> datetime:
    """A wire instant as a value, so a test never compares two spellings of one.

    The document renders UTC as `Z` and `datetime.isoformat()` renders it as
    `+00:00`; both are the same instant, and asserting on the text would be
    asserting on the serialiser.
    """

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def _write_match(
    session_factory,
    club: Club,
    *,
    start: Instant,
    seated: tuple[UUID, ...] = (),
    paid: tuple[UUID, ...] = (),
    claimed: UUID | None = None,
    kind: MatchKind = MatchKind.OPEN,
    pay_model: PayModel = PayModel.SOLO,
    open_seats: int = 0,
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
    match.kind = kind
    match.pay_model = pay_model
    match.open_seats = open_seats
    for player in seated:
        match.take_seat(player, at=at)
    for player in paid:
        match.pay_seat(player, at=at)
    # A full match past its own commitment deadline is committed, and it is the
    # only way to reach the three money outcomes: `pay_seat` checks commitment
    # at the instant the money landed, and these seats were paid a week ago.
    match.commit_if_due(at=_now())
    if claimed is not None:
        match.open_claim(claimed, at=_now())
    async with session_factory() as session:
        repository = SqlAlchemyMatchRepository(
            session, events=_Silent(), clock=SystemClock()
        )
        await repository.add(match)
        await session.commit()
    return match


def _url(match: Match) -> str:
    return f"/api/v1/matches/{match.id}/departure"


def _standings(body) -> dict[str, str]:
    return {row["outcome"]: row["standing"] for row in body["outcomes"]}


# --- reading the quote ------------------------------------------------------


async def test_the_route_prints_all_four_outcomes_and_the_one_that_is_live(
    client, session_factory
) -> None:
    """*"A table that quietly drops forfeited once it is unreachable is also a
    table that never showed it while it was."*"""

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )

    answer = await client.get(_url(match), headers=headers)

    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert [row["outcome"] for row in body["outcomes"]] == [
        "reversed",
        "refundedInFull",
        "refundedHalf",
        "forfeited",
    ]
    # Four days out and one seat paid: nothing has committed, so leaving is free
    # and the three money outcomes are a *fill* away rather than a moment away.
    assert body["quote"] == "reversed"
    assert _standings(body) == {
        "reversed": "searching",
        "refundedInFull": "stillPossible",
        "refundedHalf": "stillPossible",
        "forfeited": "stillPossible",
    }
    assert all(row["opens_at"] is None for row in body["outcomes"])


async def test_a_committed_match_names_the_moments_the_two_ahead_open_at(
    client, session_factory
) -> None:
    """The quote's reasons, as moments the phone subtracts and nothing else."""

    alice, headers = await _join(client, ALICE)
    others = [await _join(client, who) for who in (BOB, CAROL, DAVE)]
    club = await _write_club(session_factory)
    start = _in(10)
    match = await _write_match(
        session_factory,
        club,
        start=start,
        seated=(alice, *(who for who, _ in others)),
        paid=(alice, *(who for who, _ in others)),
    )

    body = (await client.get(_url(match), headers=headers)).json()

    assert body["quote"] == "refundedInFull"
    assert _standings(body) == {
        "reversed": "spent",
        "refundedInFull": "searching",
        "refundedHalf": "opens",
        "forfeited": "opens",
    }
    opens = {row["outcome"]: row["opens_at"] for row in body["outcomes"]}
    assert _moment(opens["refundedHalf"]) == start - timedelta(hours=4)
    assert _moment(opens["forfeited"]) == start - timedelta(hours=2)
    assert opens["reversed"] is None


async def test_the_screen_carries_the_deadline_the_amount_and_how_full_it_is(
    client, session_factory
) -> None:
    """ADR-0086's three facts behind the outcome, and no `phase` beside them."""

    alice, headers = await _join(client, ALICE)
    bob, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    start = _in(96)
    match = await _write_match(
        session_factory, club, start=start, seated=(alice, bob), paid=(alice,)
    )

    body = (await client.get(_url(match), headers=headers)).json()

    assert _moment(body["commitment_deadline"]) == start - timedelta(hours=24)
    assert body["price"] == {"amount": 3800, "currency": "PLN"}
    assert body["counts"] == {"seats": 4, "paid": 1, "held": 1, "turned_up": None}
    assert "phase" not in body


async def test_the_screen_is_not_a_card(client, session_factory) -> None:
    """No fit badge, no emphasis flag, no card stamp — none means anything here."""

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )

    body = (await client.get(_url(match), headers=headers)).json()

    assert "fit" not in body
    assert "emphasis" not in body
    assert "stamp" not in body
    assert "card_type" not in body
    # What it does keep is the spine and the situation half, off the same ladder.
    assert body["where"]["club_name"] == club.name.value
    assert body["situation"]["situation"] == "forming"


async def test_nothing_on_the_screen_mentions_transferring_a_seat(
    client, session_factory
) -> None:
    """*"Advertising a door that is not there is worse than the gap."*"""

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )

    raw = (await client.get(_url(match), headers=headers)).text.lower()

    assert "transfer" not in raw


async def test_a_stranger_gets_a_404(client, session_factory) -> None:
    """Authorisation, and the one place a different shape is right."""

    alice, _ = await _join(client, ALICE)
    _, stranger = await _join(client, BOB)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )

    answer = await client.get(_url(match), headers=stranger)

    assert answer.status_code == 404, answer.text


# --- may this person leave --------------------------------------------------


async def test_a_seated_player_may_leave(client, session_factory) -> None:
    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )

    assert (await client.get(_url(match), headers=headers)).json()["may_depart"]


async def test_a_match_that_has_started_offers_no_departure(
    client, session_factory
) -> None:
    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(-1), seated=(alice,), paid=(alice,)
    )

    body = (await client.get(_url(match), headers=headers)).json()

    assert body["may_depart"] is False
    assert len(body["outcomes"]) == 4


async def test_a_viewer_holding_a_live_seat_claim_may_not_leave(
    client, session_factory
) -> None:
    """ADR-0081 fixes that a claim holds no seat yet.

    Her route opens — she is something to this match — and answers *no*:
    abandoning a payment must not be dressed as leaving.
    """

    alice, headers = await _join(client, ALICE)
    bob, _ = await _join(client, BOB)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory,
        club,
        start=_in(96),
        seated=(bob,),
        paid=(bob,),
        claimed=alice,
    )

    answer = await client.get(_url(match), headers=headers)

    assert answer.status_code == 200, answer.text
    assert answer.json()["may_depart"] is False


async def test_a_full_converted_private_court_locks_past_the_clubs_deadline(
    client, session_factory
) -> None:
    """ADR-0046: *"nobody may leave and no refunds are issued."*

    The default club's cancellation window is twenty-four hours, so a court
    starting in ten is locked and one starting in a week is not.
    """

    alice, headers = await _join(client, ALICE)
    others = [await _join(client, who) for who in (BOB, CAROL, DAVE)]
    club = await _write_club(session_factory)
    seats = (alice, *(who for who, _ in others))

    locked = await _write_match(
        session_factory,
        club,
        start=_in(10),
        seated=seats,
        paid=seats,
        kind=MatchKind.PRIVATE,
        pay_model=PayModel.SPLIT,
    )
    open_still = await _write_match(
        session_factory,
        club,
        start=_in(96),
        seated=seats,
        paid=seats,
        kind=MatchKind.PRIVATE,
        pay_model=PayModel.SPLIT,
    )

    shut = (await client.get(_url(locked), headers=headers)).json()
    free = (await client.get(_url(open_still), headers=headers)).json()

    assert shut["may_depart"] is False
    assert free["may_depart"] is True
    # Two rows either way: only *refunded in full* and *forfeited* are reachable
    # on a private court, and no commitment deadline exists to name.
    assert len(shut["outcomes"]) == 2
    assert shut["commitment_deadline"] is None


async def test_the_write_refuses_the_lock_and_not_only_the_control(
    client, session_factory
) -> None:
    """A boolean the write does not enforce is a rule held only on the phone."""

    alice, headers = await _join(client, ALICE)
    others = [await _join(client, who) for who in (BOB, CAROL, DAVE)]
    club = await _write_club(session_factory)
    seats = (alice, *(who for who, _ in others))
    match = await _write_match(
        session_factory,
        club,
        start=_in(10),
        seated=seats,
        paid=seats,
        kind=MatchKind.PRIVATE,
        pay_model=PayModel.SPLIT,
    )

    answer = await client.post(
        _url(match),
        headers=headers,
        json={"quote": "refundedInFull", "idempotency_key": KEY},
    )

    assert answer.status_code == 200, answer.text
    # Nothing happened: she still holds her seat, and the screen says so.
    assert answer.json()["applied"] is None
    assert answer.json()["screen"]["may_depart"] is False
    assert answer.json()["screen"]["counts"]["paid"] == 4


# --- leaving ----------------------------------------------------------------


async def test_leaving_returns_this_screen_and_nows_update_in_one_response(
    client, session_factory
) -> None:
    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )

    answer = await client.post(
        _url(match),
        headers=headers,
        json={"quote": "reversed", "idempotency_key": KEY},
    )

    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["screen"]["match_id"] == str(match.id)
    assert body["screen"]["may_depart"] is False
    assert body["update"]["card"]["match_id"] == str(match.id)
    assert body["update"]["card"]["card_type"] == "match"
    # Her seat is gone, so nobody has paid for this match any more.
    assert body["screen"]["counts"]["paid"] == 0
    # What the tap **did**, said as a fact so the client need not derive it.
    assert body["applied"] == "reversed"


async def test_the_card_comes_back_changed_in_place_and_rendered_for_a_leaver(
    client, session_factory
) -> None:
    """ADR-0086's first mid-session audience change, over the wire.

    Nothing is removed and no region moves: the same match, the same region, a
    new rendering — and the strip agrees with the update without a second fetch.
    """

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )

    update = (
        await client.post(
            _url(match),
            headers=headers,
            json={"quote": "reversed", "idempotency_key": KEY},
        )
    ).json()["update"]["card"]

    strip = (await client.get("/api/v1/now", headers=headers)).json()["your_matches"]
    assert [card["match_id"] for card in strip["cards"]] == [str(match.id)]
    on_now = strip["cards"][0]

    assert update["situation"] == on_now["situation"]
    assert update["may_depart"] == on_now["may_depart"] is False
    # A leave before commitment took nothing, so her card names no amount at all.
    assert update["situation"]["facts"]["departure"] == {"form": "nothingTaken"}


async def test_a_leaver_who_paid_carries_her_amount_and_no_outcome_yet(
    client, session_factory
) -> None:
    """Her money is decided by her seat refilling, and nothing has yet."""

    alice, headers = await _join(client, ALICE)
    others = [await _join(client, who) for who in (BOB, CAROL, DAVE)]
    club = await _write_club(session_factory)
    seats = (alice, *(who for who, _ in others))
    match = await _write_match(
        session_factory, club, start=_in(10), seated=seats, paid=seats
    )

    body = (
        await client.post(
            _url(match),
            headers=headers,
            json={"quote": "refundedInFull", "idempotency_key": KEY},
        )
    ).json()

    departure = body["update"]["card"]["situation"]["facts"]["departure"]
    assert departure == {
        "form": "recoverable",
        "paid": {"amount": 3800, "currency": "PLN"},
        "outcome": None,
    }


async def test_a_leavers_route_resolves_rather_than_404ing(
    client, session_factory
) -> None:
    """*"A 404 tells a leaver their match never existed."*"""

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )
    await client.post(
        _url(match),
        headers=headers,
        json={"quote": "reversed", "idempotency_key": KEY},
    )

    answer = await client.get(_url(match), headers=headers)

    assert answer.status_code == 200, answer.text
    assert answer.json()["may_depart"] is False
    assert len(answer.json()["outcomes"]) == 4


# --- the key, and the refusal path ------------------------------------------


async def test_a_replayed_key_returns_the_first_answer_and_writes_nothing(
    client, session_factory
) -> None:
    """One departure on the match, not two — asserted on the record itself."""

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )
    body = {"quote": "reversed", "idempotency_key": KEY}

    first = await client.post(_url(match), headers=headers, json=body)
    again = await client.post(_url(match), headers=headers, json=body)

    assert first.status_code == again.status_code == 200
    assert again.json()["screen"]["may_depart"] is False
    # *The first outcome*, off the command log rather than off the aggregate.
    assert again.json()["applied"] == first.json()["applied"] == "reversed"

    async with session_factory() as session:
        stored = await SqlAlchemyMatchRepository(
            session, events=_Silent(), clock=SystemClock()
        ).get(match.id)
    assert stored is not None
    assert len(stored.departures) == 1
    assert len(stored.vacancies) == 1


async def test_another_players_key_is_refused(client, session_factory) -> None:
    """A client's key is its own to choose, so two clients can choose one."""

    alice, alice_headers = await _join(client, ALICE)
    bob, bob_headers = await _join(client, BOB)
    club = await _write_club(session_factory)
    hers = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )
    his = await _write_match(
        session_factory, club, start=_in(96), seated=(bob,), paid=(bob,)
    )
    body = {"quote": "reversed", "idempotency_key": KEY}

    await client.post(_url(hers), headers=alice_headers, json=body)
    collision = await client.post(_url(his), headers=bob_headers, json=body)

    assert collision.status_code == 409, collision.text
    assert collision.json()["code"] == "command_key_belongs_to_another"


async def test_a_quote_that_has_become_worse_is_refused_with_the_new_one(
    client, session_factory
) -> None:
    """*"She never gets less than quoted, silently."*

    A committed match an hour from its start is past the checkpoint, so leaving
    it is worth nothing — and a phone still holding *refunded in full* is
    corrected rather than obeyed.
    """

    alice, headers = await _join(client, ALICE)
    others = [await _join(client, who) for who in (BOB, CAROL, DAVE)]
    club = await _write_club(session_factory)
    seats = (alice, *(who for who, _ in others))
    match = await _write_match(
        session_factory, club, start=_in(1), seated=seats, paid=seats
    )

    answer = await client.post(
        _url(match),
        headers=headers,
        json={"quote": "refundedInFull", "idempotency_key": KEY},
    )

    assert answer.status_code == 200, answer.text
    screen = answer.json()["screen"]
    assert screen["quote"] == "forfeited"
    assert _standings(screen)["forfeited"] == "searching"
    # Refused, and said so: `applied` is null exactly when nothing was applied,
    # which is what stops *was I refused* being a rule on the phone.
    assert answer.json()["applied"] is None
    # She still holds her seat and may still decide to go.
    assert screen["may_depart"] is True
    assert screen["counts"]["paid"] == 4


async def test_a_forfeit_quoted_against_a_reversal_goes_through(
    client, session_factory
) -> None:
    """Equal or better applies: the quote protects money, and here it is nothing.

    What is recorded is the **reversal** the aggregate recomputed, not the
    forfeit that crossed the wire.
    """

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )

    answer = await client.post(
        _url(match),
        headers=headers,
        json={"quote": "forfeited", "idempotency_key": KEY},
    )

    assert answer.status_code == 200, answer.text
    assert answer.json()["screen"]["may_depart"] is False
    assert answer.json()["applied"] == "reversed"

    async with session_factory() as session:
        stored = await SqlAlchemyMatchRepository(
            session, events=_Silent(), clock=SystemClock()
        ).get(match.id)
    assert stored is not None
    assert stored.departures[0].quoted.value == "reversed"


async def test_a_second_tap_without_a_key_is_still_the_screen(
    client, session_factory
) -> None:
    """The naive retry, and the reason the log's absence is survivable."""

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )
    await client.post(
        _url(match),
        headers=headers,
        json={"quote": "reversed", "idempotency_key": KEY},
    )

    again = await client.post(
        _url(match),
        headers=headers,
        json={"quote": "reversed", "idempotency_key": "a-second-key"},
    )

    assert again.status_code == 200, again.text
    assert again.json()["screen"]["may_depart"] is False


async def test_the_key_is_required(client, session_factory) -> None:
    """ADR-0030 requires it of every destructive command."""

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )

    answer = await client.post(_url(match), headers=headers, json={"quote": "reversed"})

    assert answer.status_code == 422, answer.text


async def test_the_route_needs_a_bearer(client, session_factory) -> None:
    club = await _write_club(session_factory)
    alice, _ = await _join(client, ALICE)
    match = await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )

    assert (await client.get(_url(match))).status_code == 401


# --- the card on Now points at the route ------------------------------------


async def test_the_strip_now_offers_the_exit_it_could_not_offer_before(
    client, session_factory
) -> None:
    """ADR-0083's rule satisfied rather than bent: the surface exists now.

    It is a **spine boolean** and not a seventh act code — the card's `act` is
    still absent, because leaving is not the card's act.
    """

    alice, headers = await _join(client, ALICE)
    club = await _write_club(session_factory)
    await _write_match(
        session_factory, club, start=_in(96), seated=(alice,), paid=(alice,)
    )

    card = (await client.get("/api/v1/now", headers=headers)).json()["your_matches"][
        "cards"
    ][0]

    assert card["may_depart"] is True
    assert card["act"] is None

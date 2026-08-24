"""The result route over HTTP: five renderings, two clocks, and three writes.

The unit suite asserts the rules against stubs. What this file adds is the half
neither it nor the adapter suite can reach — that the route really is mounted,
that the wire really carries every field the decisions name, that a leaver's
`GET` really resolves where a stranger's 404s, and that a real proposal really
comes back through the ladder as `confirmResult` for one side and as an
acceptable score for the other.

It also carries the assertion the enrolled strip's counting taught this tree to
write: a `from_domain` that dropped a field or built one of its own passes every
unit test and ships a screen that looks exactly like an ordinary screen. So the
block's four facts, the two clocks and the three booleans are asserted **on the
rendered document** and not only on the value behind it.

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

#: A real padel scoreline, in the order side A won it.
SETS = [[6, 4], [7, 6]]


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
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def _played_match(
    session_factory,
    club: Club,
    *,
    seated: tuple[UUID, ...],
    left: UUID | None = None,
) -> Match:
    """A full padel match that finished two hours ago.

    Seats are taken in the order given, so the first two are side A and the last
    two side B — Matches' own definition, and the thing the score means.
    """

    at = instant(datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=7))
    match = Match.post(
        match_id=uuid4(),
        club_id=club.id,
        category_id=club.live_categories[0].id,
        sport=Sport.PADEL,
        start=_in(-3),
        duration=hours(1),
        share=SHARE,
        policy=club.policy_now.hold_policy(),
        at=at,
    )
    for player in seated:
        match.take_seat(player, at=at)
        match.pay_seat(player, at=at)
    match.commit_if_due(at=_in(-24))
    if left is not None:
        match.depart(left, quote=live_outcome(match.as_record(), _in(-4)), at=_in(-4))
    async with session_factory() as session:
        repository = SqlAlchemyMatchRepository(
            session, events=_Silent(), clock=SystemClock()
        )
        await repository.add(match)
        await session.commit()
    return match


def _url(match: Match) -> str:
    return f"/api/v1/matches/{match.id}/result"


async def _four_who_played(client, session_factory):
    """Four registered players, a club, and a match all four have played."""

    people = [await _join(client, who) for who in (ALICE, BOB, CAROL, DAVE)]
    club = await _write_club(session_factory)
    match = await _played_match(
        session_factory, club, seated=tuple(who for who, _ in people)
    )
    return people, match


# --- reading: five renderings, one reader -----------------------------------


async def test_a_played_match_asks_for_a_score_and_carries_an_empty_table(
    client, session_factory
) -> None:
    people, match = await _four_who_played(client, session_factory)
    _, headers = people[0]

    answer = await client.get(_url(match), headers=headers)

    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["situation"]["situation"] == "needsResult"
    # Present and empty rather than absent: the block makes no claim, so it
    # follows a region's rule rather than a shelf's.
    assert body["result"] == {
        "agreed": False,
        "proposals": 0,
        "score": None,
        "proposed_by": None,
    }
    assert body["may_enter"] is True
    assert body["may_accept"] is False
    assert body["may_counter"] is False


async def test_the_spine_crosses_verbatim_and_the_screen_is_not_a_card(
    client, session_factory
) -> None:
    people, match = await _four_who_played(client, session_factory)
    _, headers = people[0]

    body = (await client.get(_url(match), headers=headers)).json()

    assert body["match_id"] == str(match.id)
    assert body["where"]["club_name"].startswith("Zabłocie")
    assert body["where"]["cover"] == "indoor"
    assert body["price"] == {"amount": int(SHARE), "currency": "PLN"}
    # Not a card: three judgements the composition makes about a card's place on
    # Now, and none of them means anything on a screen with one thing on it.
    assert "fit" not in body
    assert "emphasis" not in body
    assert "stamp" not in body
    # And no phase and no version, both refused by name.
    assert "phase" not in body
    assert "version" not in body


async def test_the_counting_rides_beside_the_conversation(
    client, session_factory
) -> None:
    """Asserted on the rendered document, because a `from_domain` that built its
    own numbers passes every unit test and ships an ordinary-looking screen."""

    people, match = await _four_who_played(client, session_factory)
    _, headers = people[0]

    body = (await client.get(_url(match), headers=headers)).json()

    assert body["counts"] == {"seats": 4, "paid": 4, "held": 0, "turned_up": 4}


async def test_a_stranger_gets_a_404(client, session_factory) -> None:
    people, match = await _four_who_played(client, session_factory)
    _, outsider = await _join(client, ERIN)

    answer = await client.get(_url(match), headers=outsider)

    assert answer.status_code == 404


async def test_a_leaver_s_screen_opens_and_offers_nothing(
    client, session_factory
) -> None:
    """*"A 404 tells them their match never existed, which is exactly the class
    of defect ADR-0030 was written against."*"""

    people = [await _join(client, who) for who in (ALICE, BOB, CAROL, DAVE)]
    club = await _write_club(session_factory)
    alice = people[0][0]
    match = await _played_match(
        session_factory,
        club,
        seated=tuple(who for who, _ in people),
        left=alice,
    )

    answer = await client.get(_url(match), headers=people[0][1])

    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["may_enter"] is False
    assert body["may_accept"] is False
    assert body["may_counter"] is False


async def test_the_hero_clock_is_named_and_the_grace_is_absent_before_a_proposal(
    client, session_factory
) -> None:
    people, match = await _four_who_played(client, session_factory)
    _, headers = people[0]

    body = (await client.get(_url(match), headers=headers)).json()

    # Two hours after the last point, so twenty-two hours of entry left.
    assert _moment(body["settlement_deadline"]) > _now()
    assert body["acceptance_grace"] is None


# --- writing: one address for a score, another for agreeing -----------------


async def test_entering_a_score_moves_the_ladder_and_names_both_sides(
    client, session_factory
) -> None:
    people, match = await _four_who_played(client, session_factory)
    _, alice = people[0]

    answer = await client.post(_url(match), headers=alice, json={"sets": SETS})

    assert answer.status_code == 200, answer.text
    screen = answer.json()["screen"]
    assert screen["situation"]["situation"] == "confirmResult"
    assert screen["result"]["proposals"] == 1
    assert screen["result"]["proposed_by"] == 0
    assert screen["result"]["agreed"] is False
    assert [side["players"] for side in screen["result"]["score"]["sides"]] == [
        ["alice", "bob"],
        ["carol", "dave"],
    ]
    assert [
        [one["first"], one["second"]] for one in screen["result"]["score"]["sets"]
    ] == SETS


async def test_the_write_hands_now_its_update_in_the_same_response(
    client, session_factory
) -> None:
    people, match = await _four_who_played(client, session_factory)
    _, alice = people[0]

    body = (
        await client.post(_url(match), headers=alice, json={"sets": SETS})
    ).json()

    assert body["update"]["update_type"] == "card"
    card = body["update"]["card"]
    assert card["match_id"] == str(match.id)
    assert card["situation"]["situation"] == "confirmResult"
    # The card names the act, and its destination is this route.
    assert card["act"] == "answerResult"


async def test_the_opponent_sees_the_score_the_other_way_round_and_may_answer(
    client, session_factory
) -> None:
    """*Sides are named by their players, hers first* — so the same stored score
    reads as two screens and never as two facts."""

    people, match = await _four_who_played(client, session_factory)
    await client.post(_url(match), headers=people[0][1], json={"sets": SETS})

    body = (await client.get(_url(match), headers=people[2][1])).json()

    assert [side["players"] for side in body["result"]["score"]["sides"]] == [
        ["carol", "dave"],
        ["alice", "bob"],
    ]
    assert [
        [one["first"], one["second"]] for one in body["result"]["score"]["sets"]
    ] == [[4, 6], [6, 7]]
    assert body["result"]["proposed_by"] == 1
    assert body["may_accept"] is True
    assert body["may_counter"] is True
    assert body["may_enter"] is False


async def test_the_grace_is_drawn_while_it_runs(client, session_factory) -> None:
    people, match = await _four_who_played(client, session_factory)
    await client.post(_url(match), headers=people[0][1], json={"sets": SETS})

    body = (await client.get(_url(match), headers=people[2][1])).json()

    assert body["acceptance_grace"] is not None
    assert _moment(body["acceptance_grace"]) < _moment(body["settlement_deadline"])


async def test_a_teammate_cannot_accept_and_sees_why_on_the_screen(
    client, session_factory
) -> None:
    people, match = await _four_who_played(client, session_factory)
    await client.post(_url(match), headers=people[0][1], json={"sets": SETS})

    body = (await client.get(_url(match), headers=people[1][1])).json()

    assert body["may_accept"] is False
    # Her side's own score, so what she has is the correction rather than the
    # counter — the freer of the two.
    assert body["may_enter"] is True
    assert body["may_counter"] is False


async def test_an_opponent_accepting_settles_it(client, session_factory) -> None:
    people, match = await _four_who_played(client, session_factory)
    await client.post(_url(match), headers=people[0][1], json={"sets": SETS})

    answer = await client.post(
        f"{_url(match)}/acceptance", headers=people[2][1], json={}
    )

    assert answer.status_code == 200, answer.text
    screen = answer.json()["screen"]
    assert screen["situation"]["situation"] == "completed"
    assert screen["result"]["agreed"] is True
    assert screen["result"]["score"] is not None
    assert screen["may_enter"] is False
    assert screen["may_accept"] is False
    assert screen["may_counter"] is False
    assert screen["settlement_deadline"] is None
    assert screen["acceptance_grace"] is None


async def test_a_settled_card_prints_the_score_and_no_level_movement(
    client, session_factory
) -> None:
    """*The app must not invent a number no engine produced.*"""

    people, match = await _four_who_played(client, session_factory)
    await client.post(_url(match), headers=people[0][1], json={"sets": SETS})
    body = (
        await client.post(f"{_url(match)}/acceptance", headers=people[2][1], json={})
    ).json()

    card = body["update"]["card"]
    assert card["situation"]["facts"]["score"] is not None
    assert "level" not in card["situation"]["facts"]
    assert "rating" not in card["situation"]["facts"]


async def test_countering_is_the_second_proposal_and_carries_a_score(
    client, session_factory
) -> None:
    people, match = await _four_who_played(client, session_factory)
    await client.post(_url(match), headers=people[0][1], json={"sets": SETS})

    answer = await client.post(
        _url(match), headers=people[2][1], json={"sets": [[6, 3], [6, 4]]}
    )

    assert answer.status_code == 200, answer.text
    screen = answer.json()["screen"]
    assert screen["result"]["proposals"] == 2
    assert screen["result"]["proposed_by"] == 0
    assert screen["may_counter"] is False


async def test_a_stale_accept_comes_back_as_the_counter_s_situation(
    client, session_factory
) -> None:
    """ADR-0074's own named case, end to end: alice's screen still offers accept
    when her own side has countered, and her tap answers with the table as it now
    stands and no way to agree with it."""

    people, match = await _four_who_played(client, session_factory)
    await client.post(_url(match), headers=people[2][1], json={"sets": SETS})
    # Her partner counters while her screen is open.
    await client.post(_url(match), headers=people[1][1], json={"sets": [[6, 3]]})

    answer = await client.post(
        f"{_url(match)}/acceptance", headers=people[0][1], json={}
    )

    assert answer.status_code == 200, answer.text
    screen = answer.json()["screen"]
    assert screen["situation"]["situation"] == "confirmResult"
    assert screen["may_accept"] is False
    assert screen["result"]["proposals"] == 2


async def test_a_bare_rejection_has_no_shape_to_be_sent_in(
    client, session_factory
) -> None:
    """ADR-0048 forbids one, and the way it is refused is by having nowhere to
    say it: the score field is required, so a body without one is not a
    rejection, it is a malformed proposal."""

    people, match = await _four_who_played(client, session_factory)
    await client.post(_url(match), headers=people[0][1], json={"sets": SETS})

    answer = await client.post(_url(match), headers=people[2][1], json={})

    assert answer.status_code == 422


async def test_a_negative_games_count_is_turned_away_at_the_door(
    client, session_factory
) -> None:
    """The **shape** is the wire's to refuse and the rulebook is the server's.

    A negative is not a number any pad can produce, and it is bounded here
    rather than left to the domain type: `SetScore` *raises* on one, and a
    raise on a request body is a 500 where the player deserves a 422.
    """

    people, match = await _four_who_played(client, session_factory)

    answer = await client.post(
        _url(match), headers=people[0][1], json={"sets": [[-1, 6]]}
    )

    assert answer.status_code == 422


async def test_a_score_no_format_could_produce_is_declined(
    client, session_factory
) -> None:
    people, match = await _four_who_played(client, session_factory)

    answer = await client.post(
        _url(match), headers=people[0][1], json={"sets": [[0, 0]]}
    )

    assert answer.status_code == 400
    assert answer.json()["code"] == "match_impossible_score"


async def test_a_real_seven_six_is_never_called_illegal(
    client, session_factory
) -> None:
    people, match = await _four_who_played(client, session_factory)

    answer = await client.post(
        _url(match), headers=people[0][1], json={"sets": [[7, 6]]}
    )

    assert answer.status_code == 200, answer.text


async def test_a_stranger_cannot_write_either(client, session_factory) -> None:
    people, match = await _four_who_played(client, session_factory)
    _, outsider = await _join(client, ERIN)

    answer = await client.post(_url(match), headers=outsider, json={"sets": SETS})

    assert answer.status_code == 404


async def test_there_is_no_general_match_resource(client, session_factory) -> None:
    """*It would author the match-detail screen's contract inside a ticket that
    is not about it.*"""

    people, match = await _four_who_played(client, session_factory)
    _, headers = people[0]

    answer = await client.get(f"/api/v1/matches/{match.id}", headers=headers)

    assert answer.status_code == 404

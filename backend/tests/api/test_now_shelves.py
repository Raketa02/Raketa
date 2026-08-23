"""Shelves 4 and 5 over HTTP: who arrived, and where you could go and play.

The unit suite asserts the ordering, the caps and the cache against stubs. What
this file adds is the half a stub cannot reach — that *new on Raketa* really does
mean a `users` row's creation stamp with a rating stream behind it, that *new
club* really does mean a live court in a live category, and that the Level on a
person card is the one the real questionnaire produced, with the real status
behind its quiet marker.

The clubs are written through the real repository rather than through a route,
because there is no club-facing endpoint to write one with (`app/api/v1/club.py`
carries none yet). The `client` fixture overrides `get_db` with the same factory,
so a club written here is a club the request sees.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.kernel import Cover, Sport, zloty
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
from app.infrastructure.clock import SystemClock

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
CLARA = {
    "email": "clara@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "nickname": "clara",
}

ADDRESS = StreetAddress(line="ul. Zabłocie 25", city="Kraków", postal_code="30-701")
POINT = GeoPoint(latitude=Decimal("50.048100"), longitude=Decimal("19.958500"))
PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
)


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


async def _rate_as_beginner(client, headers, sport: str) -> None:
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


async def _write_club(session_factory, *, name: str, sport: Sport, courts: int = 1):
    """A club with one category and `courts` live courts, through the real store."""

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
        name=CategoryName(f"{sport.value} · hall"),
        sport=sport,
        cover=Cover.INDOOR,
        rate=zloty(80),
    )
    for index in range(courts):
        club.add_court(
            court_id=uuid4(),
            category_id=category.id,
            label=CourtLabel(f"Court {index + 1}"),
            at=SystemClock().now(),
        )
    async with session_factory() as session:
        await SqlAlchemyClubRepository(session).add(club)
        await session.commit()
    return club


def _shelf(body, code: str):
    # Narrowed on the block type rather than on the code alone: the list may also
    # hold a door, which carries a `code` of its own.
    for block in body["shelves"]["shelves"]:
        if block["block_type"] == "shelf" and block["code"] == code:
            return block
    return None


# -- new on Raketa -----------------------------------------------------------


async def test_a_player_who_just_joined_appears_on_new_on_raketa(client) -> None:
    _, alice = await _join(client, ALICE)
    bob_id, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice, "PADEL")
    await _rate_as_beginner(client, bob, "PADEL")

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    shelf = _shelf(body, "newPlayers")

    assert shelf is not None
    assert [card["nickname"] for card in shelf["cards"]] == ["bob"]
    assert shelf["cards"][0]["player_id"] == bob_id
    assert shelf["cards"][0]["card_type"] == "person"


async def test_the_viewer_is_never_introduced_to_herself(client) -> None:
    alice_id, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice, "PADEL")

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    assert _shelf(body, "newPlayers") is None
    ids = [
        card.get("player_id")
        for shelf in body["shelves"]["shelves"]
        for card in shelf["cards"]
    ]
    assert alice_id not in ids


async def test_a_person_card_carries_the_level_the_questionnaire_produced(
    client,
) -> None:
    _, alice = await _join(client, ALICE)
    _, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice, "PADEL")
    await _rate_as_beginner(client, bob, "PADEL")

    held = (await client.get("/api/v1/ratings", headers=bob)).json()["ratings"]
    padel = next(one for one in held if one["sport"] == "PADEL")
    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    card = _shelf(body, "newPlayers")["cards"][0]

    assert card["level"]["value"] == pytest.approx(padel["mu"])
    # Questionnaire-derived, so the quiet marker is on — and there is no second
    # number beside it: Confidence as a printed percentage on a card is the gauge
    # ADR-0037 refused.
    assert card["level"]["provisional"] is True
    assert set(card["level"]) == {"value", "provisional"}
    assert "confidence" not in card


async def test_a_player_rated_at_another_sport_is_not_on_this_sports_shelf(
    client,
) -> None:
    # The rating is a **fact filter**: a badminton-only player has no Level at
    # squash, so putting her on a squash shelf would print an imputed number.
    _, alice = await _join(client, ALICE)
    _, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice, "PADEL")
    await _rate_as_beginner(client, bob, "BADMINTON")

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    assert _shelf(body, "newPlayers") is None


async def test_an_unrated_sport_still_composes_the_two_light_shelves(client) -> None:
    # The door case (#78): she taps squash, holds no squash rating, and these two
    # shelves compose anyway — so she can see there are squash players and squash
    # clubs here before spending two minutes on a questionnaire.
    _, alice = await _join(client, ALICE)
    _, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice, "PADEL")
    await _rate_as_beginner(client, bob, "SQUASH")

    body = (await client.get("/api/v1/now?sport=SQUASH", headers=alice)).json()
    shelf = _shelf(body, "newPlayers")

    assert shelf is not None
    assert [card["nickname"] for card in shelf["cards"]] == ["bob"]


# -- new clubs ---------------------------------------------------------------


async def test_a_club_that_just_registered_appears_on_new_clubs(
    client, session_factory
) -> None:
    club = await _write_club(session_factory, name="Zabłocie Padel", sport=Sport.PADEL)
    _, alice = await _join(client, ALICE)

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    shelf = _shelf(body, "newClubs")

    assert shelf is not None
    assert [card["name"] for card in shelf["cards"]] == ["Zabłocie Padel"]
    assert shelf["cards"][0]["club_id"] == str(club.id)
    assert shelf["cards"][0]["card_type"] == "club"
    # No anchor, so no distance — a fact about what the platform knows, never a
    # zero (ADR-0063).
    assert shelf["cards"][0]["distance_km"] is None


async def test_a_padel_chip_never_surfaces_a_squash_only_club(
    client, session_factory
) -> None:
    await _write_club(session_factory, name="Squash Only", sport=Sport.SQUASH)
    await _write_club(session_factory, name="Zabłocie Padel", sport=Sport.PADEL)
    _, alice = await _join(client, ALICE)

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    assert [card["name"] for card in _shelf(body, "newClubs")["cards"]] == [
        "Zabłocie Padel"
    ]


async def test_new_clubs_is_capped_at_six(client, session_factory) -> None:
    for index in range(8):
        await _write_club(session_factory, name=f"Club {index}", sport=Sport.PADEL)
    _, alice = await _join(client, ALICE)

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    assert len(_shelf(body, "newClubs")["cards"]) == 6


async def test_new_clubs_composes_for_a_player_holding_no_rating_at_all(
    client, session_factory
) -> None:
    # `all` resolves to the sports she is rated at, which for a brand-new account
    # is none — so the honest answer is no shelves at all rather than a shelf of
    # squash clubs she has no way to judge.
    await _write_club(session_factory, name="Zabłocie Padel", sport=Sport.PADEL)
    _, alice = await _join(client, ALICE)

    under_all = (await client.get("/api/v1/now", headers=alice)).json()
    under_padel = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    assert under_all["shelves"]["shelves"] == []
    assert _shelf(under_padel, "newClubs") is not None


# -- the shape of the region -------------------------------------------------


async def test_a_shelf_with_nothing_in_it_is_absent_and_the_region_is_not(
    client,
) -> None:
    _, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice, "TENNIS")

    body = (await client.get("/api/v1/now?sport=TENNIS", headers=alice)).json()

    assert body["shelves"]["shelves"] == []
    assert "stamp" in body["shelves"]


async def test_new_players_is_composed_before_new_clubs(
    client, session_factory
) -> None:
    await _write_club(session_factory, name="Zabłocie Padel", sport=Sport.PADEL)
    _, alice = await _join(client, ALICE)
    _, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice, "PADEL")
    await _rate_as_beginner(client, bob, "PADEL")

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    assert [shelf["code"] for shelf in body["shelves"]["shelves"]] == [
        "newPlayers",
        "newClubs",
    ]


async def test_the_door_sits_above_the_two_light_shelves(
    client, session_factory
) -> None:
    """The whole of #78's composition, over HTTP and against real stores.

    She taps squash and holds no squash rating: the door takes the position the
    ranked shelves would occupy, and *New on Raketa* and *New clubs* compose
    beneath it — which is the argument for spending the two minutes, so it
    belongs under the ask rather than instead of it.
    """

    await _write_club(session_factory, name="Kazimierz Squash", sport=Sport.SQUASH)
    _, alice = await _join(client, ALICE)
    _, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice, "PADEL")
    await _rate_as_beginner(client, bob, "SQUASH")

    body = (await client.get("/api/v1/now?sport=SQUASH", headers=alice)).json()
    blocks = body["shelves"]["shelves"]

    assert [block["block_type"] for block in blocks] == ["door", "shelf", "shelf"]
    assert blocks[0]["code"] == "noRunYet"
    assert [block["code"] for block in blocks[1:]] == ["newPlayers", "newClubs"]


async def test_no_shelf_carries_a_title_or_a_tail_card(client, session_factory) -> None:
    await _write_club(session_factory, name="Zabłocie Padel", sport=Sport.PADEL)
    _, alice = await _join(client, ALICE)

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    shelf = _shelf(body, "newClubs")

    assert set(shelf) == {"block_type", "code", "caption", "cards"}
    assert shelf["block_type"] == "shelf"
    assert shelf["caption"] is None


async def test_every_card_on_a_shelf_carries_the_composes_stamp(
    client, session_factory
) -> None:
    await _write_club(session_factory, name="Zabłocie Padel", sport=Sport.PADEL)
    _, alice = await _join(client, ALICE)
    _, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice, "PADEL")
    await _rate_as_beginner(client, bob, "PADEL")

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    stamps = {
        card["stamp"] for shelf in body["shelves"]["shelves"] for card in shelf["cards"]
    }

    assert stamps == {body["shelves"]["stamp"]}


# -- the cache ---------------------------------------------------------------


async def test_a_club_that_registers_after_a_compose_waits_for_the_ttl(
    client, session_factory
) -> None:
    """The one visible cost of a cache with no invalidation path, asserted.

    Fifteen minutes of lag against a shelf whose own clock is sixty **days** is
    lag nobody can perceive, and it is what buys the right to have no
    invalidation at all (ADR-0068). It is asserted rather than left implicit
    because a session that added a `forget` would make this test go green while
    quietly taking on the second thing to keep in step with the truth.
    """

    await _write_club(session_factory, name="First", sport=Sport.PADEL)
    _, alice = await _join(client, ALICE)
    first = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    await _write_club(session_factory, name="Second", sport=Sport.PADEL)
    second = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    assert [card["name"] for card in _shelf(first, "newClubs")["cards"]] == ["First"]
    assert [card["name"] for card in _shelf(second, "newClubs")["cards"]] == ["First"]


async def test_a_renamed_club_reaches_the_next_screen_without_waiting(
    client, session_factory
) -> None:
    # The row is never cached, only the set. Fifteen minutes of a renamed club is
    # fifteen minutes of a player being told about a venue that no longer goes by
    # that name.
    club = await _write_club(session_factory, name="Before", sport=Sport.PADEL)
    _, alice = await _join(client, ALICE)
    await client.get("/api/v1/now?sport=PADEL", headers=alice)

    async with session_factory() as session:
        clubs = SqlAlchemyClubRepository(session)
        stored = await clubs.get(club.id)
        assert stored is not None
        stored.rename(ClubName("After"))
        await clubs.save(stored)
        await session.commit()

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    assert [card["name"] for card in _shelf(body, "newClubs")["cards"]] == ["After"]


async def test_two_players_in_one_city_share_the_set_and_not_the_screen(
    client, session_factory
) -> None:
    await _write_club(session_factory, name="Zabłocie Padel", sport=Sport.PADEL)
    _, alice = await _join(client, ALICE)
    _, bob = await _join(client, BOB)
    _, clara = await _join(client, CLARA)
    for headers in (alice, bob, clara):
        await _rate_as_beginner(client, headers, "PADEL")

    mine = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    theirs = (await client.get("/api/v1/now?sport=PADEL", headers=bob)).json()

    assert [card["name"] for card in _shelf(mine, "newClubs")["cards"]] == [
        "Zabłocie Padel"
    ]
    assert {card["nickname"] for card in _shelf(mine, "newPlayers")["cards"]} == {
        "bob",
        "clara",
    }
    assert {card["nickname"] for card in _shelf(theirs, "newPlayers")["cards"]} == {
        "alice",
        "clara",
    }


# -- the door, against these two shelves -------------------------------------
#
# That a door crosses at all, and which sentence it carries, is asserted in
# `test_now.py` beside the rest of the envelope. What belongs here is the half
# that needs this file's clubs and players: where the door sits *relative to
# these two shelves*, and that a run parked at one sport does not answer for
# another.


async def _start_a_run(client, headers, sport: str) -> None:
    """A run begun and left unfinished — the parked run the door reopens."""

    started = await client.post(
        "/api/v1/assessments", json={"sport": sport}, headers=headers
    )
    assert started.status_code in (200, 201), started.text


def _door(body):
    for block in body["shelves"]["shelves"]:
        if block["block_type"] == "door":
            return block
    return None


async def test_the_door_stands_above_the_two_light_shelves_on_the_wire(
    client, session_factory
) -> None:
    # ADR-0084: the clubs are the argument for spending the two minutes, so they
    # belong under the ask. Asserted with both shelves genuinely full, which is
    # the only arrangement in which *beneath* means anything.
    await _write_club(session_factory, name="Zabłocie Squash", sport=Sport.SQUASH)
    _, alice = await _join(client, ALICE)
    _, bob = await _join(client, BOB)
    await _rate_as_beginner(client, alice, "PADEL")
    await _rate_as_beginner(client, bob, "SQUASH")

    body = (await client.get("/api/v1/now?sport=SQUASH", headers=alice)).json()
    blocks = body["shelves"]["shelves"]

    assert [block["block_type"] for block in blocks] == ["door", "shelf", "shelf"]
    assert [block["code"] for block in blocks] == [
        "noRunYet",
        "newPlayers",
        "newClubs",
    ]


async def test_a_run_parked_at_another_sport_does_not_answer_for_this_one(
    client,
) -> None:
    # The adapter asks by pair. A tennis run half-answered on a tram says nothing
    # about squash, and reading it as though it did would offer her *pick up where
    # you left off* into a questionnaire she has never opened.
    _, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice, "PADEL")
    await _start_a_run(client, alice, "TENNIS")

    body = (await client.get("/api/v1/now?sport=SQUASH", headers=alice)).json()

    assert _door(body) == {"block_type": "door", "code": "noRunYet"}

"""Leaving and rescues in the games test console (#593; ``docs/adr/0194`` §3,
§4).

A person's row gains *Leave the game*, and *Take the seat* and *No* on a
rescue — each the use case their own button runs, so each is held to the
player's route over the same cases, **refusals included**. And two situations
that set the stage for them: *Kuba leaves before the cut-off* (6), a seat
offered to the group's best fits, her among them; and *Ania leaves* (8), two of
her own games to leave from the phone — one before its cut-off and one after.

Every claim is read where somebody would read it: Home, *Fill in* and the deck
through the player surface; for the money only a job moves, the console's own
state pane, which reads the record.

The world is ``console_world.SeedWorld``: Bonarka Arena, Instant, a 24-hour
cut-off and two hours' notice, and nine members the seed could have made. The
clock stands on **Monday 5 October 2026, 08:00 in Kraków**.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest

from app.api.dependencies import get_clock
from tests.api import players_world as players
from tests.api.console_world import (
    CONSOLE,
    PLAYER,
    SeedWorld,
    a_seed_world,
    at,
    board_of,
    code_of,
    deck_of,
    her_situation,
    home_of,
    pane_of,
    presses,
    rows_of,
)
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_player,
    makes,
    says_yes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock


@pytest.fixture
def clock(app, payments):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    payments.clock = fixed
    return fixed


@pytest.fixture
async def world(client, session_factory, payments, clock) -> SeedWorld:
    return await a_seed_world(client, session_factory, payments)


async def a_booked_game(client, session_factory, clock, world: SeedWorld) -> str:
    """Her game with the three on Saturday at 17:00 — the three's yeses, then
    hers, which books it. Its booking's id."""

    game = await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=world.club,
        versions=(world.four,),
    )
    for member in (*world.three, world.marta):
        said = await says_yes(client, member, game)
        assert said.status_code == 200, said.text
    booked = said.json()["booked"]
    assert booked is not None, said.text
    return booked["booking_id"]


async def leaves(client, via: str, member: dict, booking: str):
    """*Leave the game*, as ``member`` — by their own phone, or by the
    console's row, which holds no token."""

    if via == PLAYER:
        return await client.post(
            f"/api/v1/bookings/{booking}/departure", headers=member["headers"]
        )
    return await client.post(f"/dev/as/{member['id']}/bookings/{booking}/departure")


async def takes_the_seat(client, via: str, member: dict, booking: str):
    if via == PLAYER:
        return await client.post(
            f"/api/v1/bookings/{booking}/seats", headers=member["headers"]
        )
    return await client.post(f"/dev/as/{member['id']}/bookings/{booking}/seats")


async def says_no_to_the_seat(client, via: str, member: dict, booking: str):
    if via == PLAYER:
        return await client.post(
            f"/api/v1/bookings/{booking}/no", headers=member["headers"]
        )
    return await client.post(f"/dev/as/{member['id']}/bookings/{booking}/no")


async def fill_in_of(client, member: dict, world: SeedWorld) -> list[str]:
    """The bookings on their *Fill in*, as their own phone reads it."""

    read = await client.get(
        f"/api/v1/pools/{world.group}/fill-in",
        params={"sport": "PADEL"},
        headers=member["headers"],
    )
    assert read.status_code == 200, read.text
    return [row["booking_id"] for row in read.json()["seats_to_fill"]]


async def seat_open_cards(client, member: dict, world: SeedWorld) -> list[str]:
    return [
        card["proposal_id"]
        for card in await deck_of(client, member, world.group)
        if card["type"] == "SEAT_OPEN"
    ]


async def status_on_home(client, member: dict, booking: str) -> str | None:
    found = [g for g in await home_of(client, member) if g["booking_id"] == booking]
    return found[0]["status"] if found else None


def refunds_on(pane: dict) -> dict[str, dict | None]:
    return {charge["player"]["name"]: charge["refund"] for charge in pane["charges"]}


# --------------------------------------------------------------------------- #
# Leave the game
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_leaving_before_the_cut_off_opens_the_seat_alike(
    client, session_factory, payments, clock, world, via
):
    booking = await a_booked_game(client, session_factory, clock, world)
    kuba = world.named("kuba")

    left = await leaves(client, via, kuba, booking)

    assert left.status_code == 200, left.text
    assert left.json() == {"left": "BEFORE_THE_CUT_OFF"}
    # Read on the phones: hers shows the seat open, his no longer the game.
    assert await status_on_home(client, world.marta, booking) == "SEAT_OPEN"
    assert await status_on_home(client, kuba, booking) is None
    # Refunded at once, less the card fee.
    await players.deliver_the_outbox(session_factory, payments=payments)
    refund = refunds_on(pane_of(await board_of(client, world.group), booking))["kuba"]
    assert refund["withholds_fee"] is True
    assert refund["given_at"] is not None


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_leaving_a_game_with_no_seat_of_theirs_is_refused_alike(
    client, session_factory, clock, world, via
):
    booking = await a_booked_game(client, session_factory, clock, world)

    left = await leaves(client, via, world.named("tomek"), booking)

    assert left.status_code == 404, left.text
    assert code_of(left) == "booking_not_found"


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_leaving_once_the_hour_has_begun_is_refused_alike(
    client, session_factory, clock, world, via
):
    booking = await a_booked_game(client, session_factory, clock, world)
    clock.move(SATURDAY_FIVE - MONDAY_MORNING + timedelta(minutes=5))

    left = await leaves(client, via, world.named("kuba"), booking)

    assert left.status_code == 409, left.text
    assert code_of(left) == "game_has_started"
    assert await status_on_home(client, world.marta, booking) != "SEAT_OPEN"


# --------------------------------------------------------------------------- #
# Take the seat, and No, on a rescue
# --------------------------------------------------------------------------- #


async def a_rescue(client, session_factory, clock, world: SeedWorld) -> str:
    """Her game on Saturday, left by Kuba from his phone: a seat open."""

    booking = await a_booked_game(client, session_factory, clock, world)
    left = await leaves(client, PLAYER, world.named("kuba"), booking)
    assert left.status_code == 200, left.text
    return booking


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_taking_the_seat_pays_and_seats_them_alike(
    client, session_factory, clock, world, via
):
    booking = await a_rescue(client, session_factory, clock, world)
    tomek = world.named("tomek")

    taken = await takes_the_seat(client, via, tomek, booking)

    assert taken.status_code == 200, taken.text
    assert taken.json()["booked"]["booking_id"] == booking
    assert taken.json()["open_seats"] == 0
    assert await status_on_home(client, tomek, booking) == "BOOKED"
    assert await status_on_home(client, world.marta, booking) == "BOOKED"
    assert booking not in await fill_in_of(client, world.named("ola"), world)


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_taking_back_a_seat_they_left_is_refused_alike(
    client, session_factory, clock, world, via
):
    booking = await a_rescue(client, session_factory, clock, world)

    taken = await takes_the_seat(client, via, world.named("kuba"), booking)

    assert taken.status_code == 409, taken.text
    assert code_of(taken) == "rescue_not_offered"
    assert await status_on_home(client, world.marta, booking) == "SEAT_OPEN"


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_the_second_join_finds_the_seat_just_taken_alike(
    client, session_factory, clock, world, via
):
    booking = await a_rescue(client, session_factory, clock, world)
    first = await takes_the_seat(client, PLAYER, world.named("tomek"), booking)
    assert first.status_code == 200, first.text

    second = await takes_the_seat(client, via, world.named("ola"), booking)

    assert second.status_code == 409, second.text
    assert code_of(second) == "seat_just_taken"


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_no_takes_the_seat_open_card_from_their_deck_alike(
    client, session_factory, clock, world, via
):
    booking = await a_rescue(client, session_factory, clock, world)
    ola = world.named("ola")
    assert booking in await seat_open_cards(client, ola, world)

    said = await says_no_to_the_seat(client, via, ola, booking)

    assert said.status_code == 204, said.text
    assert booking not in await seat_open_cards(client, ola, world)
    # Still on their Fill in, which lists every rescue they fit.
    assert booking in await fill_in_of(client, ola, world)


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_no_from_somebody_on_the_game_is_refused_alike(
    client, session_factory, clock, world, via
):
    booking = await a_rescue(client, session_factory, clock, world)

    said = await says_no_to_the_seat(client, via, world.named("zofia"), booking)

    assert said.status_code == 404, said.text
    assert code_of(said) == "booking_not_found"


@pytest.mark.parametrize("press", ["departure", "seats", "no"])
async def test_each_press_refuses_an_id_that_is_nobody_s(
    client, session_factory, clock, world, press
):
    booking = await a_rescue(client, session_factory, clock, world)

    pressed = await client.post(f"/dev/as/{uuid4()}/bookings/{booking}/{press}")

    assert pressed.status_code == 403, pressed.text
    assert code_of(pressed) == "not_a_seed_account"
    assert await status_on_home(client, world.marta, booking) == "SEAT_OPEN"


# --------------------------------------------------------------------------- #
# The rows show what to leave and what to take
# --------------------------------------------------------------------------- #


async def test_a_row_lists_its_booked_games_and_the_rescues_it_could_take(
    client, session_factory, clock, world
):
    booking = await a_rescue(client, session_factory, clock, world)

    rows = rows_of(await board_of(client, world.group))

    [hers] = rows["marta"]["booked"]
    assert (hers["booking_id"], hers["state"], hers["starts_at"]) == (
        booking,
        "SEAT_OPEN",
        at(SATURDAY_FIVE),
    )
    assert hers["game_id"] is not None
    assert hers["standing"] == "AWAITING_ENTRY"
    assert rows["marta"]["rescues"] == []
    # Kuba left: no seat of his, and his own seat is never offered back.
    assert rows["kuba"]["booked"] == []
    [his] = rows["kuba"]["rescues"]
    assert (his["booking_id"], his["offered"], his["dealt"]) == (booking, False, False)
    # Ola fits and is free: offered on her Fill in, and a best fit's card.
    [olas] = rows["ola"]["rescues"]
    assert (olas["offered"], olas["dealt"], olas["said_no"]) == (True, True, False)
    assert olas["open_seats"] == 1


# --------------------------------------------------------------------------- #
# Situation 6 · Kuba leaves before the cut-off
# --------------------------------------------------------------------------- #


async def test_kuba_leaves_before_the_cut_off_and_his_seat_is_offered_to_her(
    client, session_factory, payments, clock, world
):
    """The soonest hour whose cut-off is two hours off at least: Tuesday 10:00,
    whose cut-off is Monday 10:00. Four of the group — never her — booked it;
    the first of them leaves now."""

    pressed = await her_situation(client, "one-leaves-before-the-cut-off", world)

    assert pressed.status_code == 200, pressed.text
    body = pressed.json()
    assert (body["starts_at"], body["cut_off"]) == (
        at(warsaw(6, 10)),
        at(warsaw(5, 10)),
    )
    assert "fires at 10:00 · 2 h 00 min" in body["says"]
    kuba = world.named("kuba")
    assert body["left"]["player_id"] == str(kuba["id"])
    on_it = {person["player_id"] for person in body["people_in"]}
    assert len(on_it) == 3
    assert str(world.marta["id"]) not in on_it | {str(kuba["id"])}
    assert str(world.marta["id"]) in {p["player_id"] for p in body["offered_to"]}
    assert str(world.marta["id"]) in {p["player_id"] for p in body["dealt_to"]}
    booking = body["game_id"]

    # Her phone: the seat on her Fill in, and a Seat open card in her deck.
    assert booking in await fill_in_of(client, world.marta, world)
    assert booking in await seat_open_cards(client, world.marta, world)
    # Kuba refunded at once, less the card fee.
    await players.deliver_the_outbox(session_factory, payments=payments)
    assert refunds_on(pane_of(await board_of(client, world.group), booking))["kuba"][
        "withholds_fee"
    ]

    # A row takes it, and it is gone from her board.
    taker = next(
        member
        for member in world.rest
        if str(member["id"]) in {p["player_id"] for p in body["offered_to"]}
    )
    taken = await takes_the_seat(client, CONSOLE, taker, booking)
    assert taken.status_code == 200, taken.text
    assert booking not in await fill_in_of(client, world.marta, world)


async def test_kuba_leaves_says_so_when_no_four_can_book(client, clock, world):
    """Nobody in the group is rated in tennis."""

    pressed = await presses(
        client,
        "one-leaves-before-the-cut-off",
        group_id=world.group,
        sport="TENNIS",
        protagonist_id=world.marta["id"],
    )

    assert pressed.status_code == 409, pressed.text
    assert await home_of(client, world.marta) == []


# --------------------------------------------------------------------------- #
# Situation 8 · Ania leaves
# --------------------------------------------------------------------------- #


async def test_she_leaves_has_one_game_before_its_cut_off_and_one_after(
    client, session_factory, payments, clock, world
):
    """After the cut-off: the soonest hour two hours off at least — Monday
    10:00, whose cut-off was Sunday's. Before it: Tuesday 10:00, whose cut-off
    is Monday 10:00. Both hers, booked earlier."""

    pressed = await her_situation(client, "she-leaves", world)

    assert pressed.status_code == 200, pressed.text
    before, after = pressed.json()["before"], pressed.json()["after"]
    assert (after["starts_at"], after["cut_off"]) == (
        at(warsaw(5, 10)),
        at(warsaw(4, 10)),
    )
    assert (before["starts_at"], before["cut_off"]) == (
        at(warsaw(6, 10)),
        at(warsaw(5, 10)),
    )
    for game in (before, after):
        assert str(world.marta["id"]) in {p["player_id"] for p in game["people"]}
        assert await status_on_home(client, world.marta, game["game_id"]) == "BOOKED"

    # She leaves both from her phone: one refunded at once…
    left = await leaves(client, PLAYER, world.marta, before["game_id"])
    assert left.json() == {"left": "BEFORE_THE_CUT_OFF"}, left.text
    # …and one whose seat stays paid until somebody takes it.
    left = await leaves(client, PLAYER, world.marta, after["game_id"])
    assert left.json() == {"left": "AFTER_THE_CUT_OFF"}, left.text
    await players.deliver_the_outbox(session_factory, payments=payments)
    board = await board_of(client, world.group)
    assert refunds_on(pane_of(board, before["game_id"]))["marta"]["withholds_fee"]
    assert refunds_on(pane_of(board, after["game_id"]))["marta"] is None

    # A row takes her seat, and her refund lands.
    taker = next(
        member
        for member in world.rest
        if str(member["id"]) not in {p["player_id"] for p in after["people"]}
    )
    taken = await takes_the_seat(client, CONSOLE, taker, after["game_id"])
    assert taken.status_code == 200, taken.text
    await players.deliver_the_outbox(session_factory, payments=payments)
    refund = refunds_on(pane_of(await board_of(client, world.group), after["game_id"]))[
        "marta"
    ]
    assert refund["withholds_fee"] is True
    assert refund["given_at"] is not None


@pytest.mark.parametrize("situation", ["one-leaves-before-the-cut-off", "she-leaves"])
async def test_each_situation_refuses_a_protagonist_the_seed_did_not_create(
    client, payments, world, situation
):
    piotr = await a_player(client, payments, "piotr")

    pressed = await presses(
        client,
        situation,
        group_id=world.group,
        sport="PADEL",
        protagonist_id=piotr["id"],
    )

    assert pressed.status_code == 403, pressed.text
    assert code_of(pressed) == "not_a_seed_account"

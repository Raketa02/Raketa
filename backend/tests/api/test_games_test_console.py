"""The games test console over HTTP (#590; ``docs/adr/0194``).

The console acts as seed accounts **without signing in**: a press on a person's
row runs the use case that person's own button runs. So every claim here is
made the way the page makes it — a request to the dev surface, with no token —
and **read back through the player surface**, the way the protagonist's phone
reads it: her deck, her Home, a member's live yeses. A situation is proven by
what she sees, never by the rows it wrote.

The world is small and made the way the platform makes one: a club selling a
padel court every hour, and four members addressed on the seed system's
reserved TLD — the console acts only as those — plus one who is not, whom it
refuses. The clock stands on **Monday 5 October 2026, 08:00 in Kraków**.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import update

from app.api.dependencies import get_clock
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM
from app.seeds.catalog import THE_POPULATED_PLAYER
from tests.api import players_world as players
from tests.api.console_world import (
    CONSOLE,
    PLAYER,
    SEED,
    at,
    board_of,
    code_of,
    deck_ids,
    deck_of,
    ids,
    pane_of,
    presses,
    rows_of,
    says,
)
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_selling,
    a_group,
    a_member,
    live_ids,
    makes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@dataclass(frozen=True)
class World:
    club: str
    group: UUID
    #: The protagonist — the phone in the tester's hand.
    marta: dict
    kuba: dict
    zofia: dict
    marek: dict
    #: A seed account with no saved card.
    ewa: dict
    #: A member the seed did not create: the console refuses to act as her.
    piotr: dict


@pytest.fixture
async def world(client, session_factory, payments) -> World:
    club = await a_club_selling(client)
    marta, kuba, zofia, marek = [
        await a_member(client, session_factory, payments, name, domain=SEED)
        for name in ("marta", "kuba", "zofia", "marek")
    ]
    ewa = await a_member(
        client, session_factory, payments, "ewa", domain=SEED, card=False
    )
    piotr = await a_member(client, session_factory, payments, "piotr")
    group = await a_group(client, marta, club, kuba, zofia, marek, ewa, piotr)
    return World(club, group, marta, kuba, zofia, marek, ewa, piotr)


async def a_card(session_factory, clock, world: World, *named: dict) -> UUID:
    """A pick dealt as one version naming these members — Saturday 17:00."""

    return await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=world.club,
        versions=(named,),
    )


# --------------------------------------------------------------------------- #
# The page
# --------------------------------------------------------------------------- #


async def test_the_page_is_one_file_served_on_the_dev_surface(client):
    page = await client.get("/dev")

    assert page.status_code == 200, page.text
    assert page.headers["content-type"].startswith("text/html")
    assert "games test console" in page.text.lower()


@pytest.mark.parametrize(
    "what", ["localStorage", "sessionStorage", "document.cookie", "setTimeout"]
)
async def test_the_page_stores_no_token_and_nothing_acts_on_its_own(client, what):
    """ADR-0194 §6, held where it can be: the page holds no token, so it stores
    none, and nothing answers, runs or fetches unless the tester presses."""

    page = await client.get("/dev")

    assert what not in page.text


def _function(page: str, name: str) -> str:
    """A top-level function's body in the page's one script."""

    return page.split(f"function {name}(", 1)[1].split("\n}\n", 1)[0]


async def test_the_page_s_one_timer_only_redraws_the_countdowns(client):
    """ADR-0194 §6: *a countdown only redraws a number* (#592). The page's one
    timer redraws the countdowns from what was read, and the redraw fetches,
    presses and reloads nothing."""

    page = (await client.get("/dev")).text

    assert page.count("setInterval(") == 1
    assert "setInterval(redrawCountdowns, 1000)" in page
    for name in ("redrawCountdowns", "firesAt"):
        body = _function(page, name)
        for acting in ("fetch(", "call(", "load", "run", "say("):
            assert acting not in body, (name, acting)


# --------------------------------------------------------------------------- #
# A row's buttons are the person's own
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_yes_records_and_answers_as_the_player_s_own(
    client, session_factory, clock, world, via
):
    game = await a_card(
        session_factory, clock, world, world.marta, world.kuba, world.zofia
    )

    answered = await says(client, via, "yes", world.kuba, game)

    assert answered.status_code == 200, answered.text
    assert answered.json() == {
        "proposal_id": str(game),
        "open_seats": 3,
        "booked": None,
        "waiting_for_the_club": False,
        "your_payment": None,
        "payment_awaited_until": None,
    }
    assert str(game) in await live_ids(client, world.kuba)


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_yes_from_somebody_never_dealt_it_is_refused_alike(
    client, session_factory, clock, world, via
):
    game = await a_card(
        session_factory, clock, world, world.marta, world.kuba, world.zofia
    )

    answered = await says(client, via, "yes", world.marek, game)

    assert answered.status_code == 404, answered.text
    assert code_of(answered) == "proposal_not_found"
    assert str(game) not in await live_ids(client, world.marek)


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_yes_after_a_no_is_refused_alike(
    client, session_factory, clock, world, via
):
    game = await a_card(session_factory, clock, world, world.marta, world.kuba)
    said_no = await says(client, via, "no", world.kuba, game)
    assert said_no.status_code == 204, said_no.text

    answered = await says(client, via, "yes", world.kuba, game)

    assert answered.status_code == 409, answered.text
    assert code_of(answered) == "proposal_already_answered"


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_yes_with_no_saved_card_is_refused_alike(
    client, session_factory, clock, world, via
):
    game = await a_card(session_factory, clock, world, world.marta, world.ewa)

    answered = await says(client, via, "yes", world.ewa, game)

    assert answered.status_code == 409, answered.text
    assert code_of(answered) == "payment_method_required"
    assert str(game) not in await live_ids(client, world.ewa)


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_no_takes_the_card_out_of_their_deck(
    client, session_factory, clock, world, via
):
    game = await a_card(session_factory, clock, world, world.marta, world.kuba)
    assert str(game) in await deck_ids(client, world.kuba, world.group)

    said_no = await says(client, via, "no", world.kuba, game)

    assert said_no.status_code == 204, said_no.text
    assert str(game) not in await deck_ids(client, world.kuba, world.group)


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_withdrawn_yes_leaves_their_live_yeses(
    client, session_factory, clock, world, via
):
    game = await a_card(session_factory, clock, world, world.marta, world.kuba)
    said_yes = await says(client, via, "yes", world.kuba, game)
    assert said_yes.status_code == 200, said_yes.text

    withdrawn = await says(client, via, "withdraw", world.kuba, game)

    assert withdrawn.status_code == 204, withdrawn.text
    assert str(game) not in await live_ids(client, world.kuba)


@pytest.mark.parametrize("via", [PLAYER, CONSOLE])
async def test_a_yes_from_a_disabled_account_is_refused_alike(
    client, session_factory, clock, world, via
):
    """The player's route refuses an account that is no longer active before
    any use case runs — that is ``GetCurrentUser``'s, the step after the token
    — so the console must too. No route disables an account yet, so the test
    writes the flag the way the users projection holds it."""

    game = await a_card(session_factory, clock, world, world.marta, world.kuba)
    async with session_factory() as session:
        await session.execute(
            update(UserORM)
            .where(UserORM.id == world.kuba["id"])
            .values(is_active=False)
        )
        await session.commit()

    answered = await says(client, via, "yes", world.kuba, game)

    assert answered.status_code == 401, answered.text
    assert code_of(answered) == "user_not_eligible"


# --------------------------------------------------------------------------- #
# Only as seed accounts
# --------------------------------------------------------------------------- #


async def test_it_refuses_to_act_as_an_account_the_seed_did_not_create(
    client, session_factory, clock, world
):
    game = await a_card(session_factory, clock, world, world.marta, world.piotr)

    answered = await says(client, CONSOLE, "yes", world.piotr, game)

    assert answered.status_code == 403, answered.text
    assert code_of(answered) == "not_a_seed_account"
    # Nothing was recorded: her own phone still finds the card undecided.
    assert str(game) not in await live_ids(client, world.piotr)
    assert str(game) in await deck_ids(client, world.piotr, world.group)


@pytest.mark.parametrize("verb", ["yes", "no", "withdraw"])
async def test_it_refuses_an_id_that_is_nobody_s(
    client, session_factory, clock, world, verb
):
    game = await a_card(session_factory, clock, world, world.marta, world.kuba)

    answered = await says(client, CONSOLE, verb, {"id": uuid4()}, game)

    assert answered.status_code == 403, answered.text
    assert code_of(answered) == "not_a_seed_account"


# --------------------------------------------------------------------------- #
# Picking a group: a row per seeded member, with their cards
# --------------------------------------------------------------------------- #


async def test_the_groups_to_pick_are_counted_by_who_the_console_may_act_as(
    client, world
):
    read = await client.get("/dev/groups")

    assert read.status_code == 200, read.text
    [group] = [g for g in read.json()["groups"] if g["group_id"] == str(world.group)]
    assert group == {
        "group_id": str(world.group),
        "name": "Sobotni padel",
        "club_name": "Bonarka Arena",
        "seed_members": 5,
        "other_members": 1,
        "holds_the_protagonist": False,
    }
    assert "PADEL" in read.json()["sports"]


async def test_the_protagonist_is_the_seed_s_own_once_she_is_registered(client, world):
    """The seed's default protagonist, whom the page puts on the phone — absent
    from a store the seed never ran in."""

    assert (await client.get("/dev/groups")).json()["protagonist"] is None

    signed_up = await client.post(
        "/api/v1/users",
        json={
            "email": THE_POPULATED_PLAYER.email,
            "password1": "hunter22!",
            "password2": "hunter22!",
            "adult_attested": True,
        },
    )
    assert signed_up.status_code == 201, signed_up.text

    protagonist = (await client.get("/dev/groups")).json()["protagonist"]
    assert protagonist == {"player_id": signed_up.json()["id"], "name": None}

    # Once she is in the group, the page opens on it.
    signed_in = await client.post(
        "/api/v1/auth/login",
        json={"email": THE_POPULATED_PLAYER.email, "password": "hunter22!"},
    )
    headers = players.auth(signed_in.json()["access_token"])
    named = await client.put(
        "/api/v1/users/me/name",
        json={"name": "Marta Ferrer", "nickname": "marta_ferrer"},
        headers=headers,
    )
    assert named.status_code == 200, named.text
    joined = await client.post(
        f"/api/v1/groups/{world.group}/membership", headers=headers
    )
    assert joined.status_code in (200, 201), joined.text
    groups = (await client.get("/dev/groups")).json()["groups"]
    [group] = [g for g in groups if g["group_id"] == str(world.group)]
    assert group["holds_the_protagonist"] is True


async def test_a_row_per_seeded_member_with_name_photo_and_level(
    client, session_factory, clock, world
):
    board = await board_of(client, world.group)

    rows = rows_of(board)
    # Piotr is a member, and not an account the seed created: no row.
    assert set(rows) == {"marta", "kuba", "zofia", "marek", "ewa"}
    assert rows["kuba"]["player_id"] == str(world.kuba["id"])
    assert rows["kuba"]["email"] == "kuba@raketa.example"
    assert rows["kuba"]["level"] == 2.5
    assert rows["kuba"]["photo_url"] is None
    assert board["group"]["other_members"] == 1


async def test_each_row_shows_the_cards_dealt_to_them_with_who_is_in(
    client, session_factory, clock, world
):
    game = await a_card(
        session_factory, clock, world, world.marta, world.kuba, world.zofia
    )
    said = await says(client, CONSOLE, "yes", world.kuba, game)
    assert said.status_code == 200, said.text
    said = await says(client, CONSOLE, "no", world.zofia, game)
    assert said.status_code == 204, said.text

    rows = rows_of(await board_of(client, world.group))

    [kuba] = rows["kuba"]["cards"]
    assert kuba["proposal_id"] == str(game)
    assert kuba["answer"] == "IN"
    assert kuba["kind"] == "COMPETITIVE"
    assert kuba["open_seats"] == 3
    assert kuba["people_in"] == [{"player_id": str(world.kuba["id"]), "name": "kuba"}]
    assert [card["answer"] for card in rows["marta"]["cards"]] == ["DEALT"]
    assert [card["answer"] for card in rows["zofia"]["cards"]] == ["SAID_NO"]
    assert rows["marek"]["cards"] == []
    # Another sport's board deals none of it.
    tennis = await board_of(client, world.group, "TENNIS")
    assert all(not row["cards"] for row in tennis["people"])


# --------------------------------------------------------------------------- #
# Situations
# --------------------------------------------------------------------------- #


async def test_fresh_deal_runs_the_proposer_now_for_the_group(client, clock, world):
    assert await deck_of(client, world.marta, world.group) == []

    pressed = await presses(client, "fresh-deal", group_id=world.group)

    assert pressed.status_code == 200, pressed.text
    assert pressed.json()["proposed"]["made"] >= 1
    # Read as her phone reads it: the proposer dealt her cards.
    assert await deck_of(client, world.marta, world.group) != []


async def test_fresh_deal_pressed_again_deals_nothing_twice(client, clock, world):
    first = await presses(client, "fresh-deal", group_id=world.group)
    assert first.status_code == 200, first.text

    again = await presses(client, "fresh-deal", group_id=world.group)

    assert again.status_code == 200, again.text
    assert again.json()["proposed"]["made"] == 0


async def test_needs_her_yes_puts_three_in_so_her_yes_completes_it(
    client, clock, world
):
    pressed = await presses(
        client,
        "needs-her-yes-instant-club",
        group_id=world.group,
        sport="PADEL",
        protagonist_id=world.marta["id"],
    )

    assert pressed.status_code == 200, pressed.text
    game = pressed.json()["game_id"]
    # Her deck shows *You complete it* on it — and it books at once.
    [card] = [
        c
        for c in await deck_of(client, world.marta, world.group)
        if c["proposal_id"] == game
    ]
    assert card["in_count"] == 3
    assert card["open_seats_after_your_yes"] == 0
    assert card["court"] == "BOOK_IT_NOW"
    assert card["club_confirms"] is False
    # Every one of the three put In is somebody the console may act as.
    put_in = {person["player_id"] for person in pressed.json()["people_in"]}
    assert len(put_in) == 3
    assert put_in <= {str(m["id"]) for m in (world.kuba, world.zofia, world.marek)}

    # The only card the four share is soon: it is taken, and the tester is told
    # when her yes is due.
    pane = pane_of(await board_of(client, world.group), UUID(game))
    assert pressed.json()["book_by"] == pane["book_by"]
    assert "its book-by fires at" in pressed.json()["says"]

    # Her yes, from her own phone, books the game: Home shows it.
    yes = await says(client, PLAYER, "yes", world.marta, UUID(game))
    assert yes.status_code == 200, yes.text
    assert yes.json()["booked"] is not None
    home = await client.get("/api/v1/home", headers=world.marta["headers"])
    assert home.status_code == 200, home.text
    [booked] = [g for g in home.json()["games"] if g["booking_id"] == game]
    assert booked["status"] == "BOOKED"


async def test_needs_her_yes_prefers_a_card_she_has_time_to_answer(
    client, session_factory, clock, world
):
    """Two cards she could complete: one whose book-by is an hour away, and
    Saturday's. The situation leaves Saturday's needing her, so the card does
    not expire on the way to her phone."""

    four = (world.marta, world.kuba, world.zofia, world.marek)
    soon = await makes(
        session_factory,
        clock,
        pool_id=world.group,
        club_id=world.club,
        start=warsaw(5, 11),
        versions=(four,),
    )
    saturday = await a_card(session_factory, clock, world, *four)

    pressed = await presses(
        client,
        "needs-her-yes-instant-club",
        group_id=world.group,
        sport="PADEL",
        protagonist_id=world.marta["id"],
    )

    assert pressed.status_code == 200, pressed.text
    assert pressed.json()["game_id"] == str(saturday)
    board = await board_of(client, world.group)
    assert pane_of(board, soon)["people_in"] == []
    assert len(pane_of(board, saturday)["people_in"]) == 3


async def test_needs_her_yes_refuses_a_protagonist_the_seed_did_not_create(
    client, world
):
    pressed = await presses(
        client,
        "needs-her-yes-instant-club",
        group_id=world.group,
        sport="PADEL",
        protagonist_id=world.piotr["id"],
    )

    assert pressed.status_code == 403, pressed.text
    assert code_of(pressed) == "not_a_seed_account"


async def test_needs_her_yes_says_so_when_no_game_can_be_set_up(client, clock, world):
    """Nobody in the group is rated in tennis, so the proposer deals no tennis
    game at all — and the situation says it found none, rather than inventing
    one."""

    pressed = await presses(
        client,
        "needs-her-yes-instant-club",
        group_id=world.group,
        sport="TENNIS",
        protagonist_id=world.marta["id"],
    )

    assert pressed.status_code == 409, pressed.text
    assert code_of(pressed) == "situation_unavailable"
    assert await deck_of(client, world.marta, world.group) != []


async def test_a_situation_for_no_such_group_is_refused(client, world):
    pressed = await presses(client, "fresh-deal", group_id=uuid4())

    assert pressed.status_code == 404, pressed.text
    assert code_of(pressed) == "group_not_found"


# --------------------------------------------------------------------------- #
# The state pane
# --------------------------------------------------------------------------- #


async def test_the_pane_of_a_game_still_filling(client, session_factory, clock, world):
    game = await a_card(
        session_factory, clock, world, world.marta, world.kuba, world.zofia
    )
    said = await says(client, CONSOLE, "yes", world.kuba, game)
    assert said.status_code == 200, said.text

    pane = pane_of(await board_of(client, world.group), game)

    assert pane["standing"] == "FILLING"
    assert pane["origin"] == "PICK"
    assert pane["kind"] == "COMPETITIVE"
    assert pane["club"] == {
        "club_id": world.club,
        "name": "Bonarka Arena",
        "confirms_each_game": False,
    }
    # The court hour, Saturday 17:00; its book-by; the club's cut-off — 24 h
    # before, as the club's settings stand.
    assert pane["starts_at"] == at(SATURDAY_FIVE)
    assert pane["cut_off"] == at(SATURDAY_FIVE - timedelta(hours=24))
    assert pane["book_by"] is not None
    assert pane["share_grosze"] == 30_00
    assert pane["open_seats"] == 3
    assert pane["people_in"] == [{"player_id": str(world.kuba["id"]), "name": "kuba"}]
    [version] = pane["versions"]
    assert {(p["name"], p["answer"]) for p in version["people"]} == {
        ("marta", "DEALT"),
        ("kuba", "IN"),
        ("zofia", "DEALT"),
    }
    # The sides as the people In stand on it.
    assert ids(pane["sides"]["first"]) | ids(pane["sides"]["second"]) == {
        str(world.kuba["id"])
    }
    assert pane["booking"] is None
    assert pane["charges"] == []


async def test_the_pane_of_a_booked_game_shows_its_court_sides_and_every_charge(
    client, session_factory, payments, clock, world
):
    four = (world.marta, world.kuba, world.zofia, world.marek)
    game = await a_card(session_factory, clock, world, *four)
    for member in four[1:]:
        said = await says(client, CONSOLE, "yes", member, game)
        assert said.status_code == 200, said.text
    booked = await says(client, PLAYER, "yes", world.marta, game)
    assert booked.json()["booked"] is not None, booked.text
    await players.deliver_the_outbox(session_factory, payments=payments)

    pane = pane_of(await board_of(client, world.group), game)

    assert pane["standing"] == "FILLED"
    assert ids(pane["people_in"]) == {str(m["id"]) for m in four}
    booking = pane["booking"]
    assert booking["state"] == "BOOKED"
    assert booking["court_name"] == "Court 1"
    assert booking["called_off"] is None
    assert booking["departures"] == []
    assert pane["cut_off"] == at(SATURDAY_FIVE - timedelta(hours=24))
    first, second = pane["sides"]["first"], pane["sides"]["second"]
    assert len(first) == len(second) == 2
    assert ids(first) | ids(second) == {str(m["id"]) for m in four}
    charges = pane["charges"]
    assert {charge["player"]["player_id"] for charge in charges} == {
        str(m["id"]) for m in four
    }
    # Held for the game until its cut-off, which takes them (#637).
    assert {
        (c["amount_grosze"], c["status"], c["held_until"], c["refund"])
        for c in charges
    } == {(30_00, "HELD", at(SATURDAY_FIVE - timedelta(hours=24)), None)}


async def test_the_pane_shows_a_hold_let_go_once_somebody_leaves(
    client, session_factory, payments, clock, world
):
    four = (world.marta, world.kuba, world.zofia, world.marek)
    game = await a_card(session_factory, clock, world, *four)
    for member in four[1:]:
        await says(client, CONSOLE, "yes", member, game)
    await says(client, PLAYER, "yes", world.marta, game)
    await players.deliver_the_outbox(session_factory, payments=payments)

    # Kuba leaves from his own phone, before the cut-off: his hold is let go,
    # nothing taken and nothing refunded (#637).
    left = await client.post(
        f"/api/v1/bookings/{game}/departure", headers=world.kuba["headers"]
    )
    assert left.status_code == 200, left.text
    await players.deliver_the_outbox(session_factory, payments=payments)

    pane = pane_of(await board_of(client, world.group), game)

    assert pane["booking"]["state"] == "SEAT_OPEN"
    [departure] = pane["booking"]["departures"]
    assert departure["player"]["player_id"] == str(world.kuba["id"])
    assert departure["rescued_by"] is None
    charges = {charge["player"]["name"]: charge for charge in pane["charges"]}
    assert (charges["kuba"]["status"], charges["kuba"]["refund"]) == ("CANCELLED", None)
    assert (charges["marta"]["status"], charges["marta"]["refund"]) == ("HELD", None)

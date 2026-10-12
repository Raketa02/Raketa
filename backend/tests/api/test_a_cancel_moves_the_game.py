"""**A club's cancel moves the game when a free court of the same club absorbs
it** (#672; the mechanics §16.9, Q122; ``docs/adr/0196`` §2).

A court absorbs the cancel when it is at the same club, for the same sport, on
the same day and at the same hour, sold at the same price, of the same kind or
indoor for an outdoor game — and indoor for *weather*. Of two, the same kind
comes first, then indoor; within that, the club's court order. **Then the game
moves there and nothing else happens**: every hold or taken share stays as it
is, nobody is refunded, let go or owed a card, and all four are told *Game
moved* with why the court they left can't be played. **With *anyway*, or with
no absorbing court**, the cancel calls the game off as it always did. **The
preview** says what a cancel with a reason would do now, and **the cancel
decides afresh** when the club confirms.

Every act is taken over HTTP as the club website and the phone take it, against
the fake payment provider; every claim is read where somebody would read it.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena on Court 1, padel at 120 zł —
30 zł a seat — with a 24-hour cut-off. Court 3 is indoor like Court 1, and
Court 4 is outdoor.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_proposal_directory
from tests.api.club_courts_world import (
    adds_a_court,
    court_path,
    sets_hours,
    sets_prices,
)
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_player,
    every_hour_of_the_week,
    makes,
    says_yes,
    the_cut_off_comes,
)
from tests.unit.fake_clock import MovableClock

BOOKINGS = "/api/v1/club/bookings"
HOME = "/api/v1/home"
NOTICES = "/api/v1/players/me/notices"
RECEIPTS = "/api/v1/players/me/receipts"
SHARE = 30_00
SATURDAY = "2026-10-10"


@pytest.fixture
def clock(app):
    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> tuple[str, dict]:
    """Bonarka Arena — Court 1, and two more padel courts: Court 3, indoor like
    it, and Court 4, outdoor."""

    club_id, desk = await a_club_and_its_desk(client)
    court_1 = await court_named(client, desk, "Court 1")
    court_3 = await adds_a_court(client, desk, name="Court 3", sport="PADEL")
    court_4 = await adds_a_court(
        client, desk, name="Court 4", sport="PADEL", indoor=False
    )
    await sets_hours(
        client,
        desk,
        [court_1["id"], court_3["id"], court_4["id"]],
        every_hour_of_the_week(),
    )
    return club_id, desk


@pytest.fixture
async def four(client, payments) -> list[dict]:
    return [
        {**await a_player(client, payments, name), "name": name}
        for name in ("ola", "kuba", "ewa", "tomek")
    ]


@pytest.fixture
async def group(client, club, four) -> UUID:
    return await a_group(client, four[0], club[0], *four[1:])


@pytest.fixture
async def booking(client, session_factory, clock, club, group, four, mailbox) -> str:
    """The four's game on Saturday at 17:00 on Court 1, indoor — every share
    held until the cut-off."""

    booked = await books(client, session_factory, clock, club[0], group, four)
    await mailbox.drain()
    return booked


async def books(client, session_factory, clock, club_id, group, four) -> str:
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club_id, versions=(tuple(four),)
    )
    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    return last.json()["booked"]["booking_id"]


async def court_named(client, desk: dict, name: str) -> dict:
    courts = (await client.get("/api/v1/club/courts", headers=desk)).json()["courts"]
    return next(one for one in courts if one["name"] == name)


async def changes_a_court(
    client, desk: dict, name: str, *, indoor: bool = True, offered: bool = True
) -> None:
    court = await court_named(client, desk, name)
    changed = await client.put(
        court_path(court["id"]),
        json={"name": name, "sport": "PADEL", "indoor": indoor, "offered": offered},
        headers=desk,
    )
    assert changed.status_code == 200, changed.text


async def preview(client, desk: dict, booking_id: str, reason: str) -> dict:
    read = await client.get(
        f"{BOOKINGS}/{booking_id}/cancellation/preview",
        params={"reason": reason},
        headers=desk,
    )
    assert read.status_code == 200, read.text
    return read.json()


async def cancels(
    client, desk: dict, booking_id: str, reason: str, *, anyway: bool = False
) -> dict:
    cancelled = await client.post(
        f"{BOOKINGS}/{booking_id}/cancellation",
        json={"reason": reason, "anyway": anyway},
        headers=desk,
    )
    assert cancelled.status_code == 200, cancelled.text
    return cancelled.json()


def moved_to(answer: dict) -> tuple[str, str, bool]:
    assert answer["court"] is not None, answer
    return answer["outcome"], answer["court"]["name"], answer["court"]["indoor"]


CALLED_OFF = {"outcome": "CALLED_OFF", "court": None}


async def home_card(client, player: dict) -> dict:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    [card] = read.json()["games"]
    return card


async def newest_notice(client, mailbox, player: dict) -> dict:
    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["notices"][0]


async def receipt_kinds(client, mailbox, player: dict) -> list[str]:
    await mailbox.drain()
    read = await client.get(RECEIPTS, headers=player["headers"])
    assert read.status_code == 200, read.text
    return [receipt["kind"] for receipt in read.json()["receipts"]]


async def the_desk_s_row(client, desk: dict, booking_id: str) -> dict:
    read = await client.get(
        BOOKINGS, params={"date": SATURDAY, "filter": "ALL"}, headers=desk
    )
    assert read.status_code == 200, read.text
    return next(
        row for row in read.json()["bookings"] if row["booking_id"] == booking_id
    )


async def owed_in(session_factory, clock, group: UUID) -> list[str]:
    async with session_factory() as session:
        owed = await build_proposal_directory(session).owed_a_new_card_in(
            group, now=clock.now()
        )
    return [str(one) for one in owed]


def calls(payments, name: str) -> int:
    return len(payments.called(name))


async def another_four_book_the_hour(
    client, session_factory, clock, payments, club_id: str
) -> str:
    """Four more players book a game at Bonarka at the same hour — on the
    first court still free there."""

    others = [
        await a_player(client, payments, name)
        for name in ("zosia", "marek", "iga", "piotr")
    ]
    group = await a_group(client, others[0], club_id, *others[1:])
    return await books(client, session_factory, clock, club_id, group, others)


# --------------------------------------------------------------------------- #
# A free court absorbs the cancel
# --------------------------------------------------------------------------- #


async def test_a_repair_cancel_moves_the_game_to_a_free_court_and_changes_nothing_else(
    client, session_factory, clock, club, group, booking, four, payments, mailbox
):
    """The lights on Court 1 fail and the desk cancels for *repair*: Court 3 is
    free at 17:00, indoor like Court 1, at the same 120 zł. The game is on
    Court 3, the four holds are untouched, and all four are told."""

    _, desk = club

    previewed = await preview(client, desk, booking, "REPAIR")
    answer = await cancels(client, desk, booking, "REPAIR")

    assert moved_to(previewed) == ("MOVED", "Court 3", True)
    assert moved_to(answer) == ("MOVED", "Court 3", True)
    assert answer["court"] == previewed["court"]
    await mailbox.drain()
    # Nothing let go, nothing refunded.
    assert (calls(payments, "cancel"), calls(payments, "refund")) == (0, 0)
    for player in four:
        card = await home_card(client, player)
        assert (card["status"], card["court_name"], card["indoor"]) == (
            "BOOKED",
            "Court 3",
            True,
        )
        assert card["called_off_reason"] is None
        notice = await newest_notice(client, mailbox, player)
        assert (notice["kind"], notice["opens"], notice["game_id"]) == (
            "GAME_MOVED",
            "BOOKING",
            booking,
        )
        assert (notice["title"], notice["body"]) == (
            "Bonarka Arena moved your game to Court 3 · Sat 17:00",
            "Court 1 can't be played · Padel · indoor · nothing else changes",
        )
        assert not {"RELEASED", "REFUND"} & set(
            await receipt_kinds(client, mailbox, player)
        )
        emails = await mailbox.to(f"{player['name']}@example.com")
        assert all("cancelled" not in email.subject.lower() for email in emails)
    row = await the_desk_s_row(client, desk, booking)
    assert (row["status"], row["court_name"], row["indoor"]) == (
        "BOOKED",
        "Court 3",
        True,
    )
    assert all((p["paid"], p["held"]) == (False, True) for p in row["players"])
    assert row["money"]["refunded_grosze"] == 0
    # Nobody is owed a card: the game was never called off.
    assert await owed_in(session_factory, clock, group) == []


async def test_weather_moves_an_outdoor_game_to_the_free_indoor_court(
    client, session_factory, clock, club, group, four, mailbox
):
    """Court 1 is outdoor: *repair* would take Court 4, the same kind first, but
    an outdoor court at the same hour is rained on too — *weather* takes Court
    3, indoor."""

    club_id, desk = club
    await changes_a_court(client, desk, "Court 1", indoor=False)
    booking = await books(client, session_factory, clock, club_id, group, four)
    # Told *It's a game!* first, at the same instant the clock stands on.
    await mailbox.drain()

    assert moved_to(await preview(client, desk, booking, "REPAIR")) == (
        "MOVED",
        "Court 4",
        False,
    )
    answer = await cancels(client, desk, booking, "WEATHER")

    assert moved_to(answer) == ("MOVED", "Court 3", True)
    card = await home_card(client, four[0])
    assert (card["status"], card["court_name"], card["indoor"]) == (
        "BOOKED",
        "Court 3",
        True,
    )
    notice = await newest_notice(client, mailbox, four[0])
    assert notice["body"] == (
        "Court 1 can't be played in this weather · Padel · indoor · nothing else "
        "changes"
    )


async def test_weather_never_moves_an_outdoor_game_to_another_outdoor_court(
    client, session_factory, clock, club, group, four, payments, mailbox
):
    club_id, desk = club
    await changes_a_court(client, desk, "Court 1", indoor=False)
    await changes_a_court(client, desk, "Court 3", offered=False)
    booking = await books(client, session_factory, clock, club_id, group, four)
    await mailbox.drain()

    assert moved_to(await preview(client, desk, booking, "REPAIR")) == (
        "MOVED",
        "Court 4",
        False,
    )
    assert await preview(client, desk, booking, "WEATHER") == CALLED_OFF
    answer = await cancels(client, desk, booking, "WEATHER")

    assert answer == CALLED_OFF
    card = await home_card(client, four[0])
    assert (card["status"], card["called_off_reason"], card["club_cancel_reason"]) == (
        "CALLED_OFF",
        "CANCELLED_BY_THE_CLUB",
        "WEATHER",
    )
    await mailbox.drain()
    assert calls(payments, "cancel") == 4
    assert await owed_in(session_factory, clock, group) == [booking]


async def test_an_indoor_game_with_only_an_outdoor_court_free_is_called_off_and_owed(
    client, session_factory, clock, club, group, booking, four, payments, mailbox
):
    """Outdoors from indoors would be a different game to the players: a new
    card, never a move."""

    _, desk = club
    await changes_a_court(client, desk, "Court 3", offered=False)

    assert await preview(client, desk, booking, "REPAIR") == CALLED_OFF
    answer = await cancels(client, desk, booking, "REPAIR")

    assert answer == CALLED_OFF
    for player in four:
        card = await home_card(client, player)
        assert (card["status"], card["court_name"]) == ("CALLED_OFF", "Court 1")
        assert card["club_cancel_reason"] == "REPAIR"
    await mailbox.drain()
    # Before the cut-off: every hold let go, nothing refunded (#637).
    assert (calls(payments, "cancel"), calls(payments, "refund")) == (4, 0)
    assert await owed_in(session_factory, clock, group) == [booking]


async def test_a_court_the_club_now_sells_at_another_price_never_absorbs_it(
    client, session_factory, clock, club, group, booking, four
):
    """The club has raised padel to 160 zł since the game booked at 120: Court 3
    is no longer the same game to anybody, so the cancel calls it off."""

    _, desk = club
    await sets_prices(
        client,
        desk,
        [
            {"sport": "PADEL", "price_grosze": 160_00, "bands": []},
            {"sport": "TENNIS", "price_grosze": 80_00, "bands": []},
        ],
    )

    assert await preview(client, desk, booking, "REPAIR") == CALLED_OFF
    assert await cancels(client, desk, booking, "REPAIR") == CALLED_OFF
    assert (await home_card(client, four[0]))["status"] == "CALLED_OFF"


# --------------------------------------------------------------------------- #
# Anyway, and the cancel decides afresh
# --------------------------------------------------------------------------- #


async def test_cancel_the_game_anyway_calls_it_off_though_a_court_is_free(
    client, session_factory, clock, club, group, booking, four, payments, mailbox
):
    """A club closing the whole hour — an event, a power cut."""

    _, desk = club
    assert moved_to(await preview(client, desk, booking, "OTHER"))[0] == "MOVED"

    answer = await cancels(client, desk, booking, "OTHER", anyway=True)

    assert answer == CALLED_OFF
    card = await home_card(client, four[0])
    assert (card["status"], card["called_off_reason"], card["court_name"]) == (
        "CALLED_OFF",
        "CANCELLED_BY_THE_CLUB",
        "Court 1",
    )
    await mailbox.drain()
    assert calls(payments, "cancel") == 4
    assert await owed_in(session_factory, clock, group) == [booking]


async def test_the_cancel_moves_to_the_next_court_when_the_previewed_one_was_taken(
    client, session_factory, clock, club, booking, four, payments
):
    """Court 3 is in the preview; another game books it before the desk
    confirms. The cancel reads the courts again and takes Court 5."""

    club_id, desk = club
    court_5 = await adds_a_court(client, desk, name="Court 5", sport="PADEL")
    await sets_hours(client, desk, [court_5["id"]], every_hour_of_the_week())
    assert moved_to(await preview(client, desk, booking, "REPAIR"))[1] == "Court 3"
    other = await another_four_book_the_hour(
        client, session_factory, clock, payments, club_id
    )
    assert (await the_desk_s_row(client, desk, other))["court_name"] == "Court 3"

    answer = await cancels(client, desk, booking, "REPAIR")

    assert moved_to(answer) == ("MOVED", "Court 5", True)
    assert (await home_card(client, four[0]))["court_name"] == "Court 5"


async def test_the_cancel_calls_the_game_off_when_the_previewed_court_was_taken(
    client, session_factory, clock, club, group, booking, four, payments
):
    club_id, desk = club
    assert moved_to(await preview(client, desk, booking, "REPAIR"))[1] == "Court 3"
    await another_four_book_the_hour(client, session_factory, clock, payments, club_id)

    answer = await cancels(client, desk, booking, "REPAIR")

    # Only Court 4 is free, and it is outdoor.
    assert answer == CALLED_OFF
    assert (await home_card(client, four[0]))["status"] == "CALLED_OFF"
    assert await owed_in(session_factory, clock, group) == [booking]


# --------------------------------------------------------------------------- #
# After the cut-off
# --------------------------------------------------------------------------- #


async def test_after_the_cut_off_a_move_by_cancel_leaves_the_taken_shares_taken(
    client, session_factory, clock, club, group, booking, four, payments, mailbox
):
    _, desk = club
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()
    refunds_before = calls(payments, "refund")

    answer = await cancels(client, desk, booking, "DOUBLE_BOOKING")

    assert moved_to(answer) == ("MOVED", "Court 3", True)
    await mailbox.drain()
    assert calls(payments, "refund") == refunds_before == 0
    row = await the_desk_s_row(client, desk, booking)
    assert all((p["paid"], p["held"]) == (True, False) for p in row["players"])
    assert (row["money"]["collected_grosze"], row["money"]["refunded_grosze"]) == (
        4 * SHARE,
        0,
    )
    for player in four:
        card = await home_card(client, player)
        assert (card["status"], card["court_name"]) == ("BOOKED", "Court 3")
        assert "REFUND" not in await receipt_kinds(client, mailbox, player)
    notice = await newest_notice(client, mailbox, four[0])
    assert notice["body"] == (
        "Court 1 was booked twice · Padel · indoor · nothing else changes"
    )
    assert await owed_in(session_factory, clock, group) == []


# --------------------------------------------------------------------------- #
# The preview is the club's own, while the game is still to be played
# --------------------------------------------------------------------------- #


async def test_the_preview_is_the_club_s_own_and_only_while_the_game_is_to_be_played(
    client, clock, club, booking
):
    _, desk = club
    _, other = await a_club_and_its_desk(client, name="Kazimierz Padel")
    path = f"{BOOKINGS}/{booking}/cancellation/preview"

    elsewhere = await client.get(path, params={"reason": "REPAIR"}, headers=other)
    assert (elsewhere.status_code, elsewhere.json()["code"]) == (
        404,
        "booking_not_found",
    )

    await cancels(client, desk, booking, "REPAIR", anyway=True)
    off = await client.get(path, params={"reason": "REPAIR"}, headers=desk)
    assert (off.status_code, off.json()["code"]) == (409, "booking_is_called_off")


async def test_a_game_that_has_started_has_no_preview(client, clock, club, booking):
    _, desk = club
    clock.move(SATURDAY_FIVE - MONDAY_MORNING)

    late = await client.get(
        f"{BOOKINGS}/{booking}/cancellation/preview",
        params={"reason": "REPAIR"},
        headers=desk,
    )

    assert (late.status_code, late.json()["code"]) == (409, "game_has_started")

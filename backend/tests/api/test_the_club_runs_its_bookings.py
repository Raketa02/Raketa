"""**The club runs its Raketa bookings, and a player's attendance is recorded**
(#547; the mechanics §15, §16.7–§16.10, §16.14, §19; the screens B4, B6).

The club's desk reads its bookings **by day**, filtered, each with its players
(name, *paid*, *checked in*), its money and the group it came from. It **moves**
a booked game to another free court at the same hour, **cancels** one with a
reason — everybody refunded in full, nothing on anybody's record, the players
dealt a new card first — and **checks players in** on the day by a scanned or
typed code. And on the Game, the players who came **report one who did not**:
they have a day to dispute it, a player the club checked in cannot be reported,
and a no-show that stands is the strongest mark on a record.

Every act is taken over HTTP as the website and the phone take it, against the
fake payment provider; every claim is read where somebody would read it.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena, padel at 120 zł — 30 zł a seat
— with a 24-hour cut-off.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import (
    build_check_in_codes,
    build_court_hours,
    build_proposal_directory,
)
from app.core.config import get_settings
from app.kernel import Sport
from tests.api.club_courts_world import adds_a_court, sets_hours
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_player,
    every_hour_of_the_week,
    makes,
    says_yes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

BOOKINGS = "/api/v1/club/bookings"
CHECK_INS = "/api/v1/club/check-ins"
HOME = "/api/v1/home"
RECEIPTS = "/api/v1/players/me/receipts"
SHARE = 30_00
CUT_OFF = SATURDAY_FIVE - timedelta(hours=24)
SATURDAY = "2026-10-10"


@pytest.fixture
def clock(app):
    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> tuple[str, dict]:
    """Bonarka Arena, Instant, checking its players in — and a second padel
    court, Court 3, a game can be moved to."""

    club_id, desk = await a_club_and_its_desk(client, way="INSTANT", check_in=True)
    padel = await client.get("/api/v1/club/courts", headers=desk)
    court_1 = next(one for one in padel.json()["courts"] if one["name"] == "Court 1")
    court_2 = next(one for one in padel.json()["courts"] if one["name"] == "Court 2")
    court_3 = await adds_a_court(client, desk, name="Court 3", sport="PADEL")
    await sets_hours(
        client,
        desk,
        [court_1["id"], court_2["id"], court_3["id"]],
        every_hour_of_the_week(),
    )
    return club_id, desk


@pytest.fixture
async def four(client, payments) -> list[dict]:
    return [
        await a_player(client, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek")
    ]


@pytest.fixture
async def group(client, club, four) -> UUID:
    return await a_group(client, four[0], club[0], *four[1:])


@pytest.fixture
async def booking(client, session_factory, clock, club, group, four) -> str:
    """The four's game on Saturday at 17:00 on Court 1, booked by Tomek's yes."""

    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club[0], versions=(tuple(four),)
    )
    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    return last.json()["booked"]["booking_id"]


async def the_day(client, desk: dict, *, day: str = SATURDAY, chosen: str = "ALL"):
    read = await client.get(
        BOOKINGS, params={"date": day, "filter": chosen}, headers=desk
    )
    assert read.status_code == 200, read.text
    return read.json()


async def details_of(client, player: dict, booking_id: str) -> dict:
    read = await client.get(f"/api/v1/bookings/{booking_id}", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def home_of(client, player: dict) -> list[dict]:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["games"]


async def game_of(client, player: dict, game_id: str) -> dict:
    read = await client.get("/api/v1/games", headers=player["headers"])
    assert read.status_code == 200, read.text
    return next(one for one in read.json()["games"] if one["game_id"] == game_id)


async def own_record(client, player: dict) -> dict:
    read = await client.get("/api/v1/players/me/record", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


def strand(record: dict, name: str) -> dict | None:
    return next(
        (
            one
            for one in record.get("reliability", {}).get("strands", ())
            if one["strand"] == name
        ),
        None,
    )


# --------------------------------------------------------------------------- #
# The day
# --------------------------------------------------------------------------- #


async def test_the_club_reads_its_bookings_by_day_with_what_it_may_see(
    client, club, booking, four
):
    _, desk = club

    day = await the_day(client, desk)

    assert day["day"] == SATURDAY
    [row] = day["bookings"]
    assert row["booking_id"] == booking
    assert (row["court_name"], row["sport"], row["kind"], row["status"]) == (
        "Court 1",
        "PADEL",
        "COMPETITIVE",
        "BOOKED",
    )
    assert sorted(player["name"] for player in row["players"]) == [
        "ewa",
        "kuba",
        "ola",
        "tomek",
    ]
    assert all(player["paid"] for player in row["players"])
    assert all(player["checked_in_at"] is None for player in row["players"])
    # Nothing about a player but the name, whether they paid, and the check-in.
    assert set(row["players"][0]) == {"player_id", "name", "paid", "checked_in_at"}
    assert row["money"] == {
        "price_grosze": 120_00,
        "collected_grosze": 4 * SHARE,
        "refunded_grosze": 0,
    }
    assert row["booked_from"]["name"] == "Sobotni padel"
    assert row["booked_from"]["official"] is False
    assert row["may_move_or_cancel"] is True
    assert day["counts"] == {
        "all": 1,
        "waiting_for_you": 0,
        "seat_open": 0,
        "called_off": 0,
    }
    assert (await the_day(client, desk, day="2026-10-11"))["bookings"] == []


async def test_the_filters_narrow_the_day_and_a_seat_open_is_its_own(
    client, club, booking, four
):
    _, desk = club
    left = await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=four[1]["headers"]
    )
    assert left.status_code == 200, left.text

    seat_open = await the_day(client, desk, chosen="SEAT_OPEN")
    called_off = await the_day(client, desk, chosen="CALLED_OFF")

    [row] = seat_open["bookings"]
    assert (row["status"], row["open_seats"], len(row["players"])) == (
        "SEAT_OPEN",
        1,
        3,
    )
    # The leaver was refunded, less the card fee.
    assert 0 < row["money"]["refunded_grosze"] < SHARE
    assert called_off["bookings"] == []
    assert called_off["counts"]["seat_open"] == 1


async def test_a_game_whose_hour_has_passed_is_played(client, clock, club, booking):
    _, desk = club
    clock.move(SATURDAY_FIVE - MONDAY_MORNING + timedelta(hours=1))

    [row] = (await the_day(client, desk))["bookings"]

    assert (row["status"], row["may_move_or_cancel"]) == ("PLAYED", False)


async def test_another_club_never_reads_or_runs_this_club_s_bookings(
    client, club, booking
):
    _, desk = club
    _, other = await a_club_and_its_desk(client, name="Kazimierz Padel")

    assert (await the_day(client, other))["bookings"] == []
    free = await client.get(f"{BOOKINGS}/{booking}/free-courts", headers=other)
    assert (free.status_code, free.json()["code"]) == (404, "booking_not_found")
    for target, headers in ((booking, other), (str(uuid4()), desk)):
        cancelled = await client.post(
            f"{BOOKINGS}/{target}/cancellation",
            json={"reason": "OTHER"},
            headers=headers,
        )
        moved = await client.post(
            f"{BOOKINGS}/{target}/move",
            json={"court_id": str(uuid4())},
            headers=headers,
        )
        assert (cancelled.status_code, cancelled.json()["code"]) == (
            404,
            "booking_not_found",
        )
        assert (moved.status_code, moved.json()["code"]) == (404, "booking_not_found")


# --------------------------------------------------------------------------- #
# Move
# --------------------------------------------------------------------------- #


async def test_the_club_moves_a_game_to_another_free_court_and_the_players_read_it(
    client, session_factory, clock, club, booking, four
):
    club_id, desk = club

    free = await client.get(f"{BOOKINGS}/{booking}/free-courts", headers=desk)
    assert free.status_code == 200, free.text
    [court_3] = free.json()["courts"]
    assert court_3["name"] == "Court 3"

    moved = await client.post(
        f"{BOOKINGS}/{booking}/move",
        json={"court_id": court_3["court_id"]},
        headers=desk,
    )

    assert moved.status_code == 200, moved.text
    assert moved.json() == court_3
    assert (await details_of(client, four[0], booking))["court_name"] == "Court 3"
    [row] = (await the_day(client, desk))["bookings"]
    assert row["court_name"] == "Court 3"
    # Court 1 is free at the hour again, and Court 3 is not.
    again = await client.get(f"{BOOKINGS}/{booking}/free-courts", headers=desk)
    assert [one["name"] for one in again.json()["courts"]] == ["Court 1"]


async def test_a_court_that_is_not_free_is_refused_and_so_is_a_move_once_started(
    client, clock, club, booking
):
    _, desk = club
    courts = (await client.get("/api/v1/club/courts", headers=desk)).json()["courts"]
    tennis = next(one for one in courts if one["name"] == "Court 2")

    wrong = await client.post(
        f"{BOOKINGS}/{booking}/move", json={"court_id": tennis["id"]}, headers=desk
    )
    assert (wrong.status_code, wrong.json()["code"]) == (409, "court_not_free")

    clock.move(SATURDAY_FIVE - MONDAY_MORNING)
    court_3 = next(one for one in courts if one["name"] == "Court 3")
    late = await client.post(
        f"{BOOKINGS}/{booking}/move", json={"court_id": court_3["id"]}, headers=desk
    )
    assert (late.status_code, late.json()["code"]) == (409, "game_has_started")


# --------------------------------------------------------------------------- #
# Cancel
# --------------------------------------------------------------------------- #


async def test_the_club_cancels_with_a_reason_and_everybody_is_refunded_in_full(
    client, session_factory, clock, club, group, booking, four, mailbox
):
    club_id, desk = club

    cancelled = await client.post(
        f"{BOOKINGS}/{booking}/cancellation", json={"reason": "WEATHER"}, headers=desk
    )

    assert cancelled.status_code == 204, cancelled.text
    await mailbox.drain()
    for player in four:
        [card] = await home_of(client, player)
        assert (
            card["status"],
            card["called_off_reason"],
            card["club_cancel_reason"],
        ) == (
            "CALLED_OFF",
            "CANCELLED_BY_THE_CLUB",
            "WEATHER",
        )
        assert card["money"]["refunded_grosze"] == SHARE
        receipts = (await client.get(RECEIPTS, headers=player["headers"])).json()[
            "receipts"
        ]
        refund = next(one for one in receipts if one["kind"] == "REFUND")
        assert (refund["amount_grosze"], refund["card_fee_grosze"]) == (SHARE, 0)
    [email] = [
        sent
        for sent in await mailbox.to("ola@example.com")
        if sent.subject.startswith("Game cancelled by Bonarka Arena")
    ]
    assert "because of the weather" in email.text
    [row] = (await the_day(client, desk, chosen="CALLED_OFF"))["bookings"]
    assert (row["called_off_reason"], row["cancel_reason"]) == (
        "CANCELLED_BY_THE_CLUB",
        "WEATHER",
    )
    assert row["money"]["refunded_grosze"] == 4 * SHARE
    # The hour is the club's to sell again, and the four are owed a new card.
    async with session_factory() as session:
        assert (
            await build_court_hours(session).offered(
                UUID(club_id), sport=Sport.PADEL, start=SATURDAY_FIVE, now=clock.now()
            )
            is not None
        )
        owed = await build_proposal_directory(session).owed_a_new_card_in(
            group, now=clock.now()
        )
    assert [str(one) for one in owed] == [booking]


async def test_a_cancelled_game_is_on_nobody_s_record(
    client, clock, club, booking, four
):
    _, desk = club
    clock.move(CUT_OFF - MONDAY_MORNING + timedelta(hours=1))
    # Kuba left after the cut-off: his seat is still paid for, and nobody took it.
    left = await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=four[1]["headers"]
    )
    assert left.status_code == 200, left.text

    cancelled = await client.post(
        f"{BOOKINGS}/{booking}/cancellation", json={"reason": "REPAIR"}, headers=desk
    )
    assert cancelled.status_code == 204, cancelled.text
    clock.move(timedelta(days=2))

    for player in four:
        assert strand(await own_record(client, player), "KEEPS_PLANS") is None
    [row] = (await the_day(client, desk))["bookings"]
    # Kuba's paid seat was given back in full with everybody else's.
    assert row["money"]["refunded_grosze"] == 4 * SHARE


async def test_a_game_is_cancelled_only_until_it_starts(client, clock, club, booking):
    _, desk = club
    clock.move(SATURDAY_FIVE - MONDAY_MORNING + timedelta(minutes=5))

    late = await client.post(
        f"{BOOKINGS}/{booking}/cancellation", json={"reason": "OTHER"}, headers=desk
    )

    assert (late.status_code, late.json()["code"]) == (409, "game_has_started")


# --------------------------------------------------------------------------- #
# Check in
# --------------------------------------------------------------------------- #


async def test_the_desk_checks_a_player_in_by_the_code_on_their_phone(
    client, clock, club, booking, four
):
    _, desk = club
    clock.move(SATURDAY_FIVE - MONDAY_MORNING - timedelta(minutes=8))
    code = (await details_of(client, four[2], booking))["check_in"]

    typed = await client.post(
        CHECK_INS, json={"code": code["short_code"].lower()}, headers=desk
    )

    assert typed.status_code == 200, typed.text
    assert typed.json()["player"]["name"] == "ewa"
    assert (typed.json()["court_name"], typed.json()["sport"]) == ("Court 1", "PADEL")
    again = await client.post(
        CHECK_INS, json={"code": code["qr_payload"]}, headers=desk
    )
    assert (again.status_code, again.json()["code"]) == (409, "already_checked_in")
    assert datetime.fromisoformat(
        again.json()["details"]["checked_in_at"]
    ) == datetime.fromisoformat(typed.json()["checked_in_at"])
    [row] = (await the_day(client, desk))["bookings"]
    checked = {one["name"]: one["checked_in_at"] for one in row["players"]}
    assert checked["ewa"] is not None and checked["ola"] is None
    tiles = (await details_of(client, four[0], booking))["sides"]
    assert {
        tile["player_id"]: tile["checked_in"]
        for tile in (*tiles["yours"], *tiles["theirs"])
    }[str(four[2]["id"])] is True


async def test_a_code_for_another_day_or_club_or_nobody_is_refused_with_its_reason(
    client, clock, club, booking, four
):
    _, desk = club
    code = build_check_in_codes(get_settings()).code_for(UUID(booking), four[0]["id"])

    # Monday: Ola's game is on Saturday.
    early = await client.post(CHECK_INS, json={"code": code.short_code}, headers=desk)
    assert (early.status_code, early.json()["code"]) == (
        409,
        "check_in_code_for_another_day",
    )

    clock.move(SATURDAY_FIVE - MONDAY_MORNING - timedelta(minutes=10))
    _, other = await a_club_and_its_desk(client, name="Kazimierz Padel", check_in=True)
    elsewhere = await client.post(
        CHECK_INS, json={"code": code.short_code}, headers=other
    )
    assert (elsewhere.status_code, elsewhere.json()["code"]) == (
        409,
        "check_in_code_for_another_club",
    )
    nobody = await client.post(CHECK_INS, json={"code": "ZZZZZZ"}, headers=desk)
    assert (nobody.status_code, nobody.json()["code"]) == (404, "check_in_code_unknown")


async def test_a_club_that_does_not_check_players_in_is_refused(
    client, clock, session_factory, payments
):
    club_id, desk = await a_club_and_its_desk(client, name="Ogrody 33")

    refused = await client.post(CHECK_INS, json={"code": "ABCDEF"}, headers=desk)

    assert (refused.status_code, refused.json()["code"]) == (409, "check_in_is_off")


# --------------------------------------------------------------------------- #
# Somebody did not come
# --------------------------------------------------------------------------- #


async def _game_id(client, player, booking) -> str:
    return (await details_of(client, player, booking))["game_id"]


async def test_a_player_who_came_reports_one_who_did_not_and_it_stands_its_day(
    client, clock, club, booking, four
):
    ola, kuba, ewa, tomek = four
    game_id = await _game_id(client, ola, booking)
    clock.move(SATURDAY_FIVE - MONDAY_MORNING + timedelta(hours=2))

    reported = await client.post(
        f"/api/v1/games/{game_id}/no-shows",
        json={"player_id": str(kuba["id"])},
        headers=ola["headers"],
    )

    assert reported.status_code == 200, reported.text
    assert reported.json()["standing"] == "NO_SHOW_REPORTED"
    [no_show] = reported.json()["no_shows"]
    assert (no_show["player_id"], no_show["name"], no_show["disputed_at"]) == (
        str(kuba["id"]),
        "kuba",
        None,
    )
    [kubas_card] = await home_of(client, kuba)
    [olas_card] = await home_of(client, ola)
    assert (kubas_card["status"], kubas_card["uncounted_reason"]) == (
        "UNCOUNTED",
        "NO_SHOW",
    )
    assert (kubas_card["needs_you"], olas_card["needs_you"]) == (True, False)
    score = await client.post(
        f"/api/v1/games/{game_id}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=ewa["headers"],
    )
    assert (score.status_code, score.json()["code"]) == (409, "a_no_show_is_reported")

    clock.move(timedelta(hours=24))

    assert (await game_of(client, tomek, game_id))["standing"] == "NO_SHOW"
    kubas = await own_record(client, kuba)
    assert strand(kubas, "KEEPS_PLANS") == {
        "strand": "KEEPS_PLANS",
        "good": 0,
        "opportunities": 1,
        "pct": 0,
    }
    assert strand(kubas, "SHOWS_UP") == {
        "strand": "SHOWS_UP",
        "good": 0,
        "opportunities": 1,
        "pct": 0,
    }
    olas = await own_record(client, ola)
    assert strand(olas, "KEEPS_PLANS")["good"] == 1
    assert strand(olas, "SHOWS_UP")["good"] == 1


async def test_the_reported_player_disputes_in_their_day_and_nobody_arbitrates(
    client, clock, club, booking, four
):
    ola, kuba, *_ = four
    game_id = await _game_id(client, ola, booking)
    clock.move(SATURDAY_FIVE - MONDAY_MORNING + timedelta(hours=2))
    await client.post(
        f"/api/v1/games/{game_id}/no-shows",
        json={"player_id": str(kuba["id"])},
        headers=ola["headers"],
    )
    clock.move(timedelta(hours=23))

    disputed = await client.post(
        f"/api/v1/games/{game_id}/no-shows/dispute", headers=kuba["headers"]
    )

    assert disputed.status_code == 200, disputed.text
    assert disputed.json()["standing"] == "UNSCORED"
    assert disputed.json()["no_shows"][0]["disputed_at"] is not None
    clock.move(timedelta(days=2))
    assert strand(await own_record(client, kuba), "KEEPS_PLANS")["good"] == 1
    [card] = await home_of(client, kuba)
    assert (card["status"], card["uncounted_reason"]) == ("UNCOUNTED", None)


async def test_a_dispute_after_the_day_is_too_late(client, clock, club, booking, four):
    ola, kuba, *_ = four
    game_id = await _game_id(client, ola, booking)
    clock.move(SATURDAY_FIVE - MONDAY_MORNING + timedelta(hours=2))
    await client.post(
        f"/api/v1/games/{game_id}/no-shows",
        json={"player_id": str(kuba["id"])},
        headers=ola["headers"],
    )
    clock.move(timedelta(hours=24))

    late = await client.post(
        f"/api/v1/games/{game_id}/no-shows/dispute", headers=kuba["headers"]
    )

    assert (late.status_code, late.json()["code"]) == (
        409,
        "the_dispute_window_has_closed",
    )


async def test_a_player_the_club_checked_in_cannot_be_reported(
    client, clock, club, booking, four
):
    _, desk = club
    ola, kuba, *_ = four
    game_id = await _game_id(client, ola, booking)
    clock.move(SATURDAY_FIVE - MONDAY_MORNING - timedelta(minutes=5))
    code = (await details_of(client, kuba, booking))["check_in"]
    assert (
        await client.post(CHECK_INS, json={"code": code["short_code"]}, headers=desk)
    ).status_code == 200
    clock.move(timedelta(hours=2))

    refused = await client.post(
        f"/api/v1/games/{game_id}/no-shows",
        json={"player_id": str(kuba["id"])},
        headers=ola["headers"],
    )

    assert (refused.status_code, refused.json()["code"]) == (
        409,
        "checked_in_at_the_club",
    )


async def test_nobody_is_reported_before_the_game_starts(client, club, booking, four):
    ola, kuba, *_ = four
    game_id = await _game_id(client, ola, booking)

    early = await client.post(
        f"/api/v1/games/{game_id}/no-shows",
        json={"player_id": str(kuba["id"])},
        headers=ola["headers"],
    )

    assert (early.status_code, early.json()["code"]) == (
        409,
        "the_game_has_not_started",
    )


def test_the_game_day_is_saturday():
    """The literals above agree with the calendar."""

    assert warsaw(10, 17) == SATURDAY_FIVE

"""**Leaving a booked game, and the cut-off** (#544; the mechanics §12.3, §13,
§14.1, §15.4, §16.12, §19).

Leaving is free until the club's cut-off — refunded at once, less the card fee —
and after it the seat stays paid until somebody takes it. **A game plays full or
not at all**: a seat still empty at the cut-off calls the game off and gives
everybody still in all their money back; a seat left after it lets the game go
ahead short, and a game that starts short ends *uncounted · a seat was empty*.

Every act is taken over HTTP as the phone takes it, against the fake payment
provider; the cut-off job runs as the job does, the clock moved to it; and every
claim is read where somebody would read it — Home, the details, the receipts,
the mailbox, the record.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena, padel at 120 zł — 30 zł a
seat — with a 24-hour cut-off, so free to leave until **Friday 17:00**.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_call_off_short_games, build_court_hours
from app.core.config import get_settings
from app.kernel import Sport
from app.modules.payments.domain.card_fee import estimated_card_fee
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_player,
    live_ids,
    makes,
    says_yes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

HOME = "/api/v1/home"
RECEIPTS = "/api/v1/players/me/receipts"
SHARE = 30_00
#: The card fee the fake provider keeps on a 30 zł refund: 1.5 % and 1 zł.
FEE = 1_45
CUT_OFF = SATURDAY_FIVE - timedelta(hours=24)
DESK_EMAIL = "desk@bonarka.pl"
A_SCORE = {"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}}


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    """Bonarka Arena, Instant, with its desk's sign-in."""

    club_id, _desk = await a_club_and_its_desk(client, way="INSTANT")
    return club_id


@pytest.fixture
async def four(client, payments) -> list[dict]:
    """Ola, Kuba, Ewa and Tomek: rated in padel, each with a card that pays."""

    return [
        await a_player(client, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek")
    ]


@pytest.fixture
async def group(client, club, four) -> UUID:
    return await a_group(client, four[0], club, *four[1:])


@pytest.fixture
async def booking(client, session_factory, clock, club, group, four) -> str:
    """The four's game on Saturday at 17:00, booked by Tomek's yes."""

    return await a_booked_game(client, session_factory, clock, club, group, four)


async def a_booked_game(client, session_factory, clock, club, group, four) -> str:
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    assert last.json()["booked"] is not None, last.text
    return last.json()["booked"]["booking_id"]


async def leaves(client, player: dict, booking_id: str | UUID):
    return await client.post(
        f"/api/v1/bookings/{booking_id}/departure", headers=player["headers"]
    )


async def details_of(client, player: dict, booking_id: str) -> dict:
    read = await client.get(f"/api/v1/bookings/{booking_id}", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def cuts_off(session_factory, clock):
    """One run of the cut-off job, at the clock's now."""

    async with session_factory() as session:
        return await build_call_off_short_games(
            session, clock=clock, settings=get_settings()
        ).execute()


async def the_court_is_on_sale(session_factory, clock, club: str) -> bool:
    """Whether a padel court at the club on Saturday at 17:00 is for sale."""

    async with session_factory() as session:
        offered = await build_court_hours(session).offered(
            UUID(club), sport=Sport.PADEL, start=SATURDAY_FIVE, now=clock.now()
        )
    return offered is not None


async def own_record(client, player: dict) -> dict:
    read = await client.get("/api/v1/players/me/record", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def rooms_of(client, player: dict) -> list[dict]:
    read = await client.get("/api/v1/conversations", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["conversations"]


async def home_of(client, player: dict) -> list[dict]:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["games"]


async def receipts_of(client, mailbox, player: dict) -> list[dict]:
    # The money follows the commit: the outbox gives the share back first.
    await mailbox.drain()
    read = await client.get(RECEIPTS, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["receipts"]


# --------------------------------------------------------------------------- #
# Leaving before the cut-off
# --------------------------------------------------------------------------- #


async def test_leaving_before_the_cut_off_refunds_the_leaver_less_the_card_fee(
    client, booking, four, mailbox
):
    ola, kuba, *_ = four

    left = await leaves(client, kuba, booking)

    assert left.status_code == 200, left.text
    assert left.json()["left"] == "BEFORE_THE_CUT_OFF"
    assert FEE == estimated_card_fee(SHARE)
    refund, charge = await receipts_of(client, mailbox, kuba)
    assert (charge["kind"], charge["amount_grosze"]) == ("CHARGE", SHARE)
    assert (refund["kind"], refund["amount_grosze"], refund["card_fee_grosze"]) == (
        "REFUND",
        SHARE - FEE,
        FEE,
    )
    [card] = await home_of(client, ola)
    assert (card["status"], card["open_seats"], card["needs_you"]) == (
        "SEAT_OPEN",
        1,
        True,
    )
    assert await home_of(client, kuba) == []
    [email] = [
        sent
        for sent in await mailbox.to("kuba@example.com")
        if sent.subject.startswith("You left the game")
    ]
    assert "30 zł share is being refunded" in email.text


async def test_the_details_say_what_leaving_costs_before_the_player_leaves(
    client, clock, booking, four
):
    ola = four[0]

    before = (await details_of(client, ola, booking))["leaving"]
    clock.move(CUT_OFF - MONDAY_MORNING)
    after = (await details_of(client, ola, booking))["leaving"]
    clock.move(SATURDAY_FIVE - CUT_OFF)
    started = (await details_of(client, ola, booking))["leaving"]

    assert before == {
        "kind": "BEFORE_THE_CUT_OFF",
        "refund_grosze": SHARE - FEE,
        "card_fee_grosze": FEE,
    }
    assert after["kind"] == "AFTER_THE_CUT_OFF"
    assert started is None


# --------------------------------------------------------------------------- #
# Leaving after the cut-off, after the start, and while the club decides
# --------------------------------------------------------------------------- #


async def test_leaving_after_the_cut_off_keeps_the_seat_paid_and_offers_it(
    client, clock, booking, four, mailbox
):
    ola, kuba, *_ = four
    clock.move(CUT_OFF - MONDAY_MORNING + timedelta(hours=1))

    left = await leaves(client, kuba, booking)

    assert left.status_code == 200, left.text
    assert left.json()["left"] == "AFTER_THE_CUT_OFF"
    [charge] = await receipts_of(client, mailbox, kuba)
    assert charge["kind"] == "CHARGE"
    [card] = await home_of(client, ola)
    assert (card["status"], card["open_seats"]) == ("SEAT_OPEN", 1)
    assert card["money"]["free_to_leave_until"] is None
    assert card["money"]["paid"] is True


async def test_nobody_leaves_a_game_that_has_started(client, clock, booking, four):
    clock.move(SATURDAY_FIVE - MONDAY_MORNING)

    left = await leaves(client, four[1], booking)

    assert left.status_code == 409, left.text
    assert left.json()["code"] == "game_has_started"


async def test_a_game_is_left_once_and_only_by_somebody_in_it(
    client, booking, four, payments
):
    kuba = four[1]
    stranger = await a_player(client, payments, "zosia")

    assert (await leaves(client, kuba, booking)).status_code == 200
    again = await leaves(client, kuba, booking)
    outside = await leaves(client, stranger, booking)

    assert (again.status_code, again.json()["code"]) == (404, "booking_not_found")
    assert (outside.status_code, outside.json()["code"]) == (404, "booking_not_found")


async def test_leaving_while_the_club_decides_withdraws_the_yes_and_nobody_paid(
    client, session_factory, clock, four
):
    club, _desk = await a_club_and_its_desk(
        client, name="Kazimierz Padel", way="ON_REQUEST"
    )
    group = await a_group(client, four[0], club, *four[1:])
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four:
        assert (await says_yes(client, player, proposal)).status_code == 200
    ola, kuba, *_ = four

    left = await leaves(client, kuba, proposal)

    assert left.status_code == 200, left.text
    assert left.json()["left"] == "WHILE_WAITING_FOR_THE_CLUB"
    assert await home_of(client, ola) == []


async def test_the_leaver_leaves_the_game_s_chat_and_the_others_keep_it(
    client, booking, four, mailbox
):
    ola, kuba, *_ = four
    await mailbox.drain()
    assert [room["booking_id"] for room in await rooms_of(client, kuba)] == [booking]

    assert (await leaves(client, kuba, booking)).status_code == 200
    await mailbox.drain()

    assert await rooms_of(client, kuba) == []
    assert [room["booking_id"] for room in await rooms_of(client, ola)] == [booking]


# --------------------------------------------------------------------------- #
# The cut-off: a game plays full or not at all
# --------------------------------------------------------------------------- #


async def test_a_game_still_short_at_its_cut_off_is_called_off_and_everybody_refunded(
    client, session_factory, clock, club, booking, four, mailbox
):
    ola, kuba, ewa, tomek = four
    assert (await leaves(client, kuba, booking)).status_code == 200
    await mailbox.drain()
    clock.move(CUT_OFF - MONDAY_MORNING)

    # Read off the clock from the cut-off on, before anything records it.
    [card] = await home_of(client, ola)
    assert (card["status"], card["called_off_reason"]) == (
        "CALLED_OFF",
        "SHORT_AT_THE_CUT_OFF",
    )
    assert card["money"]["refunded_grosze"] == SHARE
    assert not await the_court_is_on_sale(session_factory, clock, club)

    run = await cuts_off(session_factory, clock)

    assert (run.games, run.conflicts) == (1, 0)
    for player in (ola, ewa, tomek):
        refund, charge = await receipts_of(client, mailbox, player)
        assert (refund["kind"], refund["amount_grosze"], refund["card_fee_grosze"]) == (
            "REFUND",
            SHARE,
            0,
        )
    assert [r["kind"] for r in await receipts_of(client, mailbox, kuba)] == [
        "REFUND",
        "CHARGE",
    ]
    assert await the_court_is_on_sale(session_factory, clock, club)
    assert await rooms_of(client, ola) == []
    [called_off] = [
        sent
        for sent in await mailbox.to("ola@example.com")
        if sent.subject.startswith("Game called off")
    ]
    assert called_off.subject == "Game called off · you're refunded 30 zł"
    [desk] = await mailbox.to(DESK_EMAIL)
    assert desk.subject == (
        "A game was called off at the cut-off — the hour is free again"
    )
    again = await cuts_off(session_factory, clock)
    assert (again.games, again.conflicts) == (0, 0)


async def test_a_game_whose_seat_opened_after_the_cut_off_goes_ahead_short(
    client, session_factory, clock, booking, four
):
    ola, kuba, *_ = four
    clock.move(CUT_OFF - MONDAY_MORNING + timedelta(hours=1))
    assert (await leaves(client, kuba, booking)).status_code == 200

    assert (await cuts_off(session_factory, clock)).games == 0
    clock.move(SATURDAY_FIVE - CUT_OFF)
    assert (await cuts_off(session_factory, clock)).games == 0

    details = await details_of(client, ola, booking)
    assert (details["status"], details["uncounted_reason"]) == (
        "UNCOUNTED",
        "SEAT_EMPTY",
    )
    told = await client.post(
        f"/api/v1/games/{details['game_id']}/result",
        json=A_SCORE,
        headers=ola["headers"],
    )
    assert (told.status_code, told.json()["code"]) == (409, "the_game_started_short")


# --------------------------------------------------------------------------- #
# A full week paused, and back
# --------------------------------------------------------------------------- #


async def a_capped_week(client, session_factory, clock, club, group, four) -> UUID:
    """Ola plays one game a week and said yes to Sunday's before Saturday's
    booked — so Saturday's booking paused her Sunday yes. Sunday's card."""

    ola = four[0]
    capped = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=ola["headers"],
    )
    assert capped.status_code == 200, capped.text
    sunday = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 10),
        versions=(tuple(four),),
    )
    assert (await says_yes(client, ola, sunday)).status_code == 200
    return sunday


async def test_a_paused_yes_comes_back_when_the_game_that_paused_it_is_called_off(
    client, session_factory, clock, club, group, four, mailbox
):
    ola, kuba, *_ = four
    sunday = await a_capped_week(client, session_factory, clock, club, group, four)
    booking = await a_booked_game(client, session_factory, clock, club, group, four)
    assert str(sunday) not in await live_ids(client, ola)
    assert (await leaves(client, kuba, booking)).status_code == 200
    await mailbox.drain()
    assert str(sunday) not in await live_ids(client, ola)

    clock.move(CUT_OFF - MONDAY_MORNING)
    assert (await cuts_off(session_factory, clock)).games == 1
    await mailbox.drain()

    assert str(sunday) in await live_ids(client, ola)


async def test_a_paused_yes_comes_back_when_its_player_leaves_the_game_that_paused_it(
    client, session_factory, clock, club, group, four, mailbox
):
    ola = four[0]
    sunday = await a_capped_week(client, session_factory, clock, club, group, four)
    booking = await a_booked_game(client, session_factory, clock, club, group, four)

    assert (await leaves(client, ola, booking)).status_code == 200
    await mailbox.drain()

    assert str(sunday) in await live_ids(client, ola)


async def test_a_cut_off_reached_only_after_the_hour_still_gives_the_money_back(
    client, session_factory, clock, booking, four, mailbox
):
    ola, kuba, *_ = four
    assert (await leaves(client, kuba, booking)).status_code == 200
    clock.move(SATURDAY_FIVE - MONDAY_MORNING + timedelta(minutes=10))

    assert (await cuts_off(session_factory, clock)).games == 1

    refund, _charge = await receipts_of(client, mailbox, ola)
    assert (refund["kind"], refund["amount_grosze"]) == ("REFUND", SHARE)
    [desk] = await mailbox.to(DESK_EMAIL)
    assert desk.subject == "A game was called off at the cut-off"
    assert "Its hour has already begun." in desk.text


async def test_a_game_short_at_its_cut_off_is_not_left_before_the_job_records_it(
    client, clock, booking, four
):
    ola, kuba, *_ = four
    assert (await leaves(client, kuba, booking)).status_code == 200
    clock.move(CUT_OFF - MONDAY_MORNING)

    left = await leaves(client, ola, booking)

    assert (left.status_code, left.json()["code"]) == (409, "booking_is_called_off")


async def test_the_record_marks_a_leaver_whose_seat_called_the_game_off(
    client, session_factory, clock, booking, four, mailbox
):
    """Leaving before the cut-off is on the record only if the game is then
    called off because of that seat — and nothing is on the record of those
    who stayed (the mechanics §14.1, §15.4)."""

    ola, kuba, *_ = four
    assert (await leaves(client, kuba, booking)).status_code == 200
    clock.move(CUT_OFF - MONDAY_MORNING)
    assert (await cuts_off(session_factory, clock)).games == 1

    kubas = await own_record(client, kuba)
    olas = await own_record(client, ola)

    assert {
        "strand": "KEEPS_PLANS",
        "good": 0,
        "opportunities": 1,
        "pct": 0,
    } in kubas["reliability"]["strands"]
    assert "reliability" not in olas


async def test_the_record_marks_a_leaver_after_the_cut_off_nobody_replaced(
    client, clock, booking, four
):
    ola, kuba, *_ = four
    clock.move(CUT_OFF - MONDAY_MORNING + timedelta(hours=1))
    assert (await leaves(client, kuba, booking)).status_code == 200

    before = await own_record(client, kuba)
    clock.move(SATURDAY_FIVE - CUT_OFF)
    after = await own_record(client, kuba)

    assert "reliability" not in before
    assert {
        "strand": "KEEPS_PLANS",
        "good": 0,
        "opportunities": 1,
        "pct": 0,
    } in after["reliability"]["strands"]
    assert "reliability" not in await own_record(client, ola)

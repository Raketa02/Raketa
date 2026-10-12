"""**The fill holds the shares and the cut-off takes them** (#637; the mechanics
Q113, §12.2, §12.3, §13, §14.1, §16.9; ADR-0189's 2026-10-10 amendment).

When a game fills, every seat's share is **held** on its player's card and
nothing is taken; the club's **cut-off** takes it. Leaving before the cut-off
lets the hold go — nothing is taken, nobody is refunded, no fee arises — and a
game still short at its cut-off is called off with every hold let go, so nobody
pays anything. A game that fills after its cut-off is taken at once, as before.

Every act is taken over HTTP as the phone and the desk take it, against the
fake payment provider; the cut-off job runs as the job does, the clock moved to
it; and every claim is read where somebody would read it — Home, the details,
the receipts, the club's Money and Bookings, the mailbox, and the calls made to
the provider.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena, padel at 120 zł — 30 zł a
seat — with a 24-hour cut-off: **Friday 17:00**.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_the_cut_off
from app.core.config import get_settings
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_player,
    makes,
    says_yes,
)
from tests.unit.fake_clock import MovableClock

HOME = "/api/v1/home"
RECEIPTS = "/api/v1/players/me/receipts"
MONEY = "/api/v1/club/money"
BOOKINGS = "/api/v1/club/bookings"
SHARE = 30_00
CUT_OFF = SATURDAY_FIVE - timedelta(hours=24)
#: The cut-off on the wire: Friday 17:00 in Kraków, in UTC.
CUT_OFF_ON_THE_WIRE = "2026-10-09T15:00:00Z"


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> tuple[str, dict]:
    """Bonarka Arena, Instant: the club and its desk's session."""

    return await a_club_and_its_desk(client, way="INSTANT")


@pytest.fixture
async def four(client, payments) -> list[dict]:
    """Ola, Kuba, Ewa and Tomek: rated in padel, each with a card that pays."""

    return [
        await a_player(client, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek")
    ]


async def fills(client, session_factory, clock, club: str, four: list[dict]):
    """The four's game at the club on Saturday at 17:00, made now — Tomek's yes
    the last. The last yes's answer."""

    group = await a_group(client, four[0], club, *four[1:])
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    return last.json()


async def a_booked_game(client, session_factory, clock, club, four) -> str:
    last = await fills(client, session_factory, clock, club, four)
    assert last["booked"] is not None, last
    return last["booked"]["booking_id"]


async def cuts_off(session_factory, clock):
    """One run of the cut-off job, at the clock's now."""

    async with session_factory() as session:
        return await build_the_cut_off(
            session, clock=clock, settings=get_settings()
        ).execute()


async def leaves(client, player: dict, booking_id: str):
    left = await client.post(
        f"/api/v1/bookings/{booking_id}/departure", headers=player["headers"]
    )
    assert left.status_code == 200, left.text
    return left.json()


async def card_of(client, player: dict) -> dict:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    [card] = read.json()["games"]
    return card


async def details_of(client, player: dict, booking_id: str) -> dict:
    read = await client.get(f"/api/v1/bookings/{booking_id}", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def receipts_of(client, mailbox, player: dict) -> list[dict]:
    # The money follows the commit: the outbox moves it first.
    await mailbox.drain()
    read = await client.get(RECEIPTS, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["receipts"]


def kinds_of(receipts: list[dict]) -> list[str]:
    """Each receipt's kind — a share let go untaken is *held · released*
    (#641): nothing was taken, and the hold the bank app showed is explained."""

    return [receipt["kind"] for receipt in receipts]


async def money_of(client, desk: dict) -> dict:
    read = await client.get(MONEY, params={"month": "2026-10"}, headers=desk)
    assert read.status_code == 200, read.text
    return read.json()


async def the_club_row(client, desk: dict, booking_id: str) -> dict:
    read = await client.get(BOOKINGS, params={"date": "2026-10-10"}, headers=desk)
    assert read.status_code == 200, read.text
    [row] = [row for row in read.json()["bookings"] if row["booking_id"] == booking_id]
    return row


def calls(payments, name: str) -> int:
    return len(payments.called(name))


# --------------------------------------------------------------------------- #
# The fill holds
# --------------------------------------------------------------------------- #


async def test_a_filled_game_holds_every_share_and_takes_nothing_until_the_cut_off(
    client, session_factory, clock, club, four, payments, mailbox
):
    booking = await a_booked_game(client, session_factory, clock, club[0], four)
    await mailbox.drain()

    assert calls(payments, "authorise") == 4
    assert calls(payments, "capture") == 0
    assert calls(payments, "cancel") == 0
    card = await card_of(client, four[0])
    assert card["status"] == "BOOKED"
    assert card["money"] == {
        "share_grosze": SHARE,
        "paid": False,
        "share_state": "HELD",
        "held_from": None,
        "taken_at": CUT_OFF_ON_THE_WIRE,
        "free_to_leave_until": CUT_OFF_ON_THE_WIRE,
        "refunded_grosze": None,
    }
    assert (await details_of(client, four[0], booking))["money"] == card["money"]
    assert await receipts_of(client, mailbox, four[0]) == []
    row = await the_club_row(client, club[1], booking)
    assert [(p["paid"], p["held"]) for p in row["players"]] == [(False, True)] * 4
    assert row["money"]["collected_grosze"] == 0


async def test_the_booking_email_says_the_share_is_held_and_when_it_is_taken(
    client, session_factory, clock, club, four, mailbox
):
    await a_booked_game(client, session_factory, clock, club[0], four)

    [booked] = [
        sent
        for sent in await mailbox.to("ola@example.com")
        if sent.subject.startswith("It's a game!")
    ]

    assert booked.subject == "It's a game! · 30 zł held"
    assert (
        "30 zł is held on your card and taken on Fri 17:00, the club's cut-off. "
        "Leave before then and nothing is taken."
    ) in booked.text
    assert "you paid" not in booked.text.lower()


# --------------------------------------------------------------------------- #
# The cut-off takes
# --------------------------------------------------------------------------- #


async def test_the_cut_off_takes_every_held_share_and_collected_moves_then(
    client, session_factory, clock, club, four, payments, mailbox
):
    booking = await a_booked_game(client, session_factory, clock, club[0], four)
    await mailbox.drain()
    assert (await money_of(client, club[1]))["totals"]["collected_grosze"] == 0

    clock.move(CUT_OFF - MONDAY_MORNING)
    run = await cuts_off(session_factory, clock)
    await mailbox.drain()

    assert (run.taken, run.games, run.conflicts) == (1, 0, 0)
    assert calls(payments, "capture") == 4
    card = await card_of(client, four[0])
    assert (card["money"]["paid"], card["money"]["share_state"]) == (True, "TAKEN")
    assert card["money"]["taken_at"] == CUT_OFF_ON_THE_WIRE
    assert card["money"]["free_to_leave_until"] is None
    [receipt] = await receipts_of(client, mailbox, four[0])
    assert (receipt["kind"], receipt["amount_grosze"]) == ("CHARGE", SHARE)
    assert (await money_of(client, club[1]))["totals"]["collected_grosze"] == 4 * SHARE
    row = await the_club_row(client, club[1], booking)
    assert [(p["paid"], p["held"]) for p in row["players"]] == [(True, False)] * 4
    again = await cuts_off(session_factory, clock)
    assert (again.taken, again.games) == (0, 0)


async def test_nothing_is_taken_before_the_cut_off(
    client, session_factory, clock, club, four, payments, mailbox
):
    await a_booked_game(client, session_factory, clock, club[0], four)
    clock.move(CUT_OFF - MONDAY_MORNING - timedelta(minutes=1))

    run = await cuts_off(session_factory, clock)
    await mailbox.drain()

    assert run.taken == 0
    assert calls(payments, "capture") == 0


async def test_a_game_short_at_its_cut_off_lets_every_hold_go_and_nobody_pays(
    client, session_factory, clock, club, four, payments, mailbox
):
    ola, kuba, ewa, tomek = four
    booking = await a_booked_game(client, session_factory, clock, club[0], four)
    await leaves(client, kuba, booking)
    await mailbox.drain()
    clock.move(CUT_OFF - MONDAY_MORNING)

    run = await cuts_off(session_factory, clock)
    await mailbox.drain()

    assert (run.games, run.taken) == (1, 0)
    assert calls(payments, "cancel") == 4
    assert calls(payments, "capture") == 0
    assert calls(payments, "refund") == 0
    card = await card_of(client, ola)
    assert (card["status"], card["called_off_reason"]) == (
        "CALLED_OFF",
        "SHORT_AT_THE_CUT_OFF",
    )
    assert card["money"]["paid"] is False
    assert card["money"]["share_state"] is None
    assert card["money"]["refunded_grosze"] is None
    for player in four:
        assert kinds_of(await receipts_of(client, mailbox, player)) == ["RELEASED"]
    [called_off] = [
        sent
        for sent in await mailbox.to("ola@example.com")
        if sent.subject.startswith("Game called off")
    ]
    assert called_off.subject == "Game called off · nothing was taken"
    assert "refund" not in called_off.text.lower()
    told = await client.get("/api/v1/players/me/notices", headers=ewa["headers"])
    assert "Game called off · nothing was taken" in [
        notice["title"] for notice in told.json()["notices"]
    ]
    assert (await money_of(client, club[1]))["totals"]["card_fees_grosze"] == 0


# --------------------------------------------------------------------------- #
# Leaving
# --------------------------------------------------------------------------- #


async def test_leaving_before_the_cut_off_takes_nothing(
    client, session_factory, clock, club, four, payments, mailbox
):
    ola, kuba, *_ = four
    booking = await a_booked_game(client, session_factory, clock, club[0], four)
    await mailbox.drain()

    left = await leaves(client, kuba, booking)
    await mailbox.drain()

    assert left["left"] == "BEFORE_THE_CUT_OFF"
    [cancelled] = payments.called("cancel")
    assert calls(payments, "refund") == 0
    assert calls(payments, "capture") == 0
    assert kinds_of(await receipts_of(client, mailbox, kuba)) == ["RELEASED"]
    [email] = [
        sent
        for sent in await mailbox.to("kuba@example.com")
        if sent.subject.startswith("You left the game")
    ]
    assert email.subject == "You left the game · nothing was taken"
    assert "The 30 zł hold on your card is let go." in email.text
    assert "refund" not in email.text.lower()
    card = await card_of(client, ola)
    assert (card["status"], card["money"]["share_state"]) == ("SEAT_OPEN", "HELD")


async def test_the_leave_quote_is_null_before_the_cut_off(
    client, session_factory, clock, club, four, mailbox
):
    booking = await a_booked_game(client, session_factory, clock, club[0], four)

    before = (await details_of(client, four[0], booking))["leaving"]
    clock.move(CUT_OFF - MONDAY_MORNING)
    still_held = (await details_of(client, four[0], booking))["leaving"]
    await cuts_off(session_factory, clock)
    await mailbox.drain()
    taken = (await details_of(client, four[0], booking))["leaving"]

    assert before == {
        "kind": "BEFORE_THE_CUT_OFF",
        "refund_grosze": None,
        "card_fee_grosze": None,
    }
    # The cut-off has come and the job has not taken the share yet: nothing
    # was kept on a payment not taken, so there is no figure (#641).
    assert still_held == {
        "kind": "AFTER_THE_CUT_OFF",
        "refund_grosze": None,
        "card_fee_grosze": None,
    }
    assert taken["kind"] == "AFTER_THE_CUT_OFF"
    assert taken["refund_grosze"] is not None


async def test_a_leaver_after_the_cut_off_has_their_share_taken_with_the_rest(
    client, session_factory, clock, club, four, payments, mailbox
):
    """The seat stays paid: leaving after the cut-off — before the job has run
    — lets nothing go, and the cut-off takes it with everybody's."""

    kuba = four[1]
    booking = await a_booked_game(client, session_factory, clock, club[0], four)
    clock.move(CUT_OFF - MONDAY_MORNING + timedelta(minutes=1))

    left = await leaves(client, kuba, booking)
    await cuts_off(session_factory, clock)
    await mailbox.drain()

    assert left["left"] == "AFTER_THE_CUT_OFF"
    assert calls(payments, "cancel") == 0
    assert calls(payments, "capture") == 4
    [receipt] = await receipts_of(client, mailbox, kuba)
    assert receipt["kind"] == "CHARGE"


# --------------------------------------------------------------------------- #
# The club cancels
# --------------------------------------------------------------------------- #


async def cancels(client, desk: dict, booking_id: str) -> None:
    cancelled = await client.post(
        f"{BOOKINGS}/{booking_id}/cancellation",
        json={"reason": "WEATHER"},
        headers=desk,
    )
    assert cancelled.status_code == 204, cancelled.text


async def test_a_club_cancelling_before_the_cut_off_lets_every_hold_go(
    client, session_factory, clock, club, four, payments, mailbox
):
    booking = await a_booked_game(client, session_factory, clock, club[0], four)
    await mailbox.drain()

    await cancels(client, club[1], booking)
    await mailbox.drain()

    assert calls(payments, "cancel") == 4
    assert calls(payments, "refund") == 0
    card = await card_of(client, four[0])
    assert card["called_off_reason"] == "CANCELLED_BY_THE_CLUB"
    assert card["money"]["refunded_grosze"] is None
    assert kinds_of(await receipts_of(client, mailbox, four[0])) == ["RELEASED"]
    [email] = [
        sent
        for sent in await mailbox.to("ola@example.com")
        if sent.subject.startswith("Game cancelled")
    ]
    assert email.subject == "Game cancelled by Bonarka Arena · nothing was taken"
    assert "refund" not in email.text.lower()
    money = await money_of(client, club[1])
    assert (money["totals"]["collected_grosze"], money["totals"]["net_grosze"]) == (
        0,
        0,
    )


async def test_a_club_cancelling_after_the_cut_off_refunds_everybody_in_full(
    client, session_factory, clock, club, four, payments, mailbox
):
    booking = await a_booked_game(client, session_factory, clock, club[0], four)
    clock.move(CUT_OFF - MONDAY_MORNING)
    await cuts_off(session_factory, clock)
    await mailbox.drain()

    await cancels(client, club[1], booking)
    await mailbox.drain()

    assert calls(payments, "cancel") == 0
    assert [call.arguments["amount_grosze"] for call in payments.called("refund")] == [
        SHARE
    ] * 4
    card = await card_of(client, four[0])
    assert card["money"]["refunded_grosze"] == SHARE
    refund, charge = await receipts_of(client, mailbox, four[0])
    assert (refund["kind"], refund["amount_grosze"]) == ("REFUND", SHARE)
    [email] = [
        sent
        for sent in await mailbox.to("ola@example.com")
        if sent.subject.startswith("Game cancelled")
    ]
    assert email.subject == "Game cancelled by Bonarka Arena · you're refunded 30 zł"


# --------------------------------------------------------------------------- #
# After the cut-off, money is taken at once
# --------------------------------------------------------------------------- #


async def test_a_game_filling_after_its_cut_off_is_taken_at_once(
    client, session_factory, clock, club, four, payments, mailbox
):
    clock.move(CUT_OFF - MONDAY_MORNING + timedelta(hours=1))

    await a_booked_game(client, session_factory, clock, club[0], four)
    await mailbox.drain()

    assert calls(payments, "capture") == 4
    card = await card_of(client, four[0])
    assert (card["money"]["paid"], card["money"]["share_state"]) == (True, "TAKEN")
    assert card["money"]["free_to_leave_until"] is None
    [receipt] = await receipts_of(client, mailbox, four[0])
    assert receipt["kind"] == "CHARGE"
    [booked] = [
        sent
        for sent in await mailbox.to("ola@example.com")
        if sent.subject.startswith("It's a game!")
    ]
    assert booked.subject == "It's a game! · you paid 30 zł"

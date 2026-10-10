"""**The club sees its money, and is paid after the game** (#548; the mechanics
§12.6, §16.11, §16.12; the screens B7, B9).

The desk reads a **month** of its Raketa money, booking by booking — what the
players paid, what was given back, the card fees, and what is the club's — and
the **payouts** that carried it to its bank. **Nothing is paid out before the
game is played**: the club's money waits on its account, where a refund before
the start can still come out of it, and is released at the close of the day it
was played on — once a day, in one payout — and the desk is emailed *A payout
was sent*. And once a day the desk is emailed the bookings it took that day.

Every act is taken as the website, the phone and the jobs take it, against the
fake payment provider; every claim is read where somebody would read it.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena, padel at 120 zł — 30 zł a seat
— with a 24-hour cut-off. The card fee on a 30 zł share is 1,45 zł (1.5 % and
1 zł), so a game played whole leaves the club 114,20 zł.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import (
    build_decide_club_payouts,
    build_summarise_new_bookings,
)
from app.core.config import get_settings
from app.modules.payments.domain.entered_cards import A_CARD
from app.modules.payments.domain.provider import PayoutStatus
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_and_its_desk,
    a_group,
    a_player,
    makes,
    says_yes,
    the_cut_off_comes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

MONEY = "/api/v1/club/money"
PAYOUTS = "/api/v1/club/payouts"
DESK_EMAIL = "desk@bonarka.pl"
BOOKINGS = "/api/v1/club/bookings"
SHARE = 30_00
#: The card fee on one 30 zł share: 1.5 % and 1 zł.
FEE = 1_45


@pytest.fixture
def clock(app, payments):
    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    # The provider dates a payout's arrival off the same clock.
    payments.clock = fixed
    return fixed


@pytest.fixture
async def club(client) -> tuple[str, dict]:
    return await a_club_and_its_desk(client, way="INSTANT")


#: The four pay by Mastercard, whose hold lasts seven days: a payout test lets
#: a capture wait until the game's evening, and a Visa held on Monday morning
#: lapses on Saturday at 02:00 (ADR-0190's 2026-10-10 amendment).
MASTERCARD = replace(A_CARD, brand="mastercard", last_four="4444")


@pytest.fixture
async def four(client, payments) -> list[dict]:
    return [
        await a_player(client, payments, name, entered=MASTERCARD)
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


async def money_of(client, desk: dict, month: str | None = None) -> dict:
    read = await client.get(
        MONEY, params={} if month is None else {"month": month}, headers=desk
    )
    assert read.status_code == 200, read.text
    return read.json()


async def pays_out(session_factory, clock, mailbox):
    """One run of the payouts job, at the clock's now — it decides — and the
    outbox after it, which makes each payout decided at the provider and emails
    the desk."""

    async with session_factory() as session:
        decided = await build_decide_club_payouts(
            session, clock=clock, settings=get_settings()
        ).execute()
    await mailbox.drain()
    return decided


async def payouts_of(client, desk: dict) -> list[dict]:
    read = await client.get(PAYOUTS, headers=desk)
    assert read.status_code == 200, read.text
    return read.json()["payouts"]


def at(day: int, hour: int, minute: int = 0):
    return warsaw(day, hour) + timedelta(minutes=minute)


async def leaves(client, player: dict, booking_id: str):
    left = await client.post(
        f"/api/v1/bookings/{booking_id}/departure", headers=player["headers"]
    )
    assert left.status_code == 200, left.text


# --------------------------------------------------------------------------- #
# Money
# --------------------------------------------------------------------------- #


async def test_the_club_reads_a_month_of_its_money_booking_by_booking(
    client, session_factory, clock, club, booking, four, mailbox
):
    _, desk = club
    await mailbox.drain()
    # Held until the cut-off, nothing is collected yet (#637).
    assert (await money_of(client, desk, "2026-10"))["bookings"] == []
    await the_cut_off_comes(session_factory, clock)
    # Kuba leaves after the cut-off: his seat stays paid.
    await leaves(client, four[1], booking)
    await mailbox.drain()

    money = await money_of(client, desk, "2026-10")

    assert money["month"] == "2026-10"
    [row] = money["bookings"]
    assert row["booking_id"] == booking
    assert row["starts_at"].startswith("2026-10-10T15:00:00")
    assert (row["court_name"], row["sport"]) == ("Court 1", "PADEL")
    assert row["collected_grosze"] == 4 * SHARE
    assert row["refunded_grosze"] == 0
    assert row["card_fees_grosze"] == 4 * FEE
    # 120 zł, less 5,80 zł of card fees.
    assert row["net_grosze"] == 114_20
    assert row["paid_out"] is False
    assert money["totals"] == {
        "collected_grosze": 120_00,
        "refunded_grosze": 0,
        "card_fees_grosze": 5_80,
        "net_grosze": 114_20,
    }
    november = await money_of(client, desk, "2026-11")
    assert november["bookings"] == []
    assert november["totals"] == {
        "collected_grosze": 0,
        "refunded_grosze": 0,
        "card_fees_grosze": 0,
        "net_grosze": 0,
    }


# --------------------------------------------------------------------------- #
# Payouts
# --------------------------------------------------------------------------- #


async def test_the_club_is_paid_a_day_s_games_once_the_day_closes(
    client, session_factory, clock, club, booking, payments, mailbox
):
    _, desk = club
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()
    # The last Raketa hour of Saturday has ended.
    clock.at = at(10, 23)

    await pays_out(session_factory, clock, mailbox)
    await pays_out(session_factory, clock, mailbox)

    [sent] = payments.called("pay_out")
    assert sent.arguments["amount_grosze"] == 114_20
    [payout] = await payouts_of(client, desk)
    assert payout["amount_grosze"] == 114_20
    assert payout["status"] in (PayoutStatus.PENDING, PayoutStatus.IN_TRANSIT)
    [row] = (await money_of(client, desk, "2026-10"))["bookings"]
    assert row["paid_out"] is True
    [email] = [one for one in await mailbox.to(DESK_EMAIL) if "payout" in one.subject]
    assert email.subject == "A payout was sent"
    assert "114,20 zł" in email.text


async def test_nothing_is_paid_out_before_the_day_of_the_game_closes(
    client, session_factory, clock, club, booking, payments, mailbox
):
    _, desk = club
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()

    clock.at = at(10, 17, 30)  # playing
    await pays_out(session_factory, clock, mailbox)
    clock.at = at(10, 22, 59)  # played, and the day's last hour still on
    await pays_out(session_factory, clock, mailbox)

    assert payments.called("pay_out") == []
    assert await payouts_of(client, desk) == []
    [row] = (await money_of(client, desk, "2026-10"))["bookings"]
    assert row["paid_out"] is False


async def test_a_payout_waits_for_the_money_still_on_its_way(
    client, session_factory, clock, club, booking, payments, mailbox
):
    """The shares were taken at the cut-off and are captured from the outbox:
    until every one is, the game's money is not the club's to be paid — the
    same for a refund decided and not yet made."""

    await mailbox.drain()
    await the_cut_off_comes(session_factory, clock)
    clock.at = at(10, 23)

    await pays_out(session_factory, clock, mailbox)
    assert payments.called("pay_out") == []

    await mailbox.drain()
    await pays_out(session_factory, clock, mailbox)

    [sent] = payments.called("pay_out")
    assert sent.arguments["amount_grosze"] == 114_20


async def test_a_day_that_cost_the_club_is_netted_against_the_next_one_paid(
    client, session_factory, clock, club, group, booking, four, payments, mailbox
):
    """The club cancels Saturday's game after its cut-off took the shares:
    everybody is given back whole, and its card fees are the club's — 5,80 zł
    it is owed nothing for. Sunday's game is played whole, and Sunday's payout
    carries both: 114,20 zł less 5,80 zł."""

    club_id, desk = club
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()
    cancelled = await client.post(
        f"{BOOKINGS}/{booking}/cancellation", json={"reason": "WEATHER"}, headers=desk
    )
    assert cancelled.status_code == 204, cancelled.text
    sunday = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club_id,
        start=warsaw(11, 17),
        versions=(tuple(four),),
    )
    for player in four:
        assert (await says_yes(client, player, sunday)).status_code == 200
    await mailbox.drain()

    clock.at = at(10, 23)
    # Sunday's cut-off has come too: its shares are taken.
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()
    await pays_out(session_factory, clock, mailbox)
    assert payments.called("pay_out") == []

    clock.at = at(11, 23)
    await pays_out(session_factory, clock, mailbox)

    [sent] = payments.called("pay_out")
    assert sent.arguments["amount_grosze"] == 108_40
    money = await money_of(client, desk, "2026-10")
    assert [row["net_grosze"] for row in money["bookings"]] == [-5_80, 114_20]
    assert all(row["paid_out"] for row in money["bookings"])


async def test_a_game_short_at_its_cut_off_is_not_paid_out_before_its_refunds(
    client, session_factory, clock, club, booking, four, payments, mailbox
):
    """Kuba left and nobody took his seat, so the game was off from its
    cut-off — but until the cut-off job lets the others' holds go, their
    shares are still held, not settled, and none of it is the club's; and it
    took nothing, so the Money page lists nothing for it (#637)."""

    _, desk = club
    await leaves(client, four[1], booking)
    await mailbox.drain()
    clock.at = at(10, 23)

    await pays_out(session_factory, clock, mailbox)

    assert payments.called("pay_out") == []
    assert (await money_of(client, desk, "2026-10"))["bookings"] == []


async def test_a_payout_the_provider_cannot_take_yet_is_made_by_a_later_delivery(
    client, session_factory, clock, club, booking, payments, mailbox
):
    """The decision is recorded whatever the provider says; the payout is made
    from the outbox once the provider takes it — once, and told once."""

    _, desk = club
    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()
    clock.at = at(10, 23)
    payments.unreachable = True

    await pays_out(session_factory, clock, mailbox)

    told = await mailbox.to(DESK_EMAIL)
    assert [one for one in told if "payout" in one.subject] == []
    payments.unreachable = False
    assert await payouts_of(client, desk) == []
    [row] = (await money_of(client, desk, "2026-10"))["bookings"]
    assert row["paid_out"] is False

    clock.move(timedelta(minutes=5))
    await pays_out(session_factory, clock, mailbox)
    await pays_out(session_factory, clock, mailbox)

    [payout] = await payouts_of(client, desk)
    assert payout["amount_grosze"] == 114_20
    sent = [one for one in await mailbox.to(DESK_EMAIL) if "payout" in one.subject]
    assert len(sent) == 1


# --------------------------------------------------------------------------- #
# The day's new bookings
# --------------------------------------------------------------------------- #


async def summarises(session_factory, clock):
    """One run of the new-bookings summary job, at the clock's now."""

    async with session_factory() as session:
        return await build_summarise_new_bookings(
            session, clock=clock, settings=get_settings()
        ).execute()


async def summaries_to_the_desk(mailbox) -> list:
    return [
        one
        for one in await mailbox.to(DESK_EMAIL)
        if one.subject == "New bookings today"
    ]


async def test_the_desk_is_emailed_the_day_s_new_bookings_once_the_day_closes(
    session_factory, clock, booking, mailbox
):
    """The four booked Saturday's game on Monday morning: Monday's summary,
    sent at its close, names it — once — and Tuesday, when nothing was booked,
    sends none."""

    clock.at = at(5, 22, 59)
    await summarises(session_factory, clock)
    assert await summaries_to_the_desk(mailbox) == []

    clock.at = at(5, 23)
    await summarises(session_factory, clock)
    await summarises(session_factory, clock)

    [summary] = await summaries_to_the_desk(mailbox)
    assert "Monday 5 October" in summary.text
    assert "Saturday 10 October, 17:00 · Court 1 · Padel · 120 zł" in summary.text

    clock.at = at(6, 23)
    await summarises(session_factory, clock)
    assert len(await summaries_to_the_desk(mailbox)) == 1

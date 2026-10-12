"""**A game that fills far ahead is checked at the fill, and its shares held
four days before the cut-off** (#639; the mechanics Q113, §12.2; ADR-0189's
2026-10-10 amendment).

A card hold made without its player lasts 4 days 18 hours on a Visa and 7 days
on a Mastercard. Thursday 15 October's 19:00 fills a week ahead, on Thursday 8
October at 19:00, its cut-off Wednesday 14 October at 19:00:

- **Thursday, at the fill**, Ivan's Visa hold would not last until Wednesday,
  so it is a **Card check** — held and let go at once. Oscar's Mastercard hold
  reaches Wednesday and simply stays.
- **Saturday 19:00, the holding time**, Ivan's 40 zł is held again, and stays.
- **Any time before Wednesday 19:00**, anyone can leave and nothing is taken.

A holding the card refuses gives Ivan **time to fix the card** on the booked
game — fixed in time, the share is held; run out, his seat opens to Fill in
and he owes nothing. And **the fallback**: a holding whose hold would still
not reach the cut-off is taken at its last safe moment, which only a test's
stand-in can make happen.

Every act is taken over HTTP as the phone takes it, against the fake payment
provider on the test's clock; the holding, time-to-pay and cut-off jobs run as
the jobs do, the clock moved to them; and every claim is read where somebody
would read it — Home, the details, the To confirm rows, the receipts, the
mailbox, the notices, Fill in, and the calls made to the provider.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_the_holding
from app.core.config import get_settings
from app.modules.payments.domain.entered_cards import A_CARD, CardBehaviour
from tests.api.proposals_world import (
    a_club_and_its_desk,
    a_group,
    a_member,
    makes,
    runs_out,
    says_yes,
    the_cut_off_comes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

HOME = "/api/v1/home"
RECEIPTS = "/api/v1/players/me/receipts"
NOTICES = "/api/v1/players/me/notices"
TO_CONFIRM = "/api/v1/players/me/payments-to-confirm"
SHARE = 40_00

#: Thursday 8 October, 19:00 in Kraków: the last yes, a week ahead.
THE_FILL = warsaw(8, 19)
#: Thursday 15 October, 19:00: the game.
THE_GAME = warsaw(15, 19)
#: Wednesday 14 October, 19:00: its cut-off, a day before.
THE_CUT_OFF = warsaw(14, 19)
#: Saturday 10 October, 19:00: the holding time, four days before it.
THE_HOLDING = warsaw(10, 19)

#: The same moments on the wire.
CUT_OFF_ON_THE_WIRE = "2026-10-14T17:00:00Z"
HOLDING_ON_THE_WIRE = "2026-10-10T17:00:00Z"
#: Thirty minutes from the holding: Saturday 19:30.
FIX_BY_ON_THE_WIRE = "2026-10-10T17:30:00Z"

#: Oscar's, Marta's and Paula's card: a Mastercard, whose hold lasts 7 days.
A_MASTERCARD = replace(A_CARD, brand="mastercard", last_four="4444")


@pytest.fixture
def clock(app, payments):
    """Thursday 8 October 2026, 19:00 in Kraków — and the provider's clock, so
    a hold says when it ends and lapses after it."""

    fixed = MovableClock(THE_FILL)
    app.dependency_overrides[get_clock] = lambda: fixed
    payments.clock = fixed
    return fixed


@pytest.fixture
async def club(client) -> tuple[str, dict]:
    """Bonarka Arena: padel at 160 zł — 40 zł a seat — and a 24-hour
    cut-off."""

    return await a_club_and_its_desk(client, padel_grosze=160_00)


@pytest.fixture
async def four(client, session_factory, payments) -> dict[str, dict]:
    """Ivan pays by his Visa; Oscar, Marta and Paula by Mastercards — Diego,
    in the group too, is free to take a seat."""

    people = {
        "ivan": await a_member(client, session_factory, payments, "ivan"),
        **{
            name: await a_member(
                client, session_factory, payments, name, entered=A_MASTERCARD
            )
            for name in ("oscar", "marta", "paula")
        },
    }
    people["diego"] = await a_member(client, session_factory, payments, "diego")
    return people


async def fills(client, session_factory, clock, club: str, people: dict) -> str:
    """Thursday 15 October's 19:00, made and filled now, Ivan's yes the last.
    Its booking."""

    four = [people[name] for name in ("oscar", "marta", "paula", "ivan")]
    group = await a_group(client, four[0], club, *four[1:], people["diego"])
    people["group"] = group
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=THE_GAME,
        versions=(tuple(four),),
    )
    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    assert last.json()["booked"] is not None, last.text
    return last.json()["booked"]["booking_id"]


async def holds(session_factory, clock, payments, *, at=THE_HOLDING):
    """The clock moved to ``at`` — the holding time, unless it says another —
    and the holding job run then."""

    if clock.now() < at:
        clock.move(at - clock.now())
    async with session_factory() as session:
        return await build_the_holding(
            session, clock=clock, provider=payments, settings=get_settings()
        ).execute()


async def card_of(client, player: dict) -> dict:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    [card] = read.json()["games"]
    return card


async def details_of(client, player: dict, booking: str) -> dict:
    read = await client.get(f"/api/v1/bookings/{booking}", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def receipts_of(client, mailbox, player: dict) -> list[dict]:
    await mailbox.drain()
    read = await client.get(RECEIPTS, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["receipts"]


async def to_confirm(client, player: dict) -> list[dict]:
    read = await client.get(TO_CONFIRM, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["payments"]


async def told(client, mailbox, player: dict) -> list[str]:
    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return [notice["title"] for notice in read.json()["notices"]]


async def subjects_to(mailbox, name: str) -> list[str]:
    return [email.subject for email in await mailbox.to(f"{name}@example.com")]


async def leaves(client, player: dict, booking: str) -> None:
    left = await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=player["headers"]
    )
    assert left.status_code == 200, left.text


def ivan_s_card(payments, ivan: dict) -> str:
    """The card Ivan saved, as the fake knows it — cloned for his seat."""

    [method] = {
        call.arguments["method_id"]
        for call in payments.called("clone_method")
        if str(ivan["id"]) in call.arguments["key"]
    }
    return method


def holds_asked(payments) -> list[str]:
    """Whose share each hold asked the provider for, in order."""

    return [
        call.arguments["metadata"]["player_id"] for call in payments.called("authorise")
    ]


async def his_refused_holding(
    client, session_factory, clock, payments, mailbox, club, four
):
    """The game booked a week ahead, and Ivan's bank wanting him present at the
    holding: his card refused there. The booking."""

    booking = await fills(client, session_factory, clock, club[0], four)
    await mailbox.drain()
    payments.card_behaves(
        ivan_s_card(payments, four["ivan"]), CardBehaviour.CHECKED_EVERY_TIME
    )
    held = await holds(session_factory, clock, payments)
    assert held.refused == 1, held
    return booking


async def confirms(client, payments, player: dict, charge_id: str):
    """The phone passes the bank's check and says so."""

    read = await client.get(
        f"/api/v1/seat-charges/{charge_id}", headers=player["headers"]
    )
    assert read.status_code == 200, read.text
    secret = read.json()["to_confirm"]["client_secret"]
    payments.phone_confirms_payment(secret.split("_secret_")[0])
    return await client.post(
        f"/api/v1/seat-charges/{charge_id}/confirmation", headers=player["headers"]
    )


# --------------------------------------------------------------------------- #
# The fill: a Visa checked, a Mastercard held
# --------------------------------------------------------------------------- #


async def test_a_week_ahead_fill_checks_a_visa_seat_and_holds_a_mastercard_one(
    client, session_factory, clock, payments, mailbox, club, four
):
    booking = await fills(client, session_factory, clock, club[0], four)
    await mailbox.drain()

    # Every seat held, all or nothing — and Ivan's let go at once: a check.
    assert len(payments.called("authorise")) == 4
    [cancelled] = payments.called("cancel")
    assert cancelled.arguments["key"].startswith("raketa-cancel-check-")
    assert payments.called("capture") == []
    ivan = await card_of(client, four["ivan"])
    assert ivan["status"] == "BOOKED"
    assert ivan["money"] == {
        "share_grosze": SHARE,
        "paid": False,
        "share_state": "CHECKED",
        "held_from": HOLDING_ON_THE_WIRE,
        "taken_at": CUT_OFF_ON_THE_WIRE,
        "free_to_leave_until": CUT_OFF_ON_THE_WIRE,
        "refunded_grosze": None,
    }
    assert (await details_of(client, four["ivan"], booking))["money"] == ivan["money"]
    oscar = await card_of(client, four["oscar"])
    assert oscar["money"]["share_state"] == "HELD"
    assert oscar["money"]["held_from"] is None
    assert oscar["money"]["free_to_leave_until"] == CUT_OFF_ON_THE_WIRE
    # A check is never a receipt.
    assert await receipts_of(client, mailbox, four["ivan"]) == []


async def test_the_booking_email_tells_a_checked_seat_when_it_is_held_and_taken(
    client, session_factory, clock, payments, mailbox, club, four
):
    await fills(client, session_factory, clock, club[0], four)
    await mailbox.drain()

    [ivan_s] = [
        sent
        for sent in await mailbox.to("ivan@example.com")
        if sent.subject.startswith("It's a game!")
    ]
    assert (
        "Your card was checked. 40 zł will be held from Sat 19:00 and taken on "
        "Wed 19:00, the club's cut-off. Leave before then and nothing is taken."
    ) in ivan_s.text
    [oscar_s] = [
        sent
        for sent in await mailbox.to("oscar@example.com")
        if sent.subject.startswith("It's a game!")
    ]
    assert "40 zł is held on your card and taken on Wed 19:00" in oscar_s.text


# --------------------------------------------------------------------------- #
# The holding, and the cut-off
# --------------------------------------------------------------------------- #


async def test_the_holding_job_holds_the_checked_share_on_saturday(
    client, session_factory, clock, payments, mailbox, club, four
):
    await fills(client, session_factory, clock, club[0], four)
    await mailbox.drain()

    early = await holds(
        session_factory, clock, payments, at=THE_HOLDING - timedelta(minutes=1)
    )
    assert (early.held, early.refused) == (0, 0)
    assert len(payments.called("authorise")) == 4

    held = await holds(session_factory, clock, payments)

    assert (held.held, held.refused) == (1, 0)
    assert holds_asked(payments)[-1] == str(four["ivan"]["id"])
    money = (await card_of(client, four["ivan"]))["money"]
    assert money["share_state"] == "HELD"
    assert money["held_from"] is None
    assert money["free_to_leave_until"] == CUT_OFF_ON_THE_WIRE
    # Run again, it asks nothing more.
    again = await holds(session_factory, clock, payments)
    assert (again.held, again.refused) == (0, 0)
    assert len(payments.called("authorise")) == 5


async def test_the_cut_off_takes_the_share_held_at_the_holding(
    client, session_factory, clock, payments, mailbox, club, four
):
    await fills(client, session_factory, clock, club[0], four)
    await holds(session_factory, clock, payments)

    await the_cut_off_comes(session_factory, clock, at=THE_CUT_OFF)
    await mailbox.drain()

    assert len(payments.called("capture")) == 4
    [receipt] = await receipts_of(client, mailbox, four["ivan"])
    assert (receipt["kind"], receipt["amount_grosze"]) == ("CHARGE", SHARE)
    money = (await card_of(client, four["ivan"]))["money"]
    assert (money["paid"], money["share_state"]) == (True, "TAKEN")


async def test_a_leave_before_the_holding_takes_nothing_and_holds_nothing_later(
    client, session_factory, clock, payments, mailbox, club, four
):
    booking = await fills(client, session_factory, clock, club[0], four)
    await mailbox.drain()
    clock.move(timedelta(days=1))

    await leaves(client, four["ivan"], booking)
    await mailbox.drain()

    # Nothing was held, so nothing is let go, taken or refunded.
    assert len(payments.called("cancel")) == 1
    assert payments.called("refund") == []
    assert "You left the game · nothing was taken" in await subjects_to(mailbox, "ivan")
    held = await holds(session_factory, clock, payments)
    assert (held.held, held.refused) == (0, 0)
    assert len(payments.called("authorise")) == 4
    assert await receipts_of(client, mailbox, four["ivan"]) == []


# --------------------------------------------------------------------------- #
# A refused holding: time to fix the card
# --------------------------------------------------------------------------- #


async def test_a_refused_holding_gives_him_time_to_fix_the_card_on_the_booked_game(
    client, session_factory, clock, payments, mailbox, club, four
):
    booking = await his_refused_holding(
        client, session_factory, clock, payments, mailbox, club, four
    )

    ivan = await card_of(client, four["ivan"])
    # The game stays booked; his own line says fix your card, by when.
    assert ivan["status"] == "BOOKED"
    assert ivan["your_payment_due_by"] == FIX_BY_ON_THE_WIRE
    assert ivan["time_to"] == "FIX_THE_CARD"
    assert ivan["payment_due_by"] is None
    details = await details_of(client, four["ivan"], booking)
    assert details["your_payment_due_by"] == FIX_BY_ON_THE_WIRE
    [owed] = await to_confirm(client, four["ivan"])
    assert (owed["proposal_id"], owed["confirm_by"], owed["time_to"]) == (
        booking,
        FIX_BY_ON_THE_WIRE,
        "FIX_THE_CARD",
    )
    # Nobody else is asked anything, or told.
    oscar = await card_of(client, four["oscar"])
    assert (oscar["your_payment_due_by"], oscar["time_to"]) == (None, None)
    assert "Fix your card by 19:30 to keep your seat" in await told(
        client, mailbox, four["ivan"]
    )
    assert "Fix your card by 19:30 to keep your seat" in await subjects_to(
        mailbox, "ivan"
    )


async def test_a_refused_holding_fixed_in_time_is_held_and_taken_at_the_cut_off(
    client, session_factory, clock, payments, mailbox, club, four
):
    booking = await his_refused_holding(
        client, session_factory, clock, payments, mailbox, club, four
    )
    [owed] = await to_confirm(client, four["ivan"])
    clock.move(timedelta(minutes=10))

    fixed = await confirms(client, payments, four["ivan"], owed["seat_charge_id"])

    assert fixed.status_code == 200, fixed.text
    assert await to_confirm(client, four["ivan"]) == []
    ivan = await card_of(client, four["ivan"])
    assert (ivan["status"], ivan["your_payment_due_by"], ivan["time_to"]) == (
        "BOOKED",
        None,
        None,
    )
    assert ivan["money"]["share_state"] == "HELD"
    # The job finds nothing to run out.
    clock.move(timedelta(minutes=30))
    assert (await runs_out(session_factory, clock)).games == 0
    await the_cut_off_comes(session_factory, clock, at=THE_CUT_OFF)
    await mailbox.drain()
    assert len(payments.called("capture")) == 4
    assert (await details_of(client, four["ivan"], booking))["money"]["paid"] is True


async def test_a_refused_holding_that_runs_out_opens_his_seat_and_he_owes_nothing(
    client, session_factory, clock, payments, mailbox, club, four
):
    booking = await his_refused_holding(
        client, session_factory, clock, payments, mailbox, club, four
    )
    clock.move(timedelta(minutes=30))

    ran_out = await runs_out(session_factory, clock)

    assert ran_out.games == 1
    await mailbox.drain()
    # His seat is open — a Rescue, offered on Fill in — and the game his
    # three others'.
    oscar = await card_of(client, four["oscar"])
    assert (oscar["status"], oscar["open_seats"]) == ("SEAT_OPEN", 1)
    read = await client.get(
        f"/api/v1/pools/{four['group']}/fill-in",
        params={"sport": "PADEL"},
        headers=four["diego"]["headers"],
    )
    assert read.status_code == 200, read.text
    assert [row["booking_id"] for row in read.json()["seats_to_fill"]] == [booking]
    # He owes nothing: the refused payment let go, nothing taken or refunded.
    assert payments.called("capture") == []
    assert payments.called("refund") == []
    assert len(payments.called("cancel")) == 2
    assert await receipts_of(client, mailbox, four["ivan"]) == []
    assert await to_confirm(client, four["ivan"]) == []
    # He is told his time ran out, and the others somebody left.
    assert any(
        title.startswith("Your time to fix your card ran out")
        for title in await told(client, mailbox, four["ivan"])
    )
    assert any("left" in title for title in await told(client, mailbox, four["oscar"]))


async def test_his_confirmation_past_his_time_runs_it_out_first(
    client, session_factory, clock, payments, mailbox, club, four
):
    booking = await his_refused_holding(
        client, session_factory, clock, payments, mailbox, club, four
    )
    [owed] = await to_confirm(client, four["ivan"])
    clock.move(timedelta(minutes=31))

    late = await confirms(client, payments, four["ivan"], owed["seat_charge_id"])

    assert late.status_code in (404, 409), late.text
    oscar = await card_of(client, four["oscar"])
    assert (oscar["status"], oscar["open_seats"]) == ("SEAT_OPEN", 1)
    await mailbox.drain()
    assert payments.called("capture") == []
    assert (await details_of(client, four["oscar"], booking))["open_seats"] == 1


async def test_his_card_still_to_fix_lets_him_leave_owing_nothing(
    client, session_factory, clock, payments, mailbox, club, four
):
    booking = await his_refused_holding(
        client, session_factory, clock, payments, mailbox, club, four
    )
    clock.move(timedelta(minutes=10))

    await leaves(client, four["ivan"], booking)
    await mailbox.drain()

    # His refused holding is let go with his seat; his time no longer runs.
    assert len(payments.called("cancel")) == 2
    assert payments.called("capture") == []
    assert await to_confirm(client, four["ivan"]) == []
    oscar = await card_of(client, four["oscar"])
    assert (oscar["status"], oscar["open_seats"]) == ("SEAT_OPEN", 1)
    clock.move(timedelta(minutes=30))
    assert (await runs_out(session_factory, clock)).games == 0


async def test_a_club_cancel_while_his_card_is_to_fix_leaves_nothing_to_run_out(
    client, session_factory, clock, payments, mailbox, club, four
):
    """The club cancels the game during Ivan's time to fix the card: every
    share is let go, his refused holding with them, and the time-to-pay job
    finds nothing left to run out — on this game or any other."""

    booking = await his_refused_holding(
        client, session_factory, clock, payments, mailbox, club, four
    )
    clock.move(timedelta(minutes=10))
    cancelled = await client.post(
        f"/api/v1/club/bookings/{booking}/cancellation",
        json={"reason": "WEATHER"},
        headers=club[1],
    )
    assert cancelled.status_code == 200, cancelled.text
    # No other court takes it: called off (#672).
    assert cancelled.json()["outcome"] == "CALLED_OFF"
    await mailbox.drain()

    assert await to_confirm(client, four["ivan"]) == []
    ivan = await card_of(client, four["ivan"])
    assert (ivan["status"], ivan["your_payment_due_by"]) == ("CALLED_OFF", None)
    clock.move(timedelta(minutes=30))
    assert (await runs_out(session_factory, clock)).games == 0
    assert payments.called("capture") == []


async def test_a_club_cancel_of_a_checked_share_says_nothing_was_held(
    client, session_factory, clock, payments, mailbox, club, four
):
    booking = await fills(client, session_factory, clock, club[0], four)
    await mailbox.drain()

    cancelled = await client.post(
        f"/api/v1/club/bookings/{booking}/cancellation",
        json={"reason": "WEATHER"},
        headers=club[1],
    )
    assert cancelled.status_code == 200, cancelled.text
    # No other court takes it: called off (#672).
    assert cancelled.json()["outcome"] == "CALLED_OFF"
    await mailbox.drain()

    [ivan_s] = [
        sent
        for sent in await mailbox.to("ivan@example.com")
        if sent.subject.startswith("Game cancelled")
    ]
    assert "Nothing is held on your card for it" in ivan_s.text
    [oscar_s] = [
        sent
        for sent in await mailbox.to("oscar@example.com")
        if sent.subject.startswith("Game cancelled")
    ]
    assert "The 40 zł hold on your card is let go" in oscar_s.text
    # Nothing held, so nothing more to let go than the check was.
    assert len(payments.called("cancel")) == 1 + 3
    held = await holds(session_factory, clock, payments)
    assert (held.held, held.refused) == (0, 0)


# --------------------------------------------------------------------------- #
# The fallback
# --------------------------------------------------------------------------- #


async def test_a_holding_that_falls_short_is_taken_at_its_last_safe_moment(
    client, session_factory, clock, payments, mailbox, club, four
):
    """The stand-in made, for this test only, to hold a Visa for two days:
    even the holding falls short of the cut-off, so it is taken at its last
    safe moment — and a leave before the cut-off after that gets everything
    back."""

    payments.hold_windows["visa"] = timedelta(days=2)
    booking = await fills(client, session_factory, clock, club[0], four)
    await holds(session_factory, clock, payments)
    # Held on Saturday 19:00 until Monday 19:00: taken at Monday 13:00.
    last_safe = warsaw(12, 13)

    early = await the_cut_off_comes(
        session_factory, clock, at=last_safe - timedelta(minutes=1)
    )
    assert early.taken == 0
    taken = await the_cut_off_comes(session_factory, clock, at=last_safe)
    assert taken.taken == 1
    await mailbox.drain()
    [capture] = payments.called("capture")
    [receipt] = await receipts_of(client, mailbox, four["ivan"])
    assert receipt["kind"] == "CHARGE"

    clock.move(timedelta(days=1))
    await leaves(client, four["ivan"], booking)
    await mailbox.drain()

    [refund] = payments.called("refund")
    assert refund.arguments["payment_id"] == capture.arguments["payment_id"]
    assert refund.arguments["amount_grosze"] == SHARE


# --------------------------------------------------------------------------- #
# A rescue far ahead (#640)
# --------------------------------------------------------------------------- #


async def diego_takes_the_seat(client, four: dict, booking: str) -> dict:
    taken = await client.post(
        f"/api/v1/bookings/{booking}/seats", headers=four["diego"]["headers"]
    )
    assert taken.status_code == 200, taken.text
    assert taken.json()["booked"]["booking_id"] == booking
    return taken.json()


async def test_a_rescue_before_the_holding_time_is_checked_and_held_at_it(
    client, session_factory, clock, payments, mailbox, club, four
):
    """Diego takes Ivan's seat on Friday morning: his Visa's hold would not
    last until Wednesday, so his card is checked now, like the seats he joins,
    his share held at Saturday 19:00 with theirs and taken at the cut-off."""

    booking = await fills(client, session_factory, clock, club[0], four)
    clock.move(warsaw(9, 10) - clock.now())
    await leaves(client, four["ivan"], booking)

    answer = await diego_takes_the_seat(client, four, booking)

    money = answer["money"]
    assert (money["share_state"], money["held_from"]) == (
        "CHECKED",
        HOLDING_ON_THE_WIRE,
    )
    assert money["free_to_leave_until"] == CUT_OFF_ON_THE_WIRE
    assert (await card_of(client, four["diego"]))["money"] == money
    [email] = [
        sent
        for sent in await mailbox.to("diego@example.com")
        if sent.subject.startswith("It's a game!")
    ]
    assert "Your card was checked. 40 zł will be held from Sat 19:00" in email.text
    # Ivan left before the cut-off: nothing was taken, so nothing comes back.
    assert payments.called("refund") == []

    held = await holds(session_factory, clock, payments)

    assert (held.held, held.refused) == (1, 0)
    assert holds_asked(payments)[-1] == str(four["diego"]["id"])
    assert (await card_of(client, four["diego"]))["money"]["share_state"] == "HELD"
    await the_cut_off_comes(session_factory, clock, at=THE_CUT_OFF)
    [receipt] = await receipts_of(client, mailbox, four["diego"])
    assert (receipt["kind"], receipt["amount_grosze"]) == ("CHARGE", SHARE)


async def test_a_rescue_after_the_holding_time_is_held_until_the_cut_off(
    client, session_factory, clock, payments, mailbox, club, four
):
    booking = await fills(client, session_factory, clock, club[0], four)
    await holds(session_factory, clock, payments)
    clock.move(warsaw(12, 10) - clock.now())
    await leaves(client, four["ivan"], booking)
    await mailbox.drain()
    asked = len(payments.called("authorise"))
    cancelled = len(payments.called("cancel"))

    answer = await diego_takes_the_seat(client, four, booking)

    money = answer["money"]
    assert (money["share_state"], money["held_from"]) == ("HELD", None)
    assert money["taken_at"] == CUT_OFF_ON_THE_WIRE
    # Held once, and kept: no check to let go.
    await mailbox.drain()
    assert len(payments.called("authorise")) == asked + 1
    assert len(payments.called("cancel")) == cancelled
    assert (await holds(session_factory, clock, payments)).held == 0
    await the_cut_off_comes(session_factory, clock, at=THE_CUT_OFF)
    [receipt] = await receipts_of(client, mailbox, four["diego"])
    assert (receipt["kind"], receipt["amount_grosze"]) == ("CHARGE", SHARE)

"""**After the cut-off, a replaced leaver gets back the share less exactly what
was kept on their payment** (#641; the mechanics §12.3, §13, §17.2, Q113;
ADR-0190's 2026-10-10 amendment).

Ivan leaves Saturday's game an hour after the club's cut-off, and Diego takes
his seat. Ivan paid by his business Visa, on which 1,76 zł was kept, so he gets
**38,24 zł** back; on a personal EU card he would get 38,40 zł, on a card from
outside Europe 37,70 zł. The club neither earns nor loses on a late leave.
**Before he leaves, the details tell him that figure** — the money was taken at
the cut-off and the fee is known — and **no figure is ever an estimate**: while
the fee is not yet known (a club on its own negotiated pricing) there is no
figure and no clause, and the refund waits until it is known.

Every act is taken over HTTP as the phone takes it, against the fake payment
provider; the cut-off job runs as the job does; and every claim is read where
somebody would read it — the details, the receipts, the mailbox, the notices,
and the calls made to the provider.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena, padel at 160 zł — **40 zł a
seat** — with a 24-hour cut-off: **Friday 17:00**.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import timedelta
from uuid import UUID

import pytest
import stripe

from app.api.dependencies import get_clock
from app.core.config import get_settings
from app.modules.payments.domain.entered_cards import A_CARD, CardKind
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_group,
    a_member,
    makes,
    says_yes,
    the_cut_off_comes,
)
from tests.unit.fake_clock import MovableClock

SHARE = 40_00
CUT_OFF = SATURDAY_FIVE - timedelta(hours=24)
RECEIPTS = "/api/v1/players/me/receipts"
NOTICES = "/api/v1/players/me/notices"
IVAN = "ivan@example.com"
CONNECT_WEBHOOK = "/api/v1/webhooks/stripe-connect"
CONNECT_SECRET = "whsec_the_exact_refund_s_own"

#: What each kind of card keeps on a 40 zł share, and so what comes back.
KINDS = [
    pytest.param(CardKind.PERSONAL_EU, 38_40, 1_60, id="personal-eu"),
    pytest.param(CardKind.BUSINESS, 38_24, 1_76, id="business"),
    pytest.param(CardKind.OUTSIDE_EUROPE, 37_70, 2_30, id="outside-europe"),
]


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    """Bonarka Arena: one padel court at 160 zł, a 24-hour cut-off."""

    club_id, _desk = await a_club_and_its_desk(client, padel_grosze=160_00)
    return club_id


async def a_game_ivan_is_in(
    client, session_factory, payments, clock, club: str, *, kind: CardKind
) -> tuple[str, dict, dict]:
    """Ola, Ivan, Ewa and Tomek's game on Saturday at 17:00 — Ivan paying by a
    card of ``kind`` — and Diego, in their group, free to take a seat. The
    booking, Ivan and Diego."""

    ivan_s_card = replace(A_CARD, kind=kind)
    ola = await a_member(client, session_factory, payments, "ola")
    ivan = await a_member(
        client, session_factory, payments, "ivan", entered=ivan_s_card
    )
    ewa = await a_member(client, session_factory, payments, "ewa")
    tomek = await a_member(client, session_factory, payments, "tomek")
    diego = await a_member(client, session_factory, payments, "diego")
    four = (ola, ivan, ewa, tomek)
    group = await a_group(client, ola, club, ivan, ewa, tomek, diego)
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(four,)
    )
    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, tomek, proposal)
    assert last.status_code == 200, last.text
    return last.json()["booked"]["booking_id"], ivan, diego


async def the_cut_off_takes_the_shares(session_factory, clock, mailbox) -> None:
    """Friday 17:00: the job takes every share, and the outbox captures each —
    the provider saying the fee it kept."""

    await the_cut_off_comes(session_factory, clock)
    await mailbox.drain()


async def leaves(client, player: dict, booking_id: str) -> str:
    left = await client.post(
        f"/api/v1/bookings/{booking_id}/departure", headers=player["headers"]
    )
    assert left.status_code == 200, left.text
    return left.json()["left"]


async def joins(client, player: dict, booking_id: str) -> None:
    joined = await client.post(
        f"/api/v1/bookings/{booking_id}/seats", headers=player["headers"]
    )
    assert joined.status_code == 200, joined.text


async def leaving_of(client, player: dict, booking_id: str) -> dict | None:
    read = await client.get(f"/api/v1/bookings/{booking_id}", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["leaving"]


async def receipts_of(client, mailbox, player: dict) -> list[dict]:
    # The money follows the commit: the outbox moves it first.
    await mailbox.drain()
    read = await client.get(RECEIPTS, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["receipts"]


async def notices_of(client, mailbox, player: dict) -> list[dict]:
    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["notices"]


async def emails_to(mailbox, subject_starts: str) -> list:
    return [
        sent
        for sent in await mailbox.to(IVAN)
        if sent.subject.startswith(subject_starts)
    ]


@pytest.fixture
def the_connect_secret(monkeypatch):
    monkeypatch.setenv("STRIPE_CONNECT_WEBHOOK_SECRET", CONNECT_SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def the_provider_says_the_fee_is_ready(
    client, *, account: str, payment_id: str, notice_id: str
):
    """Stripe's ``charge.updated`` on the club's account: the charge of this
    payment changed — its fee is readable now."""

    body = json.dumps(
        {
            "id": notice_id,
            "object": "event",
            "type": "charge.updated",
            "account": account,
            "data": {
                "object": {
                    "id": f"ch_{payment_id}",
                    "object": "charge",
                    "payment_intent": payment_id,
                }
            },
        }
    )
    return await client.post(
        CONNECT_WEBHOOK,
        content=body.encode(),
        headers={
            "Stripe-Signature": stripe.WebhookSignature.generate_signature_header(
                body, CONNECT_SECRET
            ),
            "Content-Type": "application/json",
        },
    )


def a_club_on_its_own_pricing(payments, club: str) -> None:
    """The provider tells the club its fees only after the take."""

    payments.fees_reported_later.add(payments.account_opened_for(UUID(club)))


# --------------------------------------------------------------------------- #
# The seat-taken refund: the share less exactly the fee kept
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("kind", "back", "kept"), KINDS)
async def test_a_replaced_late_leaver_gets_the_share_less_exactly_the_fee_kept(
    client, session_factory, payments, clock, club, mailbox, kind, back, kept
):
    booking, ivan, diego = await a_game_ivan_is_in(
        client, session_factory, payments, clock, club, kind=kind
    )
    await the_cut_off_takes_the_shares(session_factory, clock, mailbox)
    clock.move(timedelta(hours=1))
    await leaves(client, ivan, booking)

    await joins(client, diego, booking)

    refund, charge = await receipts_of(client, mailbox, ivan)
    [asked] = payments.called("refund")
    assert asked.arguments["amount_grosze"] == back
    assert (refund["kind"], refund["amount_grosze"], refund["card_fee_grosze"]) == (
        "REFUND",
        back,
        kept,
    )
    assert (charge["kind"], charge["amount_grosze"]) == ("CHARGE", SHARE)


async def test_the_seat_taken_email_and_notice_state_the_exact_sum(
    client, session_factory, payments, clock, club, mailbox
):
    """*You've been refunded 38,24 zł · your seat was taken* — *(40 zł less
    the 1,76 zł kept on your payment)*, in the email and the notice alike."""

    booking, ivan, diego = await a_game_ivan_is_in(
        client, session_factory, payments, clock, club, kind=CardKind.BUSINESS
    )
    await the_cut_off_takes_the_shares(session_factory, clock, mailbox)
    clock.move(timedelta(hours=1))
    await leaves(client, ivan, booking)

    await joins(client, diego, booking)

    [email] = await emails_to(mailbox, "You've been refunded")
    assert email.subject == "You've been refunded 38,24 zł · your seat was taken"
    assert "(40 zł less the 1,76 zł kept on your payment)" in email.text
    assert "BLIK" not in email.text
    [notice, *_] = await notices_of(client, mailbox, ivan)
    assert notice["kind"] == "REFUNDED"
    assert notice["title"] == "You've been refunded 38,24 zł · your seat was taken"
    assert notice["body"].startswith("40 zł less the 1,76 zł kept on your payment")


async def test_a_refund_waits_for_a_fee_not_yet_known_and_is_made_once_it_is(
    client, session_factory, payments, clock, club, mailbox
):
    """A club on its own negotiated pricing is told its fee after the take:
    nothing is refunded, and nobody told a sum, until the fee is known — then
    the share less exactly it."""

    a_club_on_its_own_pricing(payments, club)
    booking, ivan, diego = await a_game_ivan_is_in(
        client, session_factory, payments, clock, club, kind=CardKind.BUSINESS
    )
    await the_cut_off_takes_the_shares(session_factory, clock, mailbox)
    clock.move(timedelta(hours=1))
    await leaves(client, ivan, booking)

    await joins(client, diego, booking)

    [charge] = await receipts_of(client, mailbox, ivan)
    assert charge["kind"] == "CHARGE"
    assert payments.called("refund") == []
    assert await emails_to(mailbox, "You've been refunded") == []

    for call in payments.called("capture"):
        payments.reports_fee(call.arguments["payment_id"])

    refund, _charge = await receipts_of(client, mailbox, ivan)
    assert (refund["kind"], refund["amount_grosze"], refund["card_fee_grosze"]) == (
        "REFUND",
        38_24,
        1_76,
    )
    [email] = await emails_to(mailbox, "You've been refunded")
    assert email.subject == "You've been refunded 38,24 zł · your seat was taken"


# --------------------------------------------------------------------------- #
# What leaving costs, said before the player leaves
# --------------------------------------------------------------------------- #


async def test_the_leave_quote_is_nothing_before_the_cut_off_and_exact_after(
    client, session_factory, payments, clock, club, mailbox
):
    booking, ivan, _diego = await a_game_ivan_is_in(
        client, session_factory, payments, clock, club, kind=CardKind.BUSINESS
    )

    before = await leaving_of(client, ivan, booking)
    await the_cut_off_takes_the_shares(session_factory, clock, mailbox)
    after = await leaving_of(client, ivan, booking)

    # Nothing is taken before the cut-off, so nothing comes back (#637).
    assert before == {
        "kind": "BEFORE_THE_CUT_OFF",
        "refund_grosze": None,
        "card_fee_grosze": None,
    }
    assert after == {
        "kind": "AFTER_THE_CUT_OFF",
        "refund_grosze": 38_24,
        "card_fee_grosze": 1_76,
    }


async def test_the_leave_quote_has_no_figure_until_the_provider_tells_the_fee(
    client, session_factory, payments, clock, club, mailbox, the_connect_secret
):
    """No figure and no clause while the fee is not yet known — never an
    estimate — and the exact one once the provider says it: Stripe's
    ``charge.updated`` is the prompt to read the payment again."""

    a_club_on_its_own_pricing(payments, club)
    booking, ivan, _diego = await a_game_ivan_is_in(
        client, session_factory, payments, clock, club, kind=CardKind.BUSINESS
    )
    await the_cut_off_takes_the_shares(session_factory, clock, mailbox)

    unknown = await leaving_of(client, ivan, booking)
    for number, call in enumerate(payments.called("capture")):
        payments.reports_fee(call.arguments["payment_id"])
        told = await the_provider_says_the_fee_is_ready(
            client,
            account=call.arguments["account_id"],
            payment_id=call.arguments["payment_id"],
            notice_id=f"evt_fee_{number}",
        )
        assert told.status_code == 204, told.text
    known = await leaving_of(client, ivan, booking)

    assert unknown == {
        "kind": "AFTER_THE_CUT_OFF",
        "refund_grosze": None,
        "card_fee_grosze": None,
    }
    assert known == {
        "kind": "AFTER_THE_CUT_OFF",
        "refund_grosze": 38_24,
        "card_fee_grosze": 1_76,
    }


async def test_leaving_after_the_cut_off_emails_what_comes_back_if_the_seat_is_taken(
    client, session_factory, payments, clock, club, mailbox
):
    booking, ivan, _diego = await a_game_ivan_is_in(
        client, session_factory, payments, clock, club, kind=CardKind.BUSINESS
    )
    await the_cut_off_takes_the_shares(session_factory, clock, mailbox)
    clock.move(timedelta(hours=1))

    assert await leaves(client, ivan, booking) == "AFTER_THE_CUT_OFF"

    [email] = await emails_to(mailbox, "You left the game")
    assert email.subject == "You left the game"
    assert (
        "Your seat is offered to others. If someone takes it, you get 38,24 zł "
        "back (40 zł less the 1,76 zł kept on your payment)."
    ) in email.text


async def test_leaving_after_the_cut_off_names_no_figure_while_the_fee_is_unknown(
    client, session_factory, payments, clock, club, mailbox
):
    a_club_on_its_own_pricing(payments, club)
    booking, ivan, _diego = await a_game_ivan_is_in(
        client, session_factory, payments, clock, club, kind=CardKind.BUSINESS
    )
    await the_cut_off_takes_the_shares(session_factory, clock, mailbox)
    clock.move(timedelta(hours=1))

    await leaves(client, ivan, booking)

    [email] = await emails_to(mailbox, "You left the game")
    assert "Your seat is offered to others." in email.text
    assert "If someone takes it" not in email.text


# --------------------------------------------------------------------------- #
# Receipts: paid, refunded with what was kept, held · released
# --------------------------------------------------------------------------- #


async def test_a_share_held_and_let_go_is_a_held_released_receipt(
    client, session_factory, payments, clock, club, mailbox
):
    """Ivan left before the cut-off: nothing was taken, and the hold his bank
    app showed is explained — *40 zł held · released*, dated when it was let
    go."""

    booking, ivan, _diego = await a_game_ivan_is_in(
        client, session_factory, payments, clock, club, kind=CardKind.BUSINESS
    )
    clock.move(timedelta(hours=2))

    assert await leaves(client, ivan, booking) == "BEFORE_THE_CUT_OFF"

    [released] = await receipts_of(client, mailbox, ivan)
    assert (
        released["kind"],
        released["amount_grosze"],
        released["card_fee_grosze"],
        released["paid_at"],
    ) == ("RELEASED", SHARE, None, "2026-10-05T08:00:00Z")
    assert released["club"]["name"] == "Bonarka Arena"


async def test_a_share_taken_is_a_paid_receipt_and_a_hold_never_let_go_is_none(
    client, session_factory, payments, clock, club, mailbox
):
    booking, ivan, _diego = await a_game_ivan_is_in(
        client, session_factory, payments, clock, club, kind=CardKind.BUSINESS
    )

    held = await receipts_of(client, mailbox, ivan)
    await the_cut_off_takes_the_shares(session_factory, clock, mailbox)
    taken = await receipts_of(client, mailbox, ivan)

    # Held until the cut-off: nothing moved, and nothing was let go.
    assert held == []
    [paid] = taken
    assert (paid["kind"], paid["amount_grosze"], paid["card_fee_grosze"]) == (
        "CHARGE",
        SHARE,
        None,
    )

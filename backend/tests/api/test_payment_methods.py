"""Saving a payment method: the setup, its order, a change and a removal (#536).

You › Payments' four steps (the mechanics §12.5, the screens A7.3): choose how
to pay, type the card into the provider's own fields, **accept the terms**, and
confirm with the bank — which is the step that saves. Driven over HTTP against
the fake provider (``tests/conftest.py``'s ``payments``), whose *phone* is told
which of Stripe's test cards the player typed.

Three rules are what these tests hold the routes to:

- **the terms are accepted before anything is saved** — the setup's secret, the
  only thing a phone can save with, is the answer to accepting them and to
  nothing else, and a save asked for before them is refused;
- **change keeps the old method until the new one is saved**, and the old card
  is released at the provider only after;
- **remove is refused while the method is still needed** — a live yes, or a
  booked game ahead.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.payments.domain.ports import Commitments
from app.modules.payments.domain.provider import Wallet
from app.modules.payments.domain.entered_cards import (
    A_CARD,
    A_CARD_THE_BANK_CHECKS_ONCE,
    A_CARD_THE_BANK_DECLINES,
    EnteredCard,
)
from app.modules.payments.infrastructure.fake_payments import FakeRefusal
from app.modules.payments.presentation.dependencies import get_payment_commitments
from tests.api.players_world import deliver_the_outbox

BASE = "/api/v1/players/me/payment-methods"
SETUP = f"{BASE}/setup"
TERMS = f"{BASE}/terms"
CONFIRMATION = f"{BASE}/confirmation"
CURRENT = f"{BASE}/current"

#: The payment terms in force — the mechanics §12.5, settled on 2026-09-29.
TERMS_IN_FORCE = "2026-09-29"

A_MASTERCARD = EnteredCard(brand="mastercard", last_four="4444")

TOMEK = {
    "email": "tomek@example.com",
    "password1": "hunter22!",
    "password2": "hunter22!",
    "adult_attested": True,
}


async def signed_in(client, payload=TOMEK) -> dict[str, str]:
    assert (await client.post("/api/v1/users", json=payload)).status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password1"]},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
async def tomek(client) -> dict[str, str]:
    return await signed_in(client)


async def starts(client, player) -> dict:
    started = await client.post(SETUP, headers=player)
    assert started.status_code == 201, started.text
    return started.json()


async def accepts(client, player, version: str = TERMS_IN_FORCE) -> dict:
    accepted = await client.post(TERMS, headers=player, json={"terms_version": version})
    assert accepted.status_code == 200, accepted.text
    return accepted.json()


async def confirms(client, player) -> dict:
    confirmed = await client.post(CONFIRMATION, headers=player)
    assert confirmed.status_code == 200, confirmed.text
    return confirmed.json()


async def current(client, player) -> dict:
    read = await client.get(CURRENT, headers=player)
    assert read.status_code == 200, read.text
    return read.json()


async def saves(client, payments, player, card: EnteredCard = A_CARD) -> dict:
    """The whole setup, in its order: start, the phone types the card, the
    terms, the bank."""

    setup = await starts(client, player)
    payments.phone_enters(setup["setup_id"], card)
    await accepts(client, player)
    return await confirms(client, player)


# ---------------------------------------------------------------------------
# The order
# ---------------------------------------------------------------------------


async def test_nothing_is_set_up_until_the_player_sets_something_up(client, tomek):
    assert await current(client, tomek) == {
        "method": None,
        "terms_needed": False,
        "terms_version": TERMS_IN_FORCE,
    }


async def test_the_setup_saves_the_card_the_phone_confirmed(client, payments, tomek):
    setup = await starts(client, tomek)
    payments.phone_enters(setup["setup_id"], A_CARD)
    accepted = await accepts(client, tomek)
    confirmed = await confirms(client, tomek)

    assert setup["setup_id"].startswith("seti_")
    assert setup["publishable_key"] == payments.publishable_key()
    assert setup["terms_version"] == TERMS_IN_FORCE
    assert accepted["client_secret"]
    assert confirmed == {
        "method": {"brand": "visa", "last_four": "4242", "wallet": None},
        "terms_needed": False,
        "terms_version": TERMS_IN_FORCE,
    }
    assert await current(client, tomek) == confirmed
    # Off-session, under the player's one customer at the provider.
    assert [call.name for call in payments.calls[:2]] == [
        "open_customer",
        "start_setup",
    ]


async def test_the_secret_a_phone_saves_with_is_the_answer_to_the_terms(
    client, payments, tomek
):
    """**Structural, not a promise**: starting a setup hands out no secret, so
    nothing can be confirmed on a phone before the terms were accepted."""

    setup = await starts(client, tomek)
    accepted = await accepts(client, tomek)
    reading = await payments.read_setup(setup["setup_id"])

    assert "client_secret" not in setup
    assert accepted["client_secret"] == reading.client_secret


async def test_nothing_is_saved_before_the_terms(client, payments, tomek):
    setup = await starts(client, tomek)
    payments.phone_enters(setup["setup_id"], A_CARD)

    refused = await client.post(CONFIRMATION, headers=tomek)

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "payment_terms_not_accepted"
    assert (await current(client, tomek))["method"] is None


async def test_neither_the_terms_nor_a_save_without_a_setup(client, tomek):
    terms = await client.post(
        TERMS, headers=tomek, json={"terms_version": TERMS_IN_FORCE}
    )
    confirmation = await client.post(CONFIRMATION, headers=tomek)

    assert terms.status_code == confirmation.status_code == 409
    assert terms.json()["code"] == "payment_setup_not_started"
    assert confirmation.json()["code"] == "payment_setup_not_started"


async def test_terms_that_are_not_the_ones_in_force_are_refused(client, tomek):
    await starts(client, tomek)

    refused = await client.post(
        TERMS, headers=tomek, json={"terms_version": "2025-01-01"}
    )

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "payment_terms_outdated"
    assert refused.json()["details"] == {"terms_version": TERMS_IN_FORCE}


async def test_the_acceptance_is_recorded_with_its_version_moment_and_address(
    client, session_factory, clock, tomek
):
    """The consent record (the mechanics §12.5): which terms, when, from where.
    It crosses on no route — the stream is where it is evidence."""

    await starts(client, tomek)
    await accepts(client, tomek)

    async with session_factory() as session:
        rows = (
            await session.scalars(
                select(EventStoreORM).where(
                    EventStoreORM.event_type == "payments.terms_accepted"
                )
            )
        ).all()

    assert len(rows) == 1
    assert rows[0].payload["terms_version"] == TERMS_IN_FORCE
    assert rows[0].payload["ip"] == "127.0.0.1"
    assert rows[0].payload["setup_id"]
    assert rows[0].occurred_at.replace(tzinfo=None) == clock.now().replace(tzinfo=None)


async def test_a_card_the_bank_declines_is_not_saved_and_another_can_be_tried(
    client, payments, tomek
):
    setup = await starts(client, tomek)
    await accepts(client, tomek)
    payments.phone_enters(setup["setup_id"], A_CARD_THE_BANK_DECLINES)

    declined = await client.post(CONFIRMATION, headers=tomek)
    payments.phone_enters(setup["setup_id"], A_CARD)
    saved = await confirms(client, tomek)

    assert declined.status_code == 409, declined.text
    assert declined.json()["code"] == "payment_method_declined"
    assert saved["method"]["last_four"] == "4242"


async def test_the_bank_s_one_time_check_must_finish_first(client, payments, tomek):
    setup = await starts(client, tomek)
    await accepts(client, tomek)
    payments.phone_enters(setup["setup_id"], A_CARD_THE_BANK_CHECKS_ONCE)

    waiting = await client.post(CONFIRMATION, headers=tomek)
    payments.phone_authenticates(setup["setup_id"])
    saved = await confirms(client, tomek)

    assert waiting.status_code == 409, waiting.text
    assert waiting.json()["code"] == "payment_setup_not_finished"
    assert waiting.json()["details"] == {"status": "AUTHENTICATING"}
    assert saved["method"]["last_four"] == "3155"


async def test_confirming_twice_is_the_same_answer(client, payments, tomek):
    first = await saves(client, payments, tomek)

    again = await confirms(client, tomek)

    assert again == first


async def test_a_wallet_is_saved_as_the_wallet(client, payments, tomek):
    saved = await saves(
        client, payments, tomek, EnteredCard(last_four="1881", wallet=Wallet.GOOGLE_PAY)
    )

    assert saved["method"] == {
        "brand": "visa",
        "last_four": "1881",
        "wallet": "GOOGLE_PAY",
    }


async def test_a_provider_that_cannot_be_reached_records_nothing(
    client, payments, tomek
):
    payments.unreachable = True
    refused = await client.post(SETUP, headers=tomek)
    payments.unreachable = False

    assert refused.status_code == 503, refused.text
    assert refused.json()["code"] == "payments_unavailable"
    assert (await current(client, tomek))["method"] is None
    await saves(client, payments, tomek)


async def test_a_sixth_setup_in_a_day_is_refused_before_the_provider_is_asked(
    client, payments, clock, tomek
):
    """Card testers target card-saving (the mechanics Appendix A)."""

    for _ in range(5):
        await starts(client, tomek)
    asked = len(payments.calls)

    refused = await client.post(SETUP, headers=tomek)
    unasked = len(payments.calls)
    clock.move(timedelta(days=1))
    later = await client.post(SETUP, headers=tomek)

    assert refused.status_code == 429, refused.text
    assert refused.json()["code"] == "payment_setups_exhausted"
    assert unasked == asked
    assert later.status_code == 201, later.text


async def test_one_player_s_setups_all_open_under_one_customer(client, payments, tomek):
    await saves(client, payments, tomek)
    await saves(client, payments, tomek, A_MASTERCARD)

    customers = {
        call.arguments["customer_id"] for call in payments.called("start_setup")
    }

    assert len(payments.called("open_customer")) == 1
    assert len(customers) == 1


# ---------------------------------------------------------------------------
# Change
# ---------------------------------------------------------------------------


async def test_a_change_keeps_the_old_card_until_the_new_one_is_saved(
    client, payments, session_factory, tomek
):
    first = await starts(client, tomek)
    payments.phone_enters(first["setup_id"], A_CARD)
    await accepts(client, tomek)
    old = (await confirms(client, tomek))["method"]
    old_card = (await payments.read_setup(first["setup_id"])).card
    setup = await starts(client, tomek)
    payments.phone_enters(setup["setup_id"], A_MASTERCARD)
    await accepts(client, tomek)

    while_changing = await current(client, tomek)
    changed = await confirms(client, tomek)
    await deliver_the_outbox(session_factory, payments=payments)

    assert while_changing["method"] == old
    assert changed["method"] == {
        "brand": "mastercard",
        "last_four": "4444",
        "wallet": None,
    }
    released = [
        call.arguments["method_id"] for call in payments.called("release_method")
    ]
    assert old_card is not None
    assert released == [old_card.method_id]
    assert payments.is_released(old_card.method_id)


async def test_an_abandoned_change_leaves_the_old_card_saved(client, payments, tomek):
    old = await saves(client, payments, tomek)
    await starts(client, tomek)

    assert await current(client, tomek) == old


async def test_a_setup_replaced_by_another_is_closed_at_the_provider(
    client, payments, session_factory, tomek
):
    """Its secret was handed out with the terms, so a phone may still hold it:
    closed, it can save nothing that nobody would record."""

    first = await starts(client, tomek)
    await accepts(client, tomek)
    await starts(client, tomek)
    await deliver_the_outbox(session_factory, payments=payments)

    assert [call.arguments["setup_id"] for call in payments.called("cancel_setup")] == [
        first["setup_id"]
    ]
    with pytest.raises(FakeRefusal):
        payments.phone_enters(first["setup_id"], A_CARD)


async def test_a_card_saved_with_a_replaced_setup_is_released(
    client, payments, session_factory, tomek
):
    """The phone confirmed the old setup before the new one was opened, and the
    app never said so: that card was saved at the provider and nobody recorded
    it, so it is released rather than left there."""

    first = await starts(client, tomek)
    await accepts(client, tomek)
    payments.phone_enters(first["setup_id"], A_CARD)
    orphan = (await payments.read_setup(first["setup_id"])).card
    await starts(client, tomek)
    await deliver_the_outbox(session_factory, payments=payments)

    assert orphan is not None
    assert payments.is_released(orphan.method_id)
    assert (await current(client, tomek))["method"] is None


# ---------------------------------------------------------------------------
# Remove
# ---------------------------------------------------------------------------


async def test_a_removed_card_is_gone_and_released_at_the_provider(
    client, payments, session_factory, tomek
):
    await saves(client, payments, tomek)

    removed = await client.delete(CURRENT, headers=tomek)
    await deliver_the_outbox(session_factory, payments=payments)

    assert removed.status_code == 204, removed.text
    assert (await current(client, tomek))["method"] is None
    released = payments.called("release_method")
    assert len(released) == 1
    assert payments.is_released(released[0].arguments["method_id"])


async def test_remove_is_refused_while_the_card_is_still_needed(
    app, client, payments, tomek
):
    """A live yes charges when its game fills, and a booked game ahead may yet
    be refunded to it (the mechanics §12.5, Q83). What they answer is stood in
    for here; a booked game holding a method is ``test_the_fill.py``'s (#541)."""

    class StillNeeded:
        async def of(self, player_id, *, at):
            return Commitments(live_yeses=2, upcoming_games=1)

    app.dependency_overrides[get_payment_commitments] = StillNeeded
    saved = await saves(client, payments, tomek)

    refused = await client.delete(CURRENT, headers=tomek)

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "payment_method_in_use"
    assert refused.json()["details"] == {"live_yeses": 2, "upcoming_games": 1}
    assert await current(client, tomek) == saved


async def test_nothing_saved_is_nothing_to_remove(client, tomek):
    refused = await client.delete(CURRENT, headers=tomek)

    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "payment_method_not_found"


async def test_a_player_reads_only_their_own_method(client, payments, tomek):
    await saves(client, payments, tomek)
    ola = await signed_in(client, {**TOMEK, "email": "ola@example.com"})

    assert (await current(client, ola))["method"] is None

"""The provider's platform webhook: verified, read once, and in Raketa's words.

``POST /api/v1/webhooks/stripe`` (#536). Stripe signs every notice with the
endpoint's secret and sends it **twice as often as not, and out of order**
(the mechanics Appendix A), so these tests post notices shaped and signed as
Stripe's are — with stripe-python's own signer — and hold the endpoint to three
rules: nothing unverified is read; a notice is read **once**, by its id; and
what it moves is the stream's, so the app and the notice saying the same thing
change it once.

Two kinds are read today: a setup that succeeded while the app was away, and a
card its bank updated — where **a new brand asks for the terms again**.
"""

from __future__ import annotations

import json
import time

import pytest
import stripe

from app.core.config import get_settings
from app.modules.payments.domain.entered_cards import A_CARD
from tests.api.test_payment_methods import (
    TERMS,
    TERMS_IN_FORCE,
    accepts,
    confirms,
    current,
    starts,
)

WEBHOOK = "/api/v1/webhooks/stripe"
SECRET = "whsec_the_suite_s_own"


@pytest.fixture(autouse=True)
def the_endpoint_s_secret(monkeypatch):
    """The secret this process verifies notices with, placed before the
    application reads its settings — so what is exercised is the route reading
    it, not a reader handed one."""

    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def tomek(client):
    from tests.api.test_payment_methods import signed_in

    return await signed_in(client)


def notice(kind: str, subject: dict, *, notice_id: str = "evt_1") -> str:
    return json.dumps(
        {
            "id": notice_id,
            "object": "event",
            "type": kind,
            "data": {"object": subject},
        }
    )


def signed(body: str, *, secret: str = SECRET, at: int | None = None) -> dict:
    return {
        "Stripe-Signature": stripe.WebhookSignature.generate_signature_header(
            body, secret, timestamp=at
        ),
        "Content-Type": "application/json",
    }


async def sends(client, body: str, headers: dict | None = None):
    return await client.post(
        WEBHOOK,
        content=body.encode(),
        headers=signed(body) if headers is None else headers,
    )


async def a_saved_card(client, payments, player) -> tuple[str, str, str]:
    """Save ``A_CARD`` the ordinary way; its setup, customer and method ids."""

    setup = await starts(client, player)
    payments.phone_enters(setup["setup_id"], A_CARD)
    await accepts(client, player)
    await confirms(client, player)
    reading = await payments.read_setup(setup["setup_id"])
    assert reading.card is not None
    return setup["setup_id"], reading.customer_id, reading.card.method_id


def card_updated(customer: str, method: str, *, brand: str, last4: str) -> dict:
    """``payment_method.automatically_updated``'s object. The card in it is what
    Stripe says, and what the endpoint deliberately does not read."""

    return {
        "id": method,
        "object": "payment_method",
        "customer": customer,
        "type": "card",
        "card": {"brand": brand, "last4": last4, "wallet": None},
    }


# ---------------------------------------------------------------------------
# Verified before a byte is read
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param(lambda body: {}, id="unsigned"),
        pytest.param(
            lambda body: signed(body, secret="whsec_somebody_else_s"),
            id="signed-with-another-secret",
        ),
        pytest.param(
            lambda body: signed(body, at=int(time.time()) - 10 * 60),
            id="signed-ten-minutes-ago",
        ),
    ],
)
async def test_a_notice_that_cannot_be_verified_is_refused(client, headers):
    body = notice("setup_intent.succeeded", {"id": "seti_1", "customer": "cus_1"})

    refused = await sends(client, body, headers(body))

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "payment_notice_refused"


async def test_a_laptop_with_no_secret_reads_no_notice(client, monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET")
    get_settings.cache_clear()
    body = notice("setup_intent.succeeded", {"id": "seti_1", "customer": "cus_1"})

    refused = await sends(client, body)

    assert refused.status_code == 503, refused.text
    assert refused.json()["code"] == "payment_notices_not_configured"


async def test_the_webhook_is_on_no_client_s_contract(client):
    """Stripe calls it and no client does, so no document describes it."""

    for surface in ("player", "club", "public", "dev"):
        from app.api.contract import SURFACES, build_surface_spec

        paths = build_surface_spec(surface, SURFACES[surface])["paths"]
        assert not [path for path in paths if "webhooks" in path], surface


# ---------------------------------------------------------------------------
# A setup that succeeded while the app was away
# ---------------------------------------------------------------------------


async def test_a_setup_the_app_never_came_back_for_is_saved_by_its_notice(
    client, payments, tomek
):
    setup = await starts(client, tomek)
    await accepts(client, tomek)
    payments.phone_enters(setup["setup_id"], A_CARD)
    reading = await payments.read_setup(setup["setup_id"])

    told = await sends(
        client,
        notice(
            "setup_intent.succeeded",
            {"id": setup["setup_id"], "customer": reading.customer_id},
        ),
    )

    assert told.status_code == 204, told.text
    assert (await current(client, tomek))["method"] == {
        "brand": "visa",
        "last_four": "4242",
        "wallet": None,
    }


async def test_a_setup_s_notice_saves_nothing_before_the_terms(client, payments, tomek):
    """A phone cannot confirm a setup without its secret, and the secret is the
    answer to the terms — but a notice is never trusted to have kept that."""

    setup = await starts(client, tomek)
    payments.phone_enters(setup["setup_id"], A_CARD)
    reading = await payments.read_setup(setup["setup_id"])

    told = await sends(
        client,
        notice(
            "setup_intent.succeeded",
            {"id": setup["setup_id"], "customer": reading.customer_id},
        ),
    )

    assert told.status_code == 204, told.text
    assert (await current(client, tomek))["method"] is None


async def test_the_app_and_the_notice_saying_the_same_thing_save_it_once(
    client, payments, tomek
):
    setup_id, customer, _ = await a_saved_card(client, payments, tomek)
    saved = await current(client, tomek)

    told = await sends(
        client,
        notice("setup_intent.succeeded", {"id": setup_id, "customer": customer}),
    )

    assert told.status_code == 204, told.text
    assert await current(client, tomek) == saved


# ---------------------------------------------------------------------------
# A card its bank updated
# ---------------------------------------------------------------------------


async def test_a_new_brand_asks_for_the_terms_again(client, payments, tomek):
    _, customer, method = await a_saved_card(client, payments, tomek)
    payments.bank_replaces_card(method, brand="mastercard", last_four="5454")

    told = await sends(
        client,
        notice(
            "payment_method.automatically_updated",
            card_updated(customer, method, brand="mastercard", last4="5454"),
        ),
    )
    asked = await current(client, tomek)
    reaccepted = await client.post(
        TERMS, headers=tomek, json={"terms_version": TERMS_IN_FORCE}
    )

    assert told.status_code == 204, told.text
    assert asked == {
        "method": {"brand": "mastercard", "last_four": "5454", "wallet": None},
        "terms_needed": True,
        "terms_version": TERMS_IN_FORCE,
    }
    assert reaccepted.status_code == 200, reaccepted.text
    assert reaccepted.json() == {"client_secret": None}
    assert (await current(client, tomek))["terms_needed"] is False


async def test_the_terms_asked_again_are_answered_with_a_change_left_open(
    client, payments, tomek
):
    """A *Change* started and abandoned leaves a setup open, and accepting the
    terms then answers that setup's secret — which must not leave the saved
    card waiting on terms the player has just accepted."""

    _, customer, method = await a_saved_card(client, payments, tomek)
    await starts(client, tomek)
    payments.bank_replaces_card(method, brand="mastercard", last_four="5454")
    await sends(
        client,
        notice(
            "payment_method.automatically_updated",
            card_updated(customer, method, brand="mastercard", last4="5454"),
        ),
    )

    accepted = await accepts(client, tomek)

    assert accepted["client_secret"]
    assert (await current(client, tomek))["terms_needed"] is False


async def test_a_new_number_of_the_same_brand_asks_nothing(client, payments, tomek):
    _, customer, method = await a_saved_card(client, payments, tomek)
    payments.bank_replaces_card(method, brand="visa", last_four="1111")

    await sends(
        client,
        notice(
            "payment_method.automatically_updated",
            card_updated(customer, method, brand="visa", last4="1111"),
        ),
    )

    assert (await current(client, tomek))["method"]["last_four"] == "1111"
    assert (await current(client, tomek))["terms_needed"] is False


# ---------------------------------------------------------------------------
# Read once
# ---------------------------------------------------------------------------


async def test_a_notice_delivered_again_is_read_once(client, payments, tomek):
    """The second delivery finds the notice in the inbox and asks the provider
    nothing: the card is read once, for the one notice."""

    _, customer, method = await a_saved_card(client, payments, tomek)
    payments.bank_replaces_card(method, brand="mastercard", last_four="5454")
    updated = notice(
        "payment_method.automatically_updated",
        card_updated(customer, method, brand="mastercard", last4="5454"),
        notice_id="evt_to_mastercard",
    )

    first = await sends(client, updated)
    again = await sends(client, updated)

    assert first.status_code == again.status_code == 204
    assert len(payments.called("read_card")) == 1


async def test_updates_arriving_out_of_order_leave_the_card_as_it_stands(
    client, payments, tomek
):
    """**Out of order** (the mechanics Appendix A): the bank moves the card to
    Mastercard and back to Visa, and the first notice arrives last. Read off the
    notices, the card would end on a brand it no longer has and ask for the
    terms for nothing; read from the provider, it ends as it is."""

    _, customer, method = await a_saved_card(client, payments, tomek)
    payments.bank_replaces_card(method, brand="mastercard", last_four="5454")
    payments.bank_replaces_card(method, brand="visa", last_four="4242")
    to_mastercard = notice(
        "payment_method.automatically_updated",
        card_updated(customer, method, brand="mastercard", last4="5454"),
        notice_id="evt_to_mastercard",
    )
    back_to_visa = notice(
        "payment_method.automatically_updated",
        card_updated(customer, method, brand="visa", last4="4242"),
        notice_id="evt_back_to_visa",
    )

    await sends(client, back_to_visa)
    await sends(client, to_mastercard)

    assert await current(client, tomek) == {
        "method": {"brand": "visa", "last_four": "4242", "wallet": None},
        "terms_needed": False,
        "terms_version": TERMS_IN_FORCE,
    }


async def test_a_notice_nothing_listens_to_or_about_nobody_is_acknowledged(
    client, payments, tomek
):
    unheeded = await sends(
        client, notice("customer.created", {"id": "cus_1"}, notice_id="evt_a")
    )
    about_nobody = await sends(
        client,
        notice(
            "payment_method.automatically_updated",
            card_updated("cus_nobody", "pm_nobody", brand="visa", last4="4242"),
            notice_id="evt_b",
        ),
    )

    assert unheeded.status_code == about_nobody.status_code == 204

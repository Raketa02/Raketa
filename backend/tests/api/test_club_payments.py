"""A club connects payments: Stripe's hosted onboarding, and the account's
status kept current by the Connected accounts webhook (#537, the mechanics
§16.2, the screens B2).

**The club is the seller** (``docs/adr/0189`` §4), so nothing can be charged
until its account at the provider can take a payment and pay it out — and the
setup checklist's first step is exactly that. The desk asks for a link, is
sent to the provider's own pages, and comes back; **what the account is, the
provider says**, by notice, and every notice is read the way the platform's are
(``docs/adr/0190`` §3): verified, read once, and a prompt to read the account as
it stands rather than a reading.

The provider here is the suite's fake (``tests/conftest.py``), whose accounts a
test moves with ``club_account_is`` — what Stripe does when a club fills in its
pages, or when it later disables charges.
"""

from __future__ import annotations

import json
import time
from uuid import UUID

import pytest
import stripe

from app.core.config import get_settings
from app.modules.payments.domain.errors import PaymentsUnavailable
from app.modules.payments.domain.provider import ClubAccountStatus
from tests.api.administration_world import DESK
from tests.api.club_courts_world import (
    PAYMENTS_LINK,
    SETUP,
    a_desk,
    adds_a_court,
    chooses,
    confirms_settings,
    sets_hours,
    sets_prices,
)

CONNECT_WEBHOOK = "/api/v1/webhooks/stripe-connect"
CONNECT_SECRET = "whsec_the_connect_endpoint_s_own"
PLATFORM_SECRET = "whsec_the_platform_endpoint_s_own"

READY = ClubAccountStatus.READY
NEEDS_DETAILS = ClubAccountStatus.NEEDS_DETAILS
NOT_STARTED = ClubAccountStatus.NOT_STARTED


@pytest.fixture(autouse=True)
def the_endpoints_secrets(monkeypatch):
    """Each endpoint's own secret, placed before the application reads its
    settings: Stripe signs a Connected accounts notice with that endpoint's
    secret and never the platform's."""

    monkeypatch.setenv("STRIPE_CONNECT_WEBHOOK_SECRET", CONNECT_SECRET)
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", PLATFORM_SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# The desk's moves, and the provider's
# ---------------------------------------------------------------------------


async def asks_for_a_link(client, desk: dict) -> str:
    linked = await client.post(PAYMENTS_LINK, headers=desk)
    assert linked.status_code == 200, linked.text
    return linked.json()["url"]


async def setup_of(client, desk: dict) -> dict:
    read = await client.get(SETUP, headers=desk)
    assert read.status_code == 200, read.text
    return read.json()


async def payments_of(client, desk: dict) -> tuple[str, str]:
    """The payments status, and the checklist's first step."""

    body = await setup_of(client, desk)
    [step] = [row for row in body["steps"] if row["step"] == "CONNECT_PAYMENTS"]
    return body["payments"], step["state"]


def account_update(
    account_id: str, *, notice_id: str = "evt_1", charges_enabled: bool = True
) -> str:
    """``account.updated``, as a Connected accounts endpoint receives it: the
    account it is about at the top, and the account itself — which the
    endpoint deliberately does not read — as its object."""

    return json.dumps(
        {
            "id": notice_id,
            "object": "event",
            "type": "account.updated",
            "account": account_id,
            "data": {
                "object": {
                    "id": account_id,
                    "object": "account",
                    "charges_enabled": charges_enabled,
                    "payouts_enabled": charges_enabled,
                    "details_submitted": True,
                }
            },
        }
    )


def signed(body: str, *, secret: str = CONNECT_SECRET, at: int | None = None) -> dict:
    return {
        "Stripe-Signature": stripe.WebhookSignature.generate_signature_header(
            body, secret, timestamp=at
        ),
        "Content-Type": "application/json",
    }


async def stripe_says(client, body: str, headers: dict | None = None):
    return await client.post(
        CONNECT_WEBHOOK,
        content=body.encode(),
        headers=signed(body) if headers is None else headers,
    )


async def account_moves(
    client, payments, club_id: str, status: ClubAccountStatus, *, notice_id: str
) -> str:
    """The club's account moves at the provider, and the provider says so."""

    account = payments.account_opened_for(UUID(club_id))
    payments.club_account_is(account, status)
    told = await stripe_says(client, account_update(account, notice_id=notice_id))
    assert told.status_code == 204, told.text
    return account


async def a_club_set_up_but_for_payments(client) -> tuple[str, dict]:
    """The four other steps done: it is payments alone that keeps it off
    players' decks."""

    club_id, desk = await a_desk(client, sports=("PADEL",))
    await chooses(client, desk, "INSTANT")
    court = await adds_a_court(client, desk, name="Court 1")
    await sets_hours(client, desk, [court["id"]], [(2, 18)])
    await sets_prices(
        client, desk, [{"sport": "PADEL", "price_grosze": 120_00, "bands": []}]
    )
    await confirms_settings(client, desk)
    return club_id, desk


# ---------------------------------------------------------------------------
# The link
# ---------------------------------------------------------------------------


async def test_a_club_that_has_not_connected_has_payments_to_do(client):
    _, desk = await a_desk(client)

    assert await payments_of(client, desk) == ("NOT_STARTED", "TO_DO")


async def test_the_first_link_opens_the_club_s_account_and_sends_it_to_the_provider(
    client, payments
):
    club_id, desk = await a_desk(client, name="Ogrody 33")

    url = await asks_for_a_link(client, desk)

    [opened] = payments.called("open_club_account")
    [linked] = payments.called("onboarding_link")
    club_website = get_settings().CLUB_WEBSITE_URL.rstrip("/")
    account = payments.account_opened_for(UUID(club_id))
    assert opened.arguments["club_id"] == UUID(club_id)
    assert opened.arguments["name"] == "Ogrody 33"
    assert opened.arguments["email"] == DESK
    assert url == f"https://connect.payments.raketa.example/onboarding/{account}"
    assert linked.arguments["return_url"] == f"{club_website}/overview"
    assert linked.arguments["refresh_url"] == f"{club_website}/payments/continue"
    assert await payments_of(client, desk) == ("NOT_STARTED", "TO_DO")


async def test_every_link_is_fresh_and_the_account_is_opened_once(client, payments):
    """A link is single use, so *Continue with Stripe* always asks for a new
    one — for the account already opened, never a second."""

    club_id, desk = await a_desk(client)

    first = await asks_for_a_link(client, desk)
    await account_moves(client, payments, club_id, NEEDS_DETAILS, notice_id="evt_1")
    again = await asks_for_a_link(client, desk)

    assert len(payments.called("open_club_account")) == 1
    assert len(payments.called("onboarding_link")) == 2
    assert first == again  # the fake's link names the account, not the visit
    assert await payments_of(client, desk) == ("NEEDS_DETAILS", "TO_DO")


async def test_a_ready_account_is_given_no_link(client, payments):
    club_id, desk = await a_desk(client)
    await asks_for_a_link(client, desk)
    await account_moves(client, payments, club_id, READY, notice_id="evt_1")

    refused = await client.post(PAYMENTS_LINK, headers=desk)

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "payments_already_connected"
    assert len(payments.called("onboarding_link")) == 1


async def test_the_link_reads_the_account_it_sends_the_desk_to(client, payments):
    """A notice can be late, or lost: every link also reads the account as it
    stands, so *Continue* finds a club Stripe already finished with."""

    club_id, desk = await a_desk(client)
    await asks_for_a_link(client, desk)
    payments.club_account_is(payments.account_opened_for(UUID(club_id)), READY)

    await asks_for_a_link(client, desk)

    assert await payments_of(client, desk) == ("READY", "DONE")


async def test_a_ready_club_the_provider_stopped_is_given_a_link_before_its_notice(
    client, payments
):
    """A notice can be lost as well as late: a club recorded ready is asked
    about before it is refused, so *Continue with Stripe* is never withheld
    from an account the provider wants more from."""

    club_id, desk = await a_desk(client)
    await asks_for_a_link(client, desk)
    await account_moves(client, payments, club_id, READY, notice_id="evt_1")
    payments.club_account_is(payments.account_opened_for(UUID(club_id)), NEEDS_DETAILS)

    url = await asks_for_a_link(client, desk)

    assert url
    assert await payments_of(client, desk) == ("NEEDS_DETAILS", "TO_DO")


async def test_a_link_that_fails_keeps_the_account_the_provider_opened(
    client, payments, monkeypatch
):
    """The account is recorded before its link is asked for, so the next try
    continues it rather than opening a second."""

    club_id, desk = await a_desk(client)

    async def unreachable(*args, **kwargs):
        raise PaymentsUnavailable()

    with monkeypatch.context() as patched:
        patched.setattr(payments, "onboarding_link", unreachable)
        refused = await client.post(PAYMENTS_LINK, headers=desk)
    again = await asks_for_a_link(client, desk)

    assert refused.status_code == 503, refused.text
    assert again.endswith(payments.account_opened_for(UUID(club_id)))
    assert len(payments.called("open_club_account")) == 1


async def test_a_provider_that_cannot_be_reached_opens_nothing(client, payments):
    _, desk = await a_desk(client)
    payments.unreachable = True

    refused = await client.post(PAYMENTS_LINK, headers=desk)
    payments.unreachable = False

    assert refused.status_code == 503, refused.text
    assert refused.json()["code"] == "payments_unavailable"
    assert await payments_of(client, desk) == ("NOT_STARTED", "TO_DO")


async def test_only_a_desk_asks_for_a_link(client):
    from tests.api.administration_world import player_signs_up

    player = await player_signs_up(client)

    refused = await client.post(PAYMENTS_LINK, headers=player)

    assert refused.status_code == 401, refused.text


async def test_the_link_is_on_the_club_s_contract_alone(client):
    from app.api.contract import SURFACES, build_surface_spec

    documents = {
        surface: build_surface_spec(surface, SURFACES[surface])["paths"]
        for surface in ("player", "club", "public", "dev")
    }

    assert "/api/v1/club/payments/onboarding-link" in documents["club"]
    assert not [
        path
        for surface, paths in documents.items()
        for path in paths
        if "webhooks" in path or (surface != "club" and "onboarding-link" in path)
    ]


# ---------------------------------------------------------------------------
# Every status, through the webhook — and the checklist
# ---------------------------------------------------------------------------


async def test_the_club_goes_live_when_the_provider_says_its_account_is_ready(
    client, payments
):
    club_id, desk = await a_club_set_up_but_for_payments(client)
    assert (await setup_of(client, desk))["live"] is False

    await asks_for_a_link(client, desk)
    assert await payments_of(client, desk) == ("NOT_STARTED", "TO_DO")

    await account_moves(client, payments, club_id, NEEDS_DETAILS, notice_id="evt_1")
    assert await payments_of(client, desk) == ("NEEDS_DETAILS", "TO_DO")
    assert (await setup_of(client, desk))["live"] is False

    await account_moves(client, payments, club_id, READY, notice_id="evt_2")
    setup = await setup_of(client, desk)

    assert await payments_of(client, desk) == ("READY", "DONE")
    assert {row["state"] for row in setup["steps"]} == {"DONE"}
    assert setup["live"] is True


async def test_a_club_whose_charges_are_disabled_is_live_no_longer(
    client, payments, mailbox
):
    club_id, desk = await a_club_set_up_but_for_payments(client)
    await asks_for_a_link(client, desk)
    await account_moves(client, payments, club_id, READY, notice_id="evt_1")
    assert (await setup_of(client, desk))["live"] is True

    await account_moves(client, payments, club_id, NEEDS_DETAILS, notice_id="evt_2")
    setup = await setup_of(client, desk)

    assert await payments_of(client, desk) == ("NEEDS_DETAILS", "TO_DO")
    assert setup["live"] is False
    # And it is sent back to the provider with a link that continues.
    assert await asks_for_a_link(client, desk)


async def test_the_desk_is_emailed_when_a_ready_account_needs_attention(
    client, payments, mailbox
):
    club_id, desk = await a_club_set_up_but_for_payments(client)
    await asks_for_a_link(client, desk)
    await account_moves(client, payments, club_id, READY, notice_id="evt_1")

    await account_moves(client, payments, club_id, NEEDS_DETAILS, notice_id="evt_2")

    [email] = await mailbox.to(DESK)
    club_website = get_settings().CLUB_WEBSITE_URL.rstrip("/")
    assert email.kind == "payments.needs_attention.club"
    assert email.subject == "Stripe needs something from you"
    assert "Ogrody 33" in email.text
    assert f"{club_website}/payments/continue" in email.text
    assert f'href="{club_website}/payments/continue"' in email.html


async def test_a_club_still_signing_up_is_not_emailed(client, payments, mailbox):
    """A club in the middle of the provider's pages reads *Stripe needs more
    details* on its own Overview; the email is for an account that was taking
    payments and stopped."""

    club_id, desk = await a_desk(client)
    await asks_for_a_link(client, desk)

    await account_moves(client, payments, club_id, NEEDS_DETAILS, notice_id="evt_1")
    await account_moves(client, payments, club_id, READY, notice_id="evt_2")

    assert await mailbox.to(DESK) == []


async def test_a_ready_account_the_provider_forgets_is_not_started_and_emailed(
    client, payments, mailbox
):
    club_id, desk = await a_desk(client)
    await asks_for_a_link(client, desk)
    await account_moves(client, payments, club_id, READY, notice_id="evt_1")

    await account_moves(client, payments, club_id, NOT_STARTED, notice_id="evt_2")

    assert await payments_of(client, desk) == ("NOT_STARTED", "TO_DO")
    assert len(await mailbox.to(DESK)) == 1


async def test_a_status_the_club_already_has_records_and_sends_nothing(
    client, payments, mailbox
):
    club_id, desk = await a_desk(client)
    await asks_for_a_link(client, desk)
    await account_moves(client, payments, club_id, READY, notice_id="evt_1")
    await account_moves(client, payments, club_id, NEEDS_DETAILS, notice_id="evt_2")

    await account_moves(client, payments, club_id, NEEDS_DETAILS, notice_id="evt_3")

    assert len(await mailbox.to(DESK)) == 1


# ---------------------------------------------------------------------------
# The Connected accounts webhook: verified, read once, a prompt
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param(lambda body: {}, id="unsigned"),
        pytest.param(
            lambda body: signed(body, secret=PLATFORM_SECRET),
            id="signed-with-the-platform-endpoint-s-secret",
        ),
        pytest.param(
            lambda body: signed(body, at=int(time.time()) - 10 * 60),
            id="signed-ten-minutes-ago",
        ),
    ],
)
async def test_a_notice_that_cannot_be_verified_is_refused(client, headers):
    body = account_update("acct_1")

    refused = await stripe_says(client, body, headers(body))

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "payment_notice_refused"


async def test_a_laptop_with_no_connect_secret_reads_no_notice(client, monkeypatch):
    monkeypatch.delenv("STRIPE_CONNECT_WEBHOOK_SECRET")
    get_settings.cache_clear()

    refused = await stripe_says(client, account_update("acct_1"))

    assert refused.status_code == 503, refused.text
    assert refused.json()["code"] == "payment_notices_not_configured"


async def test_a_notice_delivered_again_is_read_once(client, payments):
    club_id, desk = await a_desk(client)
    await asks_for_a_link(client, desk)
    account = payments.account_opened_for(UUID(club_id))
    payments.club_account_is(account, READY)
    reads_before = len(payments.called("read_club_account"))
    body = account_update(account, notice_id="evt_ready")

    first = await stripe_says(client, body)
    again = await stripe_says(client, body)

    assert first.status_code == again.status_code == 204
    assert len(payments.called("read_club_account")) == reads_before + 1


async def test_notices_out_of_order_leave_the_account_as_it_stands(client, payments):
    """Stripe disables charges and enables them again, and the first notice
    arrives last: read off the notices the club would end not live; read from
    the provider it ends as it is."""

    club_id, desk = await a_desk(client)
    await asks_for_a_link(client, desk)
    account = payments.account_opened_for(UUID(club_id))
    payments.club_account_is(account, READY)

    await stripe_says(client, account_update(account, notice_id="evt_enabled"))
    await stripe_says(
        client,
        account_update(account, notice_id="evt_disabled", charges_enabled=False),
    )

    assert await payments_of(client, desk) == ("READY", "DONE")


async def test_a_notice_about_an_account_no_club_holds_is_acknowledged(
    client, payments
):
    told = await stripe_says(client, account_update("acct_nobody_s"))
    unheeded = await stripe_says(
        client,
        json.dumps(
            {
                "id": "evt_charge",
                "object": "event",
                "type": "charge.succeeded",
                "account": "acct_nobody_s",
                "data": {"object": {"id": "ch_1", "object": "charge"}},
            }
        ),
    )

    assert told.status_code == unheeded.status_code == 204


async def test_the_platform_endpoint_does_not_read_a_club_s_account(client, payments):
    """``account.updated`` on the platform endpoint is about the platform's own
    account: it names no connected account, and moves no club."""

    club_id, desk = await a_desk(client)
    await asks_for_a_link(client, desk)
    account = payments.account_opened_for(UUID(club_id))
    payments.club_account_is(account, READY)
    body = json.dumps(
        {
            "id": "evt_platform",
            "object": "event",
            "type": "account.updated",
            "data": {"object": {"id": account, "object": "account"}},
        }
    )

    told = await client.post(
        "/api/v1/webhooks/stripe",
        content=body.encode(),
        headers=signed(body, secret=PLATFORM_SECRET),
    )

    assert told.status_code == 204, told.text
    assert await payments_of(client, desk) == ("NOT_STARTED", "TO_DO")

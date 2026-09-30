"""What the payment provider must do, run against every implementation of it.

**A demand nobody executes is a demand satisfied by accident**
(``docs/adr/0098``). Every implementation registered in
``app/bootstrap/payments_demands.py`` is enrolled here: the **fake** always,
because local runs, seeds and every API test stand on it and a fake that drifts
from the provider is a green suite about a product that does not exist; and
**Stripe** only where a person has placed test keys (#533), skipped otherwise —
and skipped by name, so a run says which half of the contract it did not check.

**The phone is played by the suite.** A card is typed into Stripe's own fields on
a player's phone and never reaches the backend, so each implementation comes with
a *phone* that confirms a setup the way a device would: the fake is told which of
its test cards was entered; Stripe, in test mode, is confirmed server-side with
the matching test PaymentMethod. The cards are Stripe's own test cards — the last
four digits are theirs — so both halves are asked the same question.
"""

from __future__ import annotations

from typing import Callable, Protocol

import pytest

from app.bootstrap.payments_demands import (
    PAYMENTS_IMPLEMENTATIONS,
    RegisteredProvider,
)
from app.core.config import get_settings
from app.modules.payments.domain.errors import PaymentsUnavailable
from app.modules.payments.domain.provider import (
    ClubAccountStatus,
    PaymentProvider,
    PaymentStatus,
    RefundStatus,
    SetupStatus,
)
from app.modules.payments.domain.entered_cards import (
    A_CARD,
    A_CARD_THE_BANK_ALWAYS_CHECKS,
    A_CARD_THE_BANK_CHECKS_ONCE,
    A_CARD_THE_BANK_DECLINES,
    A_CARD_THAT_DECLINES_LATER,
    CardBehaviour,
    EnteredCard,
)
from app.modules.payments.infrastructure.fake_payments import FakePayments
from app.shared.ids import new_uuid


class Phone(Protocol):
    """What a player's phone does to a setup, played by the suite."""

    async def enters(self, setup_id: str, card: EnteredCard) -> None: ...

    async def authenticates(self, setup_id: str) -> None: ...


class FakePhone:
    def __init__(self, provider: FakePayments) -> None:
        self._provider = provider

    async def enters(self, setup_id: str, card: EnteredCard) -> None:
        self._provider.phone_enters(setup_id, card)

    async def authenticates(self, setup_id: str) -> None:
        self._provider.phone_authenticates(setup_id)


#: Stripe's test PaymentMethods, one per test card the fake mirrors.
STRIPE_TEST_METHODS = {
    A_CARD: "pm_card_visa",
    A_CARD_THE_BANK_DECLINES: "pm_card_visa_chargeDeclined",
    # Saved, then declined: a card that simulates an issuer decline cannot be
    # attached to a customer at all, so this is the one that saves.
    A_CARD_THAT_DECLINES_LATER: "pm_card_chargeCustomerFail",
    A_CARD_THE_BANK_CHECKS_ONCE: "pm_card_authenticationRequiredOnSetup",
    A_CARD_THE_BANK_ALWAYS_CHECKS: "pm_card_authenticationRequired",
}


class StripeTestPhone:
    """A phone in Stripe test mode: the setup is confirmed server-side with the
    test PaymentMethod standing for the card that was typed. A bank's check
    cannot be completed without a browser, so a demand that needs one is
    skipped here rather than faked."""

    def __init__(self) -> None:
        import stripe

        self._http = stripe.AIOHTTPClient()
        self._client = stripe.StripeClient(
            get_settings().STRIPE_SECRET_KEY or "", http_client=self._http
        )

    async def close(self) -> None:
        await self._http.close_async()

    async def enters(self, setup_id: str, card: EnteredCard) -> None:
        import stripe

        try:
            await self._client.v1.setup_intents.confirm_async(
                setup_id,
                params={
                    "payment_method": STRIPE_TEST_METHODS[card],
                    "return_url": "https://raketa.example/return",
                },
            )
        except stripe.CardError:
            # A declined setup is an answer the read below must report.
            pass

    async def authenticates(self, setup_id: str) -> None:
        pytest.skip("a bank's 3-D Secure check needs a browser in Stripe test mode")


PHONES: dict[str, Callable[[PaymentProvider], Phone]] = {
    "FakePayments": lambda provider: FakePhone(provider),  # type: ignore[arg-type]
    "StripePayments": lambda provider: StripeTestPhone(),
}


def registered() -> list:
    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in PAYMENTS_IMPLEMENTATIONS
    ]


def _built(implementation: RegisteredProvider) -> PaymentProvider:
    provider = implementation.build(get_settings())
    if provider is None:
        pytest.skip(f"{implementation.name}: {implementation.absent_because}")
    return provider


@pytest.fixture(params=registered())
async def provider(request):
    built = _built(request.param)
    yield built
    # Stripe's adapter owns an HTTP session per test, on that test's loop.
    close = getattr(built, "close", None)
    if close is not None:
        await close()


@pytest.fixture
async def phone(request, provider):
    implementation: RegisteredProvider = request.node.callspec.params["provider"]
    device = PHONES[implementation.name](provider)
    yield device
    close = getattr(device, "close", None)
    if close is not None:
        await close()


def _key() -> str:
    """A fresh idempotency key: a provider remembers a key for a day, so a key
    reused across two runs of this suite would answer the last run's object."""

    return f"raketa-demands-{new_uuid()}"


async def _saved(provider: PaymentProvider, phone: Phone, card: EnteredCard):
    customer_id = await provider.open_customer(
        player_id=new_uuid(), idempotency_key=_key()
    )
    setup = await provider.start_setup(
        customer_id=customer_id, player_id=new_uuid(), idempotency_key=_key()
    )
    await phone.enters(setup.setup_id, card)
    if card.behaviour in (
        CardBehaviour.CHECKED_AT_SETUP,
        CardBehaviour.CHECKED_EVERY_TIME,
    ):
        await phone.authenticates(setup.setup_id)
    reading = await provider.read_setup(setup.setup_id)
    return customer_id, reading


# ---------------------------------------------------------------------------
# The register checks itself
# ---------------------------------------------------------------------------


def test_the_fake_is_registered_and_always_runs():
    """The fake is what every API test and every seed stands on, so it may never
    be the implementation that is skipped."""

    fake = [i for i in PAYMENTS_IMPLEMENTATIONS if i.name == "FakePayments"]

    assert len(fake) == 1
    assert fake[0].build(get_settings()) is not None


def test_every_registered_implementation_has_a_phone():
    """An implementation with no phone could never be asked about a setup."""

    assert {i.name for i in PAYMENTS_IMPLEMENTATIONS} == set(PHONES)


def test_every_implementation_satisfies_the_port(provider):
    assert isinstance(provider, PaymentProvider)
    assert provider.publishable_key()


# ---------------------------------------------------------------------------
# Players: a customer, and a setup
# ---------------------------------------------------------------------------


async def test_one_key_opens_one_customer(provider):
    """**The same key twice is the same customer**, which is what makes a
    request retried after a timeout safe; a different player is another."""

    player = new_uuid()
    key = _key()

    first = await provider.open_customer(player_id=player, idempotency_key=key)
    again = await provider.open_customer(player_id=player, idempotency_key=key)
    other = await provider.open_customer(player_id=new_uuid(), idempotency_key=_key())

    assert first == again
    assert other != first


async def test_a_setup_nobody_confirmed_saves_nothing(provider):
    player = new_uuid()
    customer_id = await provider.open_customer(player_id=player, idempotency_key=_key())
    key = _key()
    setup = await provider.start_setup(
        customer_id=customer_id, player_id=player, idempotency_key=key
    )
    again = await provider.start_setup(
        customer_id=customer_id, player_id=player, idempotency_key=key
    )

    reading = await provider.read_setup(setup.setup_id)

    assert again.setup_id == setup.setup_id
    assert setup.client_secret
    assert reading.status is SetupStatus.AWAITING_THE_PHONE
    assert reading.customer_id == customer_id
    assert reading.client_secret == setup.client_secret
    assert reading.card is None


async def test_a_confirmed_setup_saves_the_card(provider, phone):
    _, reading = await _saved(provider, phone, A_CARD)

    assert reading.status is SetupStatus.SUCCEEDED
    assert reading.card is not None
    assert (reading.card.brand, reading.card.last_four) == ("visa", "4242")
    assert reading.card.wallet is None
    assert reading.card.method_id


async def test_a_card_the_bank_declines_is_not_saved_and_the_setup_can_try_again(
    provider, phone
):
    customer_id = await provider.open_customer(
        player_id=new_uuid(), idempotency_key=_key()
    )
    setup = await provider.start_setup(
        customer_id=customer_id, player_id=new_uuid(), idempotency_key=_key()
    )

    await phone.enters(setup.setup_id, A_CARD_THE_BANK_DECLINES)
    declined = await provider.read_setup(setup.setup_id)
    await phone.enters(setup.setup_id, A_CARD)
    saved = await provider.read_setup(setup.setup_id)

    assert declined.status is SetupStatus.DECLINED
    assert declined.card is None
    assert saved.status is SetupStatus.SUCCEEDED


async def test_a_card_the_bank_checks_waits_for_the_check(provider, phone):
    customer_id = await provider.open_customer(
        player_id=new_uuid(), idempotency_key=_key()
    )
    setup = await provider.start_setup(
        customer_id=customer_id, player_id=new_uuid(), idempotency_key=_key()
    )

    await phone.enters(setup.setup_id, A_CARD_THE_BANK_CHECKS_ONCE)
    checking = await provider.read_setup(setup.setup_id)
    await phone.authenticates(setup.setup_id)
    saved = await provider.read_setup(setup.setup_id)

    assert checking.status is SetupStatus.AUTHENTICATING
    assert saved.status is SetupStatus.SUCCEEDED


async def test_a_released_card_can_be_released_again(provider, phone):
    """Releasing is idempotent, which is what lets it be retried from the
    outbox after a crash between the release and its mark."""

    _, reading = await _saved(provider, phone, A_CARD)
    assert reading.card is not None

    await provider.release_method(reading.card.method_id, idempotency_key=_key())
    await provider.release_method(reading.card.method_id, idempotency_key=_key())


async def test_a_cancelled_setup_can_never_save_anything(provider):
    """A setup a newer one replaced is closed, so a phone still holding its
    secret cannot save a card with it that nobody records."""

    customer_id = await provider.open_customer(
        player_id=new_uuid(), idempotency_key=_key()
    )
    setup = await provider.start_setup(
        customer_id=customer_id, player_id=new_uuid(), idempotency_key=_key()
    )

    cancelled = await provider.cancel_setup(setup.setup_id, idempotency_key=_key())
    read_after = await provider.read_setup(setup.setup_id)

    assert cancelled.status is SetupStatus.CANCELLED
    assert read_after.status is SetupStatus.CANCELLED
    assert read_after.card is None


async def test_a_setup_that_saved_a_card_answers_it_rather_than_cancelling(
    provider, phone
):
    """A saved setup cannot be cancelled; what it saved is the caller's to
    release, so the answer carries it."""

    _, saved = await _saved(provider, phone, A_CARD)

    answered = await provider.cancel_setup(saved.setup_id, idempotency_key=_key())

    assert answered.status is SetupStatus.SUCCEEDED
    assert answered.card == saved.card


async def test_a_saved_card_is_read_as_it_stands(provider, phone):
    _, saved = await _saved(provider, phone, A_CARD)
    assert saved.card is not None

    card = await provider.read_card(saved.card.method_id)

    assert card == saved.card


async def test_a_key_reused_with_other_arguments_is_refused(provider):
    """**A bug, not an outage**: Stripe refuses it, and a fake that answered it
    would hide the bug from every test standing on it."""

    key = _key()
    await provider.open_customer(player_id=new_uuid(), idempotency_key=key)

    with pytest.raises(Exception) as refused:
        await provider.open_customer(player_id=new_uuid(), idempotency_key=key)

    assert not isinstance(refused.value, PaymentsUnavailable)


# ---------------------------------------------------------------------------
# Clubs: a connected account
# ---------------------------------------------------------------------------


async def test_a_new_club_account_is_not_ready_and_has_an_onboarding_link(provider):
    club = new_uuid()
    key = _key()

    account = await provider.open_club_account(
        club_id=club,
        name="Bonarka Arena",
        email="desk@raketa.example",
        idempotency_key=key,
    )
    again = await provider.open_club_account(
        club_id=club,
        name="Bonarka Arena",
        email="desk@raketa.example",
        idempotency_key=key,
    )
    reading = await provider.read_club_account(account)
    link = await provider.onboarding_link(
        account,
        refresh_url="https://club.raketa.example/payments/refresh",
        return_url="https://club.raketa.example/payments/return",
    )
    payouts = await provider.payouts(account, limit=10)

    assert again == account
    assert reading.account_id == account
    assert reading.status is not ClubAccountStatus.READY
    assert not reading.charges_enabled
    assert link.startswith("https://")
    assert payouts == ()


# ---------------------------------------------------------------------------
# Money, on a club's account
# ---------------------------------------------------------------------------


@pytest.fixture
async def club_account(provider) -> str:
    """A club account that can take payments. The fake's is made ready by the
    suite; Stripe's has to be onboarded by a person, once, and named."""

    if isinstance(provider, FakePayments):
        account = await provider.open_club_account(
            club_id=new_uuid(),
            name="Bonarka Arena",
            email="desk@raketa.example",
            idempotency_key=_key(),
        )
        provider.club_account_is(account, ClubAccountStatus.READY)
        return account
    account = get_settings().STRIPE_TEST_CLUB_ACCOUNT
    if not account:
        pytest.skip("STRIPE_TEST_CLUB_ACCOUNT names no onboarded test club account")
    return account


async def _cloned(provider, phone, club_account, card: EnteredCard) -> str:
    customer_id, reading = await _saved(provider, phone, card)
    assert reading.card is not None
    return await provider.clone_method(
        customer_id=customer_id,
        method_id=reading.card.method_id,
        account_id=club_account,
        idempotency_key=_key(),
    )


async def test_an_authorised_payment_is_captured_whole(provider, phone, club_account):
    """**The fill's two halves**: hold every seat, then take them all."""

    clone = await _cloned(provider, phone, club_account, A_CARD)
    key = _key()

    held = await provider.authorise(
        account_id=club_account,
        method_id=clone,
        amount_grosze=4000,
        description="Padel · Bonarka Arena",
        metadata={"seat": "demands"},
        idempotency_key=key,
    )
    held_again = await provider.authorise(
        account_id=club_account,
        method_id=clone,
        amount_grosze=4000,
        description="Padel · Bonarka Arena",
        metadata={"seat": "demands"},
        idempotency_key=key,
    )
    taken = await provider.capture(
        account_id=club_account, payment_id=held.payment_id, idempotency_key=_key()
    )

    assert held.status is PaymentStatus.AUTHORISED
    assert held.amount_grosze == 4000
    assert held_again.payment_id == held.payment_id
    assert taken.status is PaymentStatus.CAPTURED
    assert taken.amount_grosze == 4000


async def test_a_held_payment_can_be_released_untaken(provider, phone, club_account):
    """**If one seat fails, nobody pays**: every other hold is cancelled."""

    clone = await _cloned(provider, phone, club_account, A_CARD)
    held = await provider.authorise(
        account_id=club_account,
        method_id=clone,
        amount_grosze=4000,
        description="Padel · Bonarka Arena",
        metadata={},
        idempotency_key=_key(),
    )

    released = await provider.cancel(
        account_id=club_account, payment_id=held.payment_id, idempotency_key=_key()
    )

    assert released.status is PaymentStatus.CANCELLED


async def test_a_payment_released_untaken_can_never_be_taken(
    provider, phone, club_account
):
    clone = await _cloned(provider, phone, club_account, A_CARD)
    held = await provider.authorise(
        account_id=club_account,
        method_id=clone,
        amount_grosze=4000,
        description="Padel · Bonarka Arena",
        metadata={},
        idempotency_key=_key(),
    )
    await provider.cancel(
        account_id=club_account, payment_id=held.payment_id, idempotency_key=_key()
    )

    with pytest.raises(Exception) as refused:
        await provider.capture(
            account_id=club_account,
            payment_id=held.payment_id,
            idempotency_key=_key(),
        )

    assert not isinstance(refused.value, PaymentsUnavailable)


async def test_a_card_that_declines_later_is_declined_off_session(
    provider, phone, club_account
):
    clone = await _cloned(provider, phone, club_account, A_CARD_THAT_DECLINES_LATER)

    declined = await provider.authorise(
        account_id=club_account,
        method_id=clone,
        amount_grosze=4000,
        description="Padel · Bonarka Arena",
        metadata={},
        idempotency_key=_key(),
    )

    assert declined.status is PaymentStatus.DECLINED
    assert declined.decline_code


async def test_a_bank_that_wants_the_player_present_says_so(
    provider, phone, club_account
):
    """Rare, and allowed even with permission on file: the player confirms the
    same payment in the app, so its secret comes back with the answer."""

    clone = await _cloned(provider, phone, club_account, A_CARD_THE_BANK_ALWAYS_CHECKS)

    wanted = await provider.authorise(
        account_id=club_account,
        method_id=clone,
        amount_grosze=4000,
        description="Padel · Bonarka Arena",
        metadata={},
        idempotency_key=_key(),
    )

    assert wanted.status is PaymentStatus.AUTHENTICATION_REQUIRED
    assert wanted.client_secret


async def test_a_rescue_is_charged_at_once(provider, phone, club_account):
    clone = await _cloned(provider, phone, club_account, A_CARD)

    taken = await provider.charge_now(
        account_id=club_account,
        method_id=clone,
        amount_grosze=2700,
        description="Padel · Bonarka Arena",
        metadata={},
        idempotency_key=_key(),
    )

    assert taken.status is PaymentStatus.CAPTURED
    assert taken.amount_grosze == 2700


async def test_a_refund_keeps_the_card_fee_back_only_when_asked(
    provider, phone, club_account
):
    """**Leaving before the cut-off** is refunded minus the card fee; **a game
    called off at the cut-off** is refunded in full (the mechanics §12.3)."""

    async def captured() -> str:
        clone = await _cloned(provider, phone, club_account, A_CARD)
        taken = await provider.charge_now(
            account_id=club_account,
            method_id=clone,
            amount_grosze=4000,
            description="Padel · Bonarka Arena",
            metadata={},
            idempotency_key=_key(),
        )
        return taken.payment_id

    left = await provider.refund(
        account_id=club_account,
        payment_id=await captured(),
        withhold_fee=True,
        idempotency_key=_key(),
    )
    called_off = await provider.refund(
        account_id=club_account,
        payment_id=await captured(),
        withhold_fee=False,
        idempotency_key=_key(),
    )

    assert 0 < left.fee_withheld_grosze < 4000
    assert left.amount_grosze == 4000 - left.fee_withheld_grosze
    assert left.status in (RefundStatus.PENDING, RefundStatus.SUCCEEDED)
    assert (called_off.amount_grosze, called_off.fee_withheld_grosze) == (4000, 0)

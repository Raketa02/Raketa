"""The payment provider, over Stripe (``docs/adr/0189`` §4; the mechanics Appendix A).

**Connect with direct charges on the club's account.** A club is a connected
account opened with **Accounts v2** — the ``merchant`` configuration, the club
paying Stripe's fees and Stripe covering its losses (``fees_collector`` and
``losses_collector`` both ``stripe``), so the club is the merchant of record and
Raketa pays no Connect fee. A player is a **v1 Customer** on the platform, the
only kind the phone's payment fields accept; their card is saved there once, in
a SetupIntent for off-session use, and **cloned onto the club's account** for
each charge — a clone is single use, and every PaymentIntent is created on the
club's account with its ``Stripe-Account`` header.

**Every write carries the caller's idempotency key**, and the SDK reuses it
across its own retries — which are **off by default** in stripe-python and
switched on here (``max_network_retries``). A key reused with different
arguments is a bug and raises.

**Outages become ``PaymentsUnavailable``; outcomes become statuses.** A card
refused off-session is a 402 ``CardError`` whose PaymentIntent is read out of
the error: ``authentication_required`` is the bank wanting the player present,
anything else a decline with its code. A request Stripe calls invalid is a bug in
this adapter and is raised as it came, never dressed as an outage.

**Verified against stripe-python 15.6.1's own source** (the version the lock
pins, and with it the API version it sends), and held to the same demands as the
fake wherever a person has placed test keys (#533). What only a live test key
could confirm is listed in ``tests/demands/test_payments_demands.py``'s skips.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Literal, Mapping, TypeVar, final
from uuid import UUID

import stripe

from app.kernel import instant, invariant
from app.modules.payments.domain.errors import PaymentsUnavailable
from app.modules.payments.domain.provider import (
    CardOnFile,
    ClubAccountReading,
    ClubAccountStatus,
    Payment,
    PaymentStatus,
    Payout,
    PayoutStatus,
    Refund,
    RefundStatus,
    SetupReading,
    SetupStatus,
    StartedSetup,
    Wallet,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

#: Every amount is złoty, in grosze.
CURRENCY = "pln"

#: How many times the SDK retries a request that failed on the network, with the
#: same idempotency key. Off by default in stripe-python.
NETWORK_RETRIES = 2

#: The errors that mean *Stripe could not be asked*, rather than *Stripe
#: answered*: the network, a rate limit, Stripe's own failure — and a key it
#: refuses, which is a configuration fault a retry will not fix but which is
#: still about the platform and never about the player.
_OUTAGES = (
    stripe.APIConnectionError,
    stripe.RateLimitError,
    stripe.APIError,
    stripe.AuthenticationError,
    stripe.PermissionError,
)

_WALLETS = {"apple_pay": Wallet.APPLE_PAY, "google_pay": Wallet.GOOGLE_PAY}

_PAYMENT_STATUSES = {
    "requires_capture": PaymentStatus.AUTHORISED,
    "succeeded": PaymentStatus.CAPTURED,
    "canceled": PaymentStatus.CANCELLED,
    "requires_action": PaymentStatus.AUTHENTICATION_REQUIRED,
    "requires_payment_method": PaymentStatus.DECLINED,
    "requires_confirmation": PaymentStatus.PROCESSING,
    "processing": PaymentStatus.PROCESSING,
}

_REFUND_STATUSES = {
    "pending": RefundStatus.PENDING,
    "requires_action": RefundStatus.PENDING,
    "succeeded": RefundStatus.SUCCEEDED,
    "failed": RefundStatus.FAILED,
    "canceled": RefundStatus.FAILED,
}

_PAYOUT_STATUSES = {
    "pending": PayoutStatus.PENDING,
    "in_transit": PayoutStatus.IN_TRANSIT,
    "paid": PayoutStatus.PAID,
    "failed": PayoutStatus.FAILED,
    "canceled": PayoutStatus.CANCELLED,
}


def card_of(method: Mapping[str, Any]) -> CardOnFile:
    """A Stripe PaymentMethod, as plain JSON, as a card on file — the webhook's
    body, or an SDK object's ``to_dict()``: stripe-python's objects are not
    dicts, and read an absent field as an error rather than as nothing."""

    card = method["card"]
    wallet = card.get("wallet")
    return CardOnFile(
        method_id=method["id"],
        brand=card["brand"],
        last_four=card["last4"],
        wallet=_WALLETS.get(wallet["type"]) if wallet else None,
    )


@final
class StripePayments:
    """``PaymentProvider`` over Stripe."""

    def __init__(
        self,
        *,
        secret_key: str,
        publishable_key: str,
        timeout_seconds: float,
    ) -> None:
        # aiohttp, because it is already a runtime dependency; stripe-python's
        # default async client is httpx, which this backend installs for its
        # tests only.
        self._http = stripe.AIOHTTPClient(timeout=timeout_seconds)
        self._client = stripe.StripeClient(
            secret_key,
            http_client=self._http,
            max_network_retries=NETWORK_RETRIES,
        )
        self._publishable_key = publishable_key

    async def close(self) -> None:
        """Close the HTTP session. ``StripeClient`` has no close of its own."""

        await self._http.close_async()

    def publishable_key(self) -> str:
        return self._publishable_key

    # ------------------------------------------------------ players, on the platform

    async def open_customer(self, *, player_id: UUID, idempotency_key: str) -> str:
        # Nothing about the person but their id: Stripe needs no name or email
        # to hold a card, and Raketa sends none it does not need.
        customer = await self._call(
            self._client.v1.customers.create_async(
                params={"metadata": {"raketa_player_id": str(player_id)}},
                options={"idempotency_key": idempotency_key},
            )
        )
        return customer.id

    async def start_setup(
        self, *, customer_id: str, player_id: UUID, idempotency_key: str
    ) -> StartedSetup:
        setup = await self._call(
            self._client.v1.setup_intents.create_async(
                params={
                    "customer": customer_id,
                    "usage": "off_session",
                    # Cards and the wallets, which save cards. BLIK waits on
                    # Stripe (open item O1) and Przelewy24 cannot be saved.
                    "payment_method_types": ["card"],
                    "metadata": {"raketa_player_id": str(player_id)},
                },
                options={"idempotency_key": idempotency_key},
            )
        )
        secret = setup.client_secret
        invariant(secret is not None, "a setup with no secret")
        assert secret is not None
        return StartedSetup(setup_id=setup.id, client_secret=secret)

    async def read_setup(self, setup_id: str) -> SetupReading:
        setup = await self._call(
            self._client.v1.setup_intents.retrieve_async(
                setup_id, params={"expand": ["payment_method"]}
            )
        )
        status = self._setup_status(
            setup.status, declined=bool(getattr(setup, "last_setup_error", None))
        )
        method = setup.payment_method
        invariant(
            not isinstance(method, str), "a setup read without its method expanded"
        )
        card = (
            card_of(method.to_dict())
            if status is SetupStatus.SUCCEEDED
            and method is not None
            and not isinstance(method, str)
            else None
        )
        customer = setup.customer
        return SetupReading(
            setup_id=setup.id,
            customer_id=(
                customer
                if isinstance(customer, str)
                else customer.id
                if customer is not None
                else ""
            ),
            status=status,
            client_secret=setup.client_secret or "",
            card=card,
        )

    @staticmethod
    def _setup_status(status: str, *, declined: bool) -> SetupStatus:
        if status == "succeeded":
            return SetupStatus.SUCCEEDED
        if status == "requires_action":
            return SetupStatus.AUTHENTICATING
        if status == "processing":
            return SetupStatus.PROCESSING
        if status == "canceled":
            return SetupStatus.CANCELLED
        if status == "requires_payment_method" and declined:
            return SetupStatus.DECLINED
        return SetupStatus.AWAITING_THE_PHONE

    async def cancel_setup(
        self, setup_id: str, *, idempotency_key: str
    ) -> SetupReading:
        # A succeeded setup cannot be cancelled, and Stripe says so as an invalid
        # request; the reading after says which of the two it was, and a saved
        # card in it is the caller's to release.
        try:
            await self._call(
                self._client.v1.setup_intents.cancel_async(
                    setup_id, options={"idempotency_key": idempotency_key}
                )
            )
        except stripe.InvalidRequestError:
            reading = await self.read_setup(setup_id)
            if reading.status is not SetupStatus.SUCCEEDED:
                raise
            return reading
        return await self.read_setup(setup_id)

    async def read_card(self, method_id: str) -> CardOnFile:
        method = await self._call(
            self._client.v1.payment_methods.retrieve_async(method_id)
        )
        return card_of(method.to_dict())

    async def release_method(self, method_id: str, *, idempotency_key: str) -> None:
        # Detaching is permanent: a detached card can never be charged or
        # attached again. Detaching one already detached is refused by Stripe as
        # an invalid request, which is the answer this port calls success.
        try:
            await self._call(
                self._client.v1.payment_methods.detach_async(
                    method_id, options={"idempotency_key": idempotency_key}
                )
            )
        except stripe.InvalidRequestError:
            method = await self._call(
                self._client.v1.payment_methods.retrieve_async(method_id)
            )
            if method.customer is not None:
                raise

    # ------------------------------------------------ clubs, as connected accounts

    async def open_club_account(
        self, *, club_id: UUID, name: str, email: str, idempotency_key: str
    ) -> str:
        account = await self._call(
            self._client.v2.core.accounts.create_async(
                params={
                    "contact_email": email,
                    "display_name": name,
                    "dashboard": "full",
                    "identity": {"country": "pl", "entity_type": "company"},
                    "defaults": {
                        "currency": CURRENCY,
                        "locales": ["pl-PL"],
                        # Set with the merchant configuration and never again:
                        # the club pays Stripe's fees, Stripe covers its losses.
                        "responsibilities": {
                            "fees_collector": "stripe",
                            "losses_collector": "stripe",
                        },
                    },
                    "configuration": {
                        "merchant": {
                            "capabilities": {"card_payments": {"requested": True}}
                        }
                    },
                    "metadata": {"raketa_club_id": str(club_id)},
                },
                options={"idempotency_key": idempotency_key},
            )
        )
        return account.id

    async def onboarding_link(
        self, account_id: str, *, refresh_url: str, return_url: str
    ) -> str:
        # One kind of link for the first visit and for continuing: an account
        # with Stripe's own dashboard is not given the *update* link.
        link = await self._call(
            self._client.v2.core.account_links.create_async(
                params={
                    "account": account_id,
                    "use_case": {
                        "type": "account_onboarding",
                        "account_onboarding": {
                            "configurations": ["merchant"],
                            "refresh_url": refresh_url,
                            "return_url": return_url,
                        },
                    },
                }
            )
        )
        return link.url

    async def read_club_account(self, account_id: str) -> ClubAccountReading:
        # Read through v1, which answers for a v2 account and is the one shape
        # that says whether details were ever submitted — v2 has no such field.
        account = await self._call(self._client.v1.accounts.retrieve_async(account_id))
        # Ready means the club can both take a share and be paid it out.
        # Anything short of that with details submitted — Stripe still
        # verifying included — reads as needing details; #537 draws it.
        charges = bool(account.charges_enabled)
        payouts = bool(account.payouts_enabled)
        if charges and payouts:
            status = ClubAccountStatus.READY
        elif not account.details_submitted:
            status = ClubAccountStatus.NOT_STARTED
        else:
            status = ClubAccountStatus.NEEDS_DETAILS
        return ClubAccountReading(
            account_id=account_id,
            status=status,
            charges_enabled=charges,
            payouts_enabled=payouts,
        )

    async def payouts(self, account_id: str, *, limit: int) -> tuple[Payout, ...]:
        page = await self._call(
            self._client.v1.payouts.list_async(
                params={"limit": limit}, options={"stripe_account": account_id}
            )
        )
        return tuple(
            Payout(
                payout_id=payout.id,
                amount_grosze=payout.amount,
                arrives_at=instant(
                    datetime.fromtimestamp(payout.arrival_date, tz=timezone.utc)
                ),
                status=_PAYOUT_STATUSES[payout.status],
            )
            for payout in page.data
        )

    # ------------------------------------------------ money, on the club's account

    async def clone_method(
        self,
        *,
        customer_id: str,
        method_id: str,
        account_id: str,
        idempotency_key: str,
    ) -> str:
        clone = await self._call(
            self._client.v1.payment_methods.create_async(
                params={"customer": customer_id, "payment_method": method_id},
                options={
                    "stripe_account": account_id,
                    "idempotency_key": idempotency_key,
                },
            )
        )
        return clone.id

    async def authorise(
        self,
        *,
        account_id: str,
        method_id: str,
        amount_grosze: int,
        description: str,
        metadata: Mapping[str, str],
        idempotency_key: str,
    ) -> Payment:
        return await self._pay(
            account_id=account_id,
            method_id=method_id,
            amount_grosze=amount_grosze,
            description=description,
            metadata=metadata,
            idempotency_key=idempotency_key,
            capture_method="manual",
        )

    async def charge_now(
        self,
        *,
        account_id: str,
        method_id: str,
        amount_grosze: int,
        description: str,
        metadata: Mapping[str, str],
        idempotency_key: str,
    ) -> Payment:
        # `automatic`, not the default `automatic_async`: the charge's fee is
        # then known in the answer, and a refund that withholds it can be made
        # at once rather than an hour later.
        return await self._pay(
            account_id=account_id,
            method_id=method_id,
            amount_grosze=amount_grosze,
            description=description,
            metadata=metadata,
            idempotency_key=idempotency_key,
            capture_method="automatic",
        )

    async def _pay(
        self,
        *,
        account_id: str,
        method_id: str,
        amount_grosze: int,
        description: str,
        metadata: Mapping[str, str],
        idempotency_key: str,
        capture_method: Literal["manual", "automatic"],
    ) -> Payment:
        try:
            intent = await self._call(
                self._client.v1.payment_intents.create_async(
                    params={
                        "amount": amount_grosze,
                        "currency": CURRENCY,
                        # The clone, which belongs to no customer on the club's
                        # account — so none is named.
                        "payment_method": method_id,
                        "payment_method_types": ["card"],
                        "capture_method": capture_method,
                        "off_session": True,
                        "confirm": True,
                        "description": description,
                        "metadata": dict(metadata),
                    },
                    options={
                        "stripe_account": account_id,
                        "idempotency_key": idempotency_key,
                    },
                )
            )
        except stripe.CardError as refusal:
            refused = refusal.error.payment_intent if refusal.error else None
            if refused is None:
                raise
            wanted = refusal.code == "authentication_required"
            return Payment(
                payment_id=refused.id,
                status=(
                    PaymentStatus.AUTHENTICATION_REQUIRED
                    if wanted
                    else PaymentStatus.DECLINED
                ),
                amount_grosze=refused.amount,
                client_secret=refused.client_secret if wanted else None,
                decline_code=(
                    None
                    if wanted
                    else (refusal.error.decline_code if refusal.error else None)
                    or refusal.code
                ),
            )
        return self._payment_of(intent)

    async def capture(
        self, *, account_id: str, payment_id: str, idempotency_key: str
    ) -> Payment:
        intent = await self._call(
            self._client.v1.payment_intents.capture_async(
                payment_id,
                options={
                    "stripe_account": account_id,
                    "idempotency_key": idempotency_key,
                },
            )
        )
        return self._payment_of(intent)

    async def cancel(
        self, *, account_id: str, payment_id: str, idempotency_key: str
    ) -> Payment:
        intent = await self._call(
            self._client.v1.payment_intents.cancel_async(
                payment_id,
                options={
                    "stripe_account": account_id,
                    "idempotency_key": idempotency_key,
                },
            )
        )
        return self._payment_of(intent)

    async def refund(
        self,
        *,
        account_id: str,
        payment_id: str,
        withhold_fee: bool,
        idempotency_key: str,
    ) -> Refund:
        intent = await self._call(
            self._client.v1.payment_intents.retrieve_async(
                payment_id,
                params={"expand": ["latest_charge.balance_transaction"]},
                options={"stripe_account": account_id},
            )
        )
        charge = intent.latest_charge
        # What is left to give back: a share is refunded once, but a payment
        # refunded in part before would otherwise be refunded past its total.
        remaining = intent.amount_received - (
            getattr(charge, "amount_refunded", 0) or 0
        )
        fee = 0
        if withhold_fee:
            # Stripe never returns its processing fee on a refund, and this is
            # the fee it took: the charge's balance transaction, on the club's
            # account — which settles in złoty, so the two amounts share a unit.
            settled = getattr(charge, "balance_transaction", None)
            if settled is None:
                raise PaymentsUnavailable("the charge's fee is not known yet")
            invariant(settled.currency == CURRENCY, "a club settling outside złoty")
            fee = settled.fee
        # A share is at least 2,50 zł (the club's price floor over four seats)
        # and its fee about 1,04 zł, so there is always something to give back.
        invariant(remaining - fee > 0, "a refund of nothing")
        refund = await self._call(
            self._client.v1.refunds.create_async(
                # No reason: Stripe's three are a customer's request, a
                # duplicate and fraud, and a game called off is none of them.
                params={"payment_intent": payment_id, "amount": remaining - fee},
                options={
                    "stripe_account": account_id,
                    "idempotency_key": idempotency_key,
                },
            )
        )
        return Refund(
            refund_id=refund.id,
            status=_REFUND_STATUSES.get(refund.status or "", RefundStatus.PENDING),
            amount_grosze=refund.amount,
            fee_withheld_grosze=fee,
        )

    # -------------------------------------------------------------- internals

    @staticmethod
    def _payment_of(intent: Any) -> Payment:
        status = _PAYMENT_STATUSES[intent.status]
        # Unlike an error raised, a PaymentIntent's last error omits every field
        # it has no value for, and the SDK reads an absent one as an error.
        failure = getattr(intent, "last_payment_error", None)
        return Payment(
            payment_id=intent.id,
            status=status,
            amount_grosze=intent.amount,
            client_secret=(
                intent.client_secret
                if status is PaymentStatus.AUTHENTICATION_REQUIRED
                else None
            ),
            decline_code=(
                (
                    getattr(failure, "decline_code", None)
                    or getattr(failure, "code", None)
                )
                if status is PaymentStatus.DECLINED
                else None
            ),
        )

    @staticmethod
    async def _call(operation: Awaitable[T]) -> T:
        try:
            return await operation
        except _OUTAGES as outage:
            # The request id is what Stripe's support would ask for; the
            # message may carry nothing of a card, and the key never reaches it.
            logger.warning(
                "payments.stripe.unavailable",
                extra={
                    "error": type(outage).__name__,
                    "request_id": getattr(outage, "request_id", None),
                },
            )
            raise PaymentsUnavailable() from outage

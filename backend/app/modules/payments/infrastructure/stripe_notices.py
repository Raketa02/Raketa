"""Stripe's webhook, verified and read as a notice in Rakieta's words.

**Verified before a byte of it is read.** A notice is signed with the platform
endpoint's secret — ``Stripe-Signature: t=…,v1=…``, an HMAC-SHA256 over the
timestamp and the raw body — and checked by stripe-python's own verifier with a
**five-minute tolerance**, which the verifier leaves off unless asked (0 would
accept a notice replayed a year later). Anything unsigned, signed with another
secret, too old or not text is refused whole.

**Whichever provider this process pays through**, the notices come from Stripe:
a laptop on the fake receives none and holds no secret, so every notice is
answered ``payment_notices_not_configured``.

**One reader per endpoint, each over its own secret.** The platform endpoint
notifies about the platform's own objects — a setup that succeeded, a card its
bank updated. The **Connected accounts** endpoint (#537) notifies about each
club's account and the payments made on it: a notice there names the connected
account **at its top level** (``account``) — ``account.updated``, and the
``payment_intent.*`` kinds of a seat's payment (#541), which name the
PaymentIntent and nothing of its state — and ``charge.updated`` on that
payment's charge, which is how Stripe says **the fee kept on it is ready**
(#641): a club on its own negotiated pricing learns its fees after the take, so
the payment is read again and the fee recorded. Stripe still sends that
v1 notice for an Accounts v2 account, to a Connected accounts endpoint and never
to the platform's — where an ``account.updated`` names no connected account and
is about the platform itself, so it is read as nothing. Every other kind is
``Unheeded`` and acknowledged.
"""

from __future__ import annotations

import json
from typing import final

import stripe

from app.modules.payments.domain.errors import (
    PaymentNoticeRefused,
    PaymentNoticesNotConfigured,
)
from app.modules.payments.domain.notices import (
    CardUpdatedByBank,
    ConnectedAccountChanged,
    Notice,
    SeatPaymentChanged,
    SetupSucceeded,
    Unheeded,
)

#: How old a signed notice may be, in seconds: the libraries' own default,
#: which their verifier applies only when it is passed.
TOLERANCE_SECONDS = 300

#: Stripe's word that a captured payment's charge changed — its fee became
#: readable (#641; "readiness is signalled by ``charge.updated``"). A prompt to
#: read the payment again, like every other.
FEE_READY_KIND = "charge.updated"

#: The kinds that say a seat's payment moved (the mechanics Appendix A): held,
#: taken, released, refused, or waiting for its player. Each is only a prompt.
SEAT_PAYMENT_KINDS = frozenset(
    {
        "payment_intent.amount_capturable_updated",
        "payment_intent.succeeded",
        "payment_intent.canceled",
        "payment_intent.payment_failed",
        "payment_intent.requires_action",
    }
)


@final
class StripeNotices:
    """``PaymentNotices`` for one of Stripe's two endpoints, by its secret."""

    def __init__(self, *, secret: str | None) -> None:
        self._secret = secret

    def read(self, payload: bytes, *, signature: str | None) -> Notice:
        if not self._secret:
            raise PaymentNoticesNotConfigured()
        if not signature:
            raise PaymentNoticeRefused()
        try:
            body = payload.decode("utf-8")
            stripe.WebhookSignature.verify_header(
                body, signature, self._secret, tolerance=TOLERANCE_SECONDS
            )
            event = json.loads(body)
            notice_id, kind = event["id"], event["type"]
            subject = event["data"]["object"]
            connected = event.get("account")
        except (
            stripe.SignatureVerificationError,
            UnicodeDecodeError,
            ValueError,
            KeyError,
            TypeError,
        ):
            raise PaymentNoticeRefused() from None
        customer = subject.get("customer")
        if kind == "setup_intent.succeeded" and isinstance(customer, str):
            return SetupSucceeded(
                notice_id=notice_id, customer_id=customer, setup_id=subject["id"]
            )
        if kind == "payment_method.automatically_updated" and isinstance(
            customer, str
        ):
            # The method's id and nothing of the card: the card is read from
            # Stripe as it stands, because two updates arrive in either order.
            return CardUpdatedByBank(
                notice_id=notice_id, customer_id=customer, method_id=subject["id"]
            )
        if kind in SEAT_PAYMENT_KINDS and isinstance(connected, str):
            # A direct charge lives on the club's account, so its notice comes
            # through the Connected accounts endpoint naming that account.
            return SeatPaymentChanged(
                notice_id=notice_id, account_id=connected, payment_id=subject["id"]
            )
        payment = subject.get("payment_intent")
        if (
            kind == FEE_READY_KIND
            and isinstance(connected, str)
            and isinstance(payment, str)
        ):
            # The charge names its payment: read as it stands, its fee too.
            return SeatPaymentChanged(
                notice_id=notice_id, account_id=connected, payment_id=payment
            )
        if kind == "account.updated" and isinstance(connected, str):
            # The account's id and nothing of its state: it is read from
            # Stripe as it stands, because two updates arrive in either order.
            return ConnectedAccountChanged(notice_id=notice_id, account_id=connected)
        return Unheeded(notice_id=notice_id, kind=kind)

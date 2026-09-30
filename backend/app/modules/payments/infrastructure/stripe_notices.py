"""Stripe's webhook, verified and read as a notice in Raketa's words.

**Verified before a byte of it is read.** A notice is signed with the platform
endpoint's secret — ``Stripe-Signature: t=…,v1=…``, an HMAC-SHA256 over the
timestamp and the raw body — and checked by stripe-python's own verifier with a
**five-minute tolerance**, which the verifier leaves off unless asked (0 would
accept a notice replayed a year later). Anything unsigned, signed with another
secret, too old or not text is refused whole.

**Whichever provider this process pays through**, the notices come from Stripe:
a laptop on the fake receives none and holds no secret, so every notice is
answered ``payment_notices_not_configured``.

**The platform endpoint only.** Direct charges and club accounts notify on a
**Connected accounts** endpoint with a secret of its own (#537, #541); the kinds
read here are the platform's — a setup that succeeded, and a card its bank
updated. Every other kind is ``Unheeded`` and acknowledged.
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
    Notice,
    SetupSucceeded,
    Unheeded,
)

#: How old a signed notice may be, in seconds: the libraries' own default,
#: which their verifier applies only when it is passed.
TOLERANCE_SECONDS = 300


@final
class StripeNotices:
    """``PaymentNotices`` for Stripe's platform endpoint."""

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
        return Unheeded(notice_id=notice_id, kind=kind)

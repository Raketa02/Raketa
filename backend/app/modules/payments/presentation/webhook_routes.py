"""The payment provider's two webhooks: the platform's, ``POST
/api/v1/webhooks/stripe``, and the **Connected accounts** endpoint's, ``POST
/api/v1/webhooks/stripe-connect`` (#537).

**Two endpoints because Stripe sends two kinds of notice to two places**: what
happens on the platform — a setup, a card — and what happens on a club's own
account — its onboarding, and later the payments made on it — each signed with
its endpoint's own secret. Read by one reader each, and acted on by one
receiver, so a notice is read once through the one inbox whichever endpoint it
came through.

**No client calls it, so no client document carries it** (``docs/adr/0190``):
the caller is Stripe, whose event shape is Stripe's contract and not this
backend's, so it is mounted beside the surfaces (``app/api/v1/webhooks.py``) and
kept out of every schema. It takes no session — a notice is its own credential,
signed with the endpoint's secret.

**Verified, then read once** (``domain/notices.py``). An unverifiable notice is a
``400`` and nothing is read; a notice read before, or about something nobody
here holds, is acknowledged with a ``204`` and changes nothing — the provider
retries anything but a success for three days, and a retry of a notice Raketa
has no stake in is noise. Only a failure to act on one it does is an error, so
that the provider sends it again.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from app.modules.payments.presentation.dependencies import (
    ConnectedAccountNoticesDep,
    PaymentNoticesDep,
    ReceivePaymentNoticeDep,
)

router = APIRouter(prefix="/webhooks", include_in_schema=False)


@router.post("/stripe", status_code=status.HTTP_204_NO_CONTENT)
async def receive_stripe_notice(
    request: Request,
    notices: PaymentNoticesDep,
    receive: ReceivePaymentNoticeDep,
) -> Response:
    # The raw body, byte for byte: the signature is over exactly what was sent,
    # and a body parsed and re-serialised is a body that no longer verifies.
    notice = notices.read(
        await request.body(), signature=request.headers.get("Stripe-Signature")
    )
    await receive.execute(notice)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/stripe-connect", status_code=status.HTTP_204_NO_CONTENT)
async def receive_stripe_connect_notice(
    request: Request,
    notices: ConnectedAccountNoticesDep,
    receive: ReceivePaymentNoticeDep,
) -> Response:
    notice = notices.read(
        await request.body(), signature=request.headers.get("Stripe-Signature")
    )
    await receive.execute(notice)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

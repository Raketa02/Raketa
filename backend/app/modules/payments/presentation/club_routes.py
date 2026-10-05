"""The club's payments account, on the club surface (#537, the mechanics §16.2,
the screens B2) — and its payouts (#548, the mechanics §16.11, the screens B7).

Mounted under ``/api/v1/club``, which only the club website consumes
(``docs/adr/0187`` §5), and it takes a **club-audience** token: a desk connects
its own club. **Signed by this context** because it holds the provider; the
account itself is the club's, recorded on its Club courts stream and read back
by ``GET /api/v1/club/setup``.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from app.core.exception_handlers import ErrorResponse
from app.modules.clubs.application.commands import ConnectPaymentsCommand
from app.modules.clubs.presentation.dependencies import CurrentClubAccountDep
from app.modules.payments.domain.provider import PayoutStatus
from app.modules.payments.presentation.dependencies import (
    ConnectPaymentsDep,
    ReadClubPayoutsDep,
)

router = APIRouter(prefix="/payments", tags=["club"])
#: The Money page's payouts (#548).
payouts_router = APIRouter(prefix="/payouts", tags=["club"])


class OnboardingLinkResponse(BaseModel):
    url: str = Field(
        description=(
            "The provider's own hosted pages for the club's account — **single "
            "use and short-lived**, so the desk is sent there at once and a new "
            "one is asked for every time. The provider sends the desk back to "
            "the website's `/overview` when it leaves, and to "
            "`/payments/continue` — which asks for a fresh link and follows it "
            "— when this one is spent or stale."
        )
    )


@router.post(
    "/onboarding-link",
    response_model=OnboardingLinkResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`payments_already_connected` — the provider says the account "
                "is ready: the checklist's first step is done, and there is "
                "nothing left to fill in. No link was made."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`payments_unavailable` — the provider could not be reached. "
                "Try again; an account it had already opened is kept, and the "
                "next link continues it."
            ),
        },
    },
    summary="Connect with Stripe — or continue",
    description=(
        "The setup checklist's first step (*Connect payments*). The first time, "
        "opens the club's account at the payment provider — **once, for ever** "
        "— and answers a link to the provider's hosted pages, where the club "
        "gives its company details, its representative and a Polish IBAN. "
        "Every later call answers a fresh link for the same account: *Continue "
        "with Stripe* while the provider needs more details. **Every call also "
        "reads the account as it stands**, so the checklist follows what the "
        "provider says even before its notice arrives."
    ),
)
async def onboarding_link(
    account: CurrentClubAccountDep, connect: ConnectPaymentsDep
) -> OnboardingLinkResponse:
    url = await connect.execute(
        ConnectPaymentsCommand(club_id=account.club_id, email=account.email.value)
    )
    return OnboardingLinkResponse(url=url)


class PayoutSchema(BaseModel):
    payout_id: str = Field(description="The provider's own id for it.")
    amount_grosze: int
    arrives_at: datetime = Field(
        description="When it reaches — or reached — your bank, as the provider says."
    )
    status: PayoutStatus = Field(
        description=(
            "`PENDING` and `IN_TRANSIT` — on its way. `PAID` — in your bank. "
            "`FAILED` — your bank refused it: the provider asks you for your "
            "details. `CANCELLED` — it never left."
        )
    )


class PayoutsResponse(BaseModel):
    payouts: list[PayoutSchema] = Field(
        description=(
            "Your account's payouts, newest first. **You are paid after the "
            "game is played**: at the close of each day, what that day's games "
            "over left you goes to your bank in one payout."
        )
    )


@payouts_router.get(
    "",
    response_model=PayoutsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`payments_unavailable` — the provider could not be reached. Try again."
            ),
        },
    },
    summary="Your payouts",
    description=(
        "The payouts to your bank, as the payment provider says they stand — "
        "the Money page's list. Empty until payments are connected and a "
        "first game is played."
    ),
)
async def payouts(
    account: CurrentClubAccountDep,
    read: ReadClubPayoutsDep,
    limit: int = Query(default=30, ge=1, le=100),
) -> PayoutsResponse:
    found = await read.execute(account.club_id, limit=limit)
    return PayoutsResponse(
        payouts=[
            PayoutSchema(
                payout_id=payout.payout_id,
                amount_grosze=payout.amount_grosze,
                arrives_at=payout.arrives_at,
                status=payout.status,
            )
            for payout in found
        ]
    )

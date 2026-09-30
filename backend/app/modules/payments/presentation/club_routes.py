"""The club's payments account, on the club surface (#537, the mechanics §16.2,
the screens B2).

Mounted under ``/api/v1/club``, which only the club website consumes
(``docs/adr/0187`` §5), and it takes a **club-audience** token: a desk connects
its own club. **Signed by this context** because it holds the provider; the
account itself is the club's, recorded on its Club courts stream and read back
by ``GET /api/v1/club/setup``.
"""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core.exception_handlers import ErrorResponse
from app.modules.clubs.application.commands import ConnectPaymentsCommand
from app.modules.clubs.presentation.dependencies import CurrentClubAccountDep
from app.modules.payments.presentation.dependencies import ConnectPaymentsDep

router = APIRouter(prefix="/payments", tags=["club"])


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

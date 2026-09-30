"""The player surface's payment routes: You › Payments (#536; the screens A7.3).

Mounted on the player surface (``app/api/v1/player.py``) under
``/players/me/payment-methods``: the four steps of the setup in their order —
**start** it, **accept the terms**, **confirm** the save — and the saved method
read and removed. Every route takes a player's token and acts on their own
method only; there is no route that names another player.

**The order is the contract** (the mechanics §12.5). Starting answers what the
phone opens the provider's card fields with, and **no secret**; accepting the
terms answers the setup's secret, the only way a phone can save anything; and
confirming reads what the setup saved. A client that skips a step meets a
refusal naming it.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, Response, status

from app.core.exception_handlers import ErrorResponse
from app.modules.payments.application.commands import AcceptPaymentTermsCommand
from app.modules.payments.presentation.dependencies import (
    AcceptPaymentTermsDep,
    ConfirmPaymentSetupDep,
    ReadPaymentMethodDep,
    RemovePaymentMethodDep,
    StartPaymentSetupDep,
)
from app.modules.payments.presentation.schemas import (
    PaymentMethodResponse,
    PaymentSetupResponse,
    PaymentTermsRequest,
    PaymentTermsResponse,
)
from app.modules.users.presentation.dependencies import (
    ADULT_ATTESTATION_MISSING,
    AttestedPlayerDep,
    CurrentUserDep,
)

router = APIRouter(prefix="/players/me/payment-methods", tags=["payments"])

#: Every route that asks the provider can find it unreachable, and records
#: nothing when it does.
_PROVIDER_DOWN: dict[int | str, dict[str, Any]] = {
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": (
            "`payments_unavailable` — the payment provider could not be reached. "
            "Nothing was recorded; retry."
        ),
    },
}

_NOT_STARTED = (
    "`payment_setup_not_started` — no setup is open: never started, or "
    "cancelled at the provider. Start one."
)


@router.post(
    "/setup",
    response_model=PaymentSetupResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        **ADULT_ATTESTATION_MISSING,
        **_PROVIDER_DOWN,
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse,
            "description": (
                "`payment_setups_exhausted` — five setups were started in the "
                "last day, the card-testing guard. Nothing was asked of the "
                "provider."
            ),
        },
    },
    summary="Start saving a payment method",
    description=(
        "Opens a setup at the provider for a card saved for **off-session** use "
        "— charged by the club when a game fills, without the player present. "
        "The first opens the player's customer at the provider. A method already "
        "saved **keeps working** until a setup saves another (*Change*); a setup "
        "left open is replaced by the next one. Answers what the phone opens the "
        "provider's card fields with — **never the setup's secret**, which is "
        "the answer to accepting the terms."
    ),
)
async def start_payment_setup(
    user: AttestedPlayerDep, start: StartPaymentSetupDep
) -> PaymentSetupResponse:
    return PaymentSetupResponse.from_opened(await start.execute(user.id))


@router.post(
    "/terms",
    response_model=PaymentTermsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_PROVIDER_DOWN,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`payment_terms_outdated` — the words shown are not the terms in "
                "force, named by `details.terms_version`. "
                + _NOT_STARTED
                + " Nothing was recorded."
            ),
        },
    },
    summary="Accept the payment terms",
    description=(
        "Records the acceptance — the version, the moment and the address it "
        "came from — **before anything is saved**, and answers the open setup's "
        "secret. With no setup open, accepts them again for the saved method "
        "after its bank moved it to another brand, and answers no secret. "
        "Accepting what nothing asks for records nothing."
    ),
)
async def accept_payment_terms(
    payload: PaymentTermsRequest,
    request: Request,
    user: CurrentUserDep,
    accept: AcceptPaymentTermsDep,
) -> PaymentTermsResponse:
    secret = await accept.execute(
        AcceptPaymentTermsCommand(
            player_id=user.id,
            terms_version=payload.terms_version,
            # The route's, never the body's: the address is evidence.
            ip=request.client.host if request.client else None,
        )
    )
    return PaymentTermsResponse(client_secret=secret)


@router.post(
    "/confirmation",
    response_model=PaymentMethodResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_PROVIDER_DOWN,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`payment_terms_not_accepted` — the terms come first; nothing "
                "was saved. `payment_setup_not_finished` — the phone has not "
                "confirmed, or the bank's check is not done "
                "(`details.status`: `AWAITING_THE_PHONE`, `AUTHENTICATING`, "
                "`PROCESSING`). `payment_method_declined` — the bank refused "
                "the card; the same setup can try another. " + _NOT_STARTED
            ),
        },
    },
    summary="Confirm the save",
    description=(
        "Reads what the open setup saved at the provider and records it as the "
        "player's method — replacing, and releasing, the one they had. "
        "Confirming again answers the same method."
    ),
)
async def confirm_payment_setup(
    user: CurrentUserDep, confirm: ConfirmPaymentSetupDep
) -> PaymentMethodResponse:
    return PaymentMethodResponse.from_aggregate(await confirm.execute(user.id))


@router.get(
    "/current",
    response_model=PaymentMethodResponse,
    status_code=status.HTTP_200_OK,
    summary="The saved payment method",
    description=(
        "The card or wallet the club charges when a game fills, or `null` — "
        "*Not set up* — and whether the terms wait to be accepted again."
    ),
)
async def read_payment_method(
    user: CurrentUserDep, read: ReadPaymentMethodDep
) -> PaymentMethodResponse:
    return PaymentMethodResponse.from_aggregate(await read.execute(user.id))


@router.delete(
    "/current",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "`payment_method_not_found` — nothing is saved.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`payment_method_in_use` — a live yes or a booked game ahead "
                "still needs it; `details.live_yeses` and "
                "`details.upcoming_games` count them. Nothing was removed."
            ),
        },
    },
    summary="Remove the saved payment method",
    description=(
        "Forgets the method and releases it at the provider, where it can never "
        "be charged again. Refused while anything could still be charged to it."
    ),
)
async def remove_payment_method(
    user: CurrentUserDep, remove: RemovePaymentMethodDep
) -> Response:
    await remove.execute(user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

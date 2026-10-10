"""The player surface's seat charge routes (#541; the mechanics §12.2; the
screens A2.4, A7.3): **a refused payment, read to be confirmed**, and You ›
Payments' *RECEIPTS*.

Mounted on the player surface (``app/api/v1/player.py``). Every route takes a
player's token and answers about that player's own charges only. **The secret a
phone confirms a payment with crosses here and is recorded nowhere**: it is
asked of the provider when the read is made. Confirming it — *the yes again* —
is ``POST /seat-charges/{id}/confirmation``, the Proposals context's, since a
yes is.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.payments.presentation.dependencies import (
    ReadReceiptsDep,
    ReadSeatChargeDep,
)
from app.modules.payments.presentation.schemas import (
    ReceiptsResponse,
    SeatChargeResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

seat_charges_router = APIRouter(prefix="/seat-charges", tags=["payments"])
receipts_router = APIRouter(prefix="/players/me", tags=["payments"])


@seat_charges_router.get(
    "/{seat_charge_id}",
    response_model=SeatChargeResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`seat_charge_not_found` — no such charge **for this player**: it "
                "does not exist, or it is somebody else's. One code for both."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`payments_unavailable` — the payment provider could not be "
                "reached for what the phone confirms with. Retry."
            ),
        },
    },
    summary="One of my seat charges",
    description=(
        "A share of a game, as it stands — and, while its payment waits for the "
        "player (*Confirm your payment to keep your seat*), what the phone "
        "confirms it with on the club's account. Nothing is recorded."
    ),
)
async def read_seat_charge(
    seat_charge_id: UUID, user: CurrentUserDep, read: ReadSeatChargeDep
) -> SeatChargeResponse:
    return SeatChargeResponse.from_reading(
        await read.execute(seat_charge_id, player_id=user.id)
    )


@receipts_router.get(
    "/receipts",
    response_model=ReceiptsResponse,
    summary="My receipts",
    description=(
        "You › Payments' *RECEIPTS*: every share the reader paid, every refund "
        "with exactly what was kept on the payment, and every share held for a "
        "booked game and let go untaken (*held · released*, #641) — the latest "
        "first, **the club named as the seller**. A hold released because the "
        "game did not book on it is not here, nor is a card check."
    ),
)
async def read_receipts(
    user: CurrentUserDep, read: ReadReceiptsDep
) -> ReceiptsResponse:
    return ReceiptsResponse.from_receipts(await read.execute(user.id))

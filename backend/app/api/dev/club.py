"""The club row: a request answered, a game moved or cancelled — as the club
whose court it is (``docs/adr/0194`` §2, §3; #591). Its check-in press went
with desk check-in (#651).

**Each route is the club's own route with the acting club in place of the
signed-in desk** — ``POST /dev/clubs/{club_id}/bookings/{id}/acceptance`` beside
the desk's ``POST /api/v1/club/bookings/{id}/acceptance`` — and runs the same
use case, built by the same dependency, with the same arguments and the same
wire. So a press does what the desk's own button would do, **refusals
included**: a booking at another club is ``booking_not_found``, a request
answered already ``request_not_waiting``.

**Only a club the seed signed up**: the acting club's desk signs in on the
reserved ``.example`` TLD, as a seeded player's account does, and any other club
— or an id that is no club's — is refused ``not_a_seed_account`` before the use
case is built. A real club's desk is somebody's, and the console never acts as
anybody's.

**No no-show button here.** The club does not report a no-show: a player on the
court does (the mechanics §15.3) — so it is a person's row's press (#593), not
the club's.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Response, status

from app.api.dev.accounts import NotASeedAccount, is_seed_account
from app.core.exception_handlers import ErrorResponse
from app.modules.clubs.domain.ports import ClubAccountRepository
from app.modules.clubs.presentation.dependencies import ClubAccountRepositoryDep
from app.modules.proposals.presentation.club_routes import (
    AcceptanceResponse,
    CancelRequest,
    CourtToMoveToSchema,
    FreeCourtsResponse,
    MoveRequest,
    RefusalRequest,
)
from app.modules.proposals.presentation.dependencies import (
    AcceptTheRequestDep,
    CancelTheGameDep,
    MoveTheGameDep,
    ReadFreeCourtsDep,
    RefuseTheRequestDep,
)

router = APIRouter(prefix="/clubs/{club_id}", tags=["dev"])


async def is_a_seed_club(accounts: ClubAccountRepository, club_id: UUID) -> bool:
    """Whether the seed signed this club up — its desk signs in on the reserved
    TLD. ``False`` for an id that is no club's, which is not one either."""

    account = await accounts.get_by_club(club_id)
    return account is not None and is_seed_account(account.email.value)


async def acting_club(
    club_id: Annotated[
        UUID,
        Path(
            description=(
                "The acting club: one the seed signed up, whose desk signs in on "
                "the reserved TLD. Any other id is refused `not_a_seed_account`."
            )
        ),
    ],
    accounts: ClubAccountRepositoryDep,
) -> UUID:
    """The acting club's id, once its desk's account is one the seed created —
    the club-surface twin of ``acting_account``."""

    if not await is_a_seed_club(accounts, club_id):
        raise NotASeedAccount()
    return club_id


ActingClubDep = Annotated[UUID, Depends(acting_club)]

_REFUSED: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`not_a_seed_account` — the acting club is not one the seed signed "
            "up. Nothing was asked of the use case."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "As the club's own route answers it.",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "As the club's own route answers it.",
    },
}


@router.post(
    "/bookings/{booking_id}/acceptance",
    response_model=AcceptanceResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_REFUSED,
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "As the club's own route answers it.",
        },
    },
    summary="Accept a request, as the club",
    description=(
        "`POST /api/v1/club/bookings/{id}/acceptance` as the acting club: "
        "everybody charged together or not at all, over the provider this "
        "process moves money through, and the reserved court given."
    ),
)
async def accept(
    booking_id: UUID, club: ActingClubDep, accept: AcceptTheRequestDep
) -> AcceptanceResponse:
    return AcceptanceResponse.from_acceptance(
        await accept.execute(club_id=club, booking_id=booking_id)
    )


@router.post(
    "/bookings/{booking_id}/refusal",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=_REFUSED,
    summary="Refuse a request, as the club",
    description=(
        "`POST /api/v1/club/bookings/{id}/refusal` as the acting club: nobody "
        "paid, the hour is the club's again, the players are dealt a new card."
    ),
)
async def refuse(
    booking_id: UUID,
    club: ActingClubDep,
    refuse: RefuseTheRequestDep,
    payload: RefusalRequest | None = None,
) -> Response:
    await refuse.execute(
        club_id=club,
        booking_id=booking_id,
        reason=None if payload is None else payload.reason,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/bookings/{booking_id}/free-courts",
    response_model=FreeCourtsResponse,
    status_code=status.HTTP_200_OK,
    responses=_REFUSED,
    summary="Where a game can be moved, as the club",
    description="`GET /api/v1/club/bookings/{id}/free-courts` as the acting club.",
)
async def free_courts(
    booking_id: UUID, club: ActingClubDep, read: ReadFreeCourtsDep
) -> FreeCourtsResponse:
    courts = await read.execute(club_id=club, booking_id=booking_id)
    return FreeCourtsResponse(courts=[CourtToMoveToSchema.of(one) for one in courts])


@router.post(
    "/bookings/{booking_id}/move",
    response_model=CourtToMoveToSchema,
    status_code=status.HTTP_200_OK,
    responses=_REFUSED,
    summary="Move a game to another court, as the club",
    description="`POST /api/v1/club/bookings/{id}/move` as the acting club.",
)
async def move(
    booking_id: UUID,
    payload: MoveRequest,
    club: ActingClubDep,
    move: MoveTheGameDep,
) -> CourtToMoveToSchema:
    return CourtToMoveToSchema.of(
        await move.execute(
            club_id=club, booking_id=booking_id, court_id=payload.court_id
        )
    )


@router.post(
    "/bookings/{booking_id}/cancellation",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=_REFUSED,
    summary="Cancel a game, as the club",
    description=(
        "`POST /api/v1/club/bookings/{id}/cancellation` as the acting club: "
        "every hold let go before the cut-off, everybody refunded in full after "
        "it, on nobody's record, a new card owed."
    ),
)
async def cancel(
    booking_id: UUID,
    payload: CancelRequest,
    club: ActingClubDep,
    cancel: CancelTheGameDep,
) -> Response:
    await cancel.execute(club_id=club, booking_id=booking_id, because=payload.reason)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

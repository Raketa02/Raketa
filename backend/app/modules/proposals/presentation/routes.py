"""The player surface's proposal routes: the three answers to a card, the
reader's live yeses (#538; the mechanics §6, §10.2; the screens A2.4, A7.3), a
group's deck and the reader's Games & money (#539; the mechanics §6.6, §8,
§17.1; the screens A2, A7.1).

Mounted on the player surface (``app/api/v1/player.py``). Every route takes a
player's token and answers for that player only.

**A yes and a no are silent**: nothing here tells anybody anything, and a
repeated tap records nothing. **Nothing is charged by a yes — except the last**
(#541): the yes that leaves no seat open books the game, every seat charged
together or nobody, and its answer says which. Confirming a refused payment is
that player's yes again, ``POST /seat-charges/{id}/confirmation``.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Response, status

from app.core.exception_handlers import ErrorResponse
from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.proposals.application.commands import (
    AnswerProposalCommand,
    ConfirmPaymentCommand,
    ReadGroupDeckCommand,
    SetGamesAndMoneyCommand,
)
from app.modules.proposals.presentation.dependencies import (
    ConfirmPaymentDep,
    ReadPaymentsToConfirmDep,
    ReadGamesAndMoneyDep,
    ReadGroupDeckDep,
    ReadLiveYesesDep,
    SayNoDep,
    SayYesDep,
    SetGamesAndMoneyDep,
    WithdrawYesDep,
)
from app.modules.proposals.presentation.schemas import (
    GamesAndMoneyRequest,
    GamesAndMoneyResponse,
    GroupDeckResponse,
    LiveYesesResponse,
    PaymentsToConfirmResponse,
    YesAnswerResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/proposals", tags=["proposals"])
players_router = APIRouter(prefix="/players/me", tags=["proposals"])
pools_router = APIRouter(prefix="/pools", tags=["proposals"])
seat_charges_router = APIRouter(prefix="/seat-charges", tags=["proposals"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`proposal_not_found` — no such game **for this player**: it does not "
            "exist, it was never dealt to them, or (for a yes) they are no longer "
            "in its group. One code for all three."
        ),
    },
}

_OVER = (
    "`proposal_is_over` — the game is no longer filling, named by "
    "`details.standing` (`EXPIRED` once its book-by passed, `WITHDRAWN` once its "
    "poster took the post back with nobody else In, `COURT_HOUR_LOST` once the "
    "last court at its club and hour went). The card leaves."
)


_YES_REFUSED = (
    " `payment_to_confirm` — this player's seat reopened because their payment "
    "could not be held: confirming it (`details.seat_charge_id`) is their yes "
    "again. `proposal_already_answered` — this player said no: the card does not come "
    "back. `proposal_is_full` — every seat is In. `payment_method_required` — no "
    "saved payment method: save one, then say yes. `live_yeses_exhausted` — "
    "`details.cap` live yeses in `details.sport` already. `no_longer_fits` — "
    "somebody In now is somebody this player does not fit; the card has gone, "
    "and who is not said. Nothing was recorded — except on `proposal_is_over` "
    "with `COURT_HOUR_LOST` from the yes that filled it: no court was left at the "
    "club and hour, the card is over, and nobody paid."
)

_FILL_UNAVAILABLE = (
    "`block_state_unavailable` — whether this player fits the people In could "
    "not be read. `payments_unavailable` — the yes filled the game and the "
    "payment provider could not be reached to hold the shares. Nothing was "
    "recorded; retry."
)


@router.post(
    "/{proposal_id}/yes",
    response_model=YesAnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": _OVER + _YES_REFUSED,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": _FILL_UNAVAILABLE,
        },
    },
    summary="Say yes to a game",
    description=(
        "*I'm in — if everybody is, book it and charge my share.* **Silent, free, "
        "and it holds nothing** — no money moves, no court is held, nobody is told "
        "(the others see the player In on the card) — **unless it is the last**. "
        "Yeses are the game's, not a version's: a yes on any version counts toward "
        "the one game. A yes already said records nothing and answers the same.\n\n"
        "**The last yes books the game** (the client gives its ten seconds of "
        "*Undo* before sending it): every seat's share is held on the club's "
        "account and then all are taken, or none is — `booked` names the booking "
        "and its Game, and everybody is emailed *It's a game! · you paid*. When a "
        "share could not be held, **nobody paid**: that player's seat is open "
        "again (`open_seats`), and when it is this player's own, `your_payment` "
        "names the refused payment to confirm. At an On request club a full game "
        "waits for the club (#543): `open_seats` is nought and nothing is booked."
    ),
)
async def say_yes(
    proposal_id: UUID, user: CurrentUserDep, say: SayYesDep
) -> YesAnswerResponse:
    answer = await say.execute(
        AnswerProposalCommand(proposal_id=proposal_id, player_id=user.id)
    )
    return YesAnswerResponse.from_answer(answer)


@router.post(
    "/{proposal_id}/no",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                _OVER + " `proposal_already_answered` — this player is In: they "
                "leave by withdrawing their yes, never by a no."
            ),
        },
    },
    summary="Say no to a game",
    description=(
        "A swipe left: **silent, final, and never on the player's record.** The "
        "card does not come back. A second no records nothing."
    ),
)
async def say_no(proposal_id: UUID, user: CurrentUserDep, say: SayNoDep) -> Response:
    await say.execute(AnswerProposalCommand(proposal_id=proposal_id, player_id=user.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{proposal_id}/yes",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {"model": ErrorResponse, "description": _OVER},
    },
    summary="Withdraw a yes",
    description=(
        "*Withdraw* on a You're In row: free and silent until the game fills. The "
        "seat is open again, and the player may say yes again while it fills. "
        "Withdrawing a yes never said records nothing. **A poster withdrawing "
        "with nobody else In "
        "takes the post with them**; with others In, the game carries on without "
        "them."
    ),
)
async def withdraw_yes(
    proposal_id: UUID, user: CurrentUserDep, withdraw: WithdrawYesDep
) -> Response:
    await withdraw.execute(
        AnswerProposalCommand(proposal_id=proposal_id, player_id=user.id)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@players_router.get(
    "/live-yeses",
    response_model=LiveYesesResponse,
    summary="My live yeses",
    description=(
        "Every yes of the reader's on a game that has not filled, **across "
        "groups**, soonest game first, each with the share it would charge — You "
        "› Payments' *LIVE YESES*. A game past its book-by is not here, whether "
        "or not its expiry has been recorded."
    ),
)
async def read_live_yeses(
    user: CurrentUserDep, read: ReadLiveYesesDep
) -> LiveYesesResponse:
    return LiveYesesResponse.from_live(await read.execute(user.id))


@players_router.get(
    "/payments-to-confirm",
    response_model=PaymentsToConfirmResponse,
    summary="My payments to confirm",
    description=(
        "*Confirm your payment to keep your seat*: every game still filling whose "
        "last yes could not hold the reader's share — the bank wanted them, or "
        "declined — so their seat is open again until they confirm the payment "
        "(`POST /seat-charges/{id}/confirmation`) or somebody takes it. Across "
        "groups, soonest game first. A game that filled without them, or is no "
        "longer filling, is not here."
    ),
)
async def read_payments_to_confirm(
    user: CurrentUserDep, read: ReadPaymentsToConfirmDep
) -> PaymentsToConfirmResponse:
    return PaymentsToConfirmResponse.from_owed(await read.execute(user.id))


@pools_router.get(
    "/{pool_id}/deck",
    response_model=GroupDeckResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`pool_not_found` — no such group, or the reader is not in it. One "
                "code for both."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`block_state_unavailable` — whether the reader fits the people on "
                "the cards could not be read. Retry."
            ),
        },
    },
    summary="A group's deck",
    description=(
        "The **Games** tab for one sport and segment: the cards dealt to the "
        "reader in this group — the pool is filed under the group's id — each "
        "as **the reader's own version**, with its sides, forecast and overlap "
        "computed now. **Never dealt**: a card the reader said no to, one they are "
        "In on (it is in *You're In*), a kind their Play intent does not want, a "
        "share above their *most I'll pay*, a week at their games per week, an "
        "hour they already have a game at, a club no longer selling, and a card "
        "with somebody In they may not share a court with. Around the deck: a "
        "count per segment, the Games badge and the capped weeks. Nothing is "
        "recorded."
    ),
)
async def read_group_deck(
    pool_id: UUID,
    sport: Sport,
    kind: SearchMode,
    user: CurrentUserDep,
    read: ReadGroupDeckDep,
) -> GroupDeckResponse:
    deck = await read.execute(
        ReadGroupDeckCommand(player_id=user.id, pool_id=pool_id, sport=sport, kind=kind)
    )
    return GroupDeckResponse.from_deck(deck, reader=user.id)


@players_router.get(
    "/games-and-money",
    response_model=GamesAndMoneyResponse,
    summary="My Games & money",
    description=(
        "You › Account › *Games & money*: games per week (two until changed) and "
        "most I'll pay per game (off until changed), with the ranges the form "
        "offers. Applies across sports and groups."
    ),
)
async def read_games_and_money(
    user: CurrentUserDep, read: ReadGamesAndMoneyDep
) -> GamesAndMoneyResponse:
    return GamesAndMoneyResponse.from_settings(await read.execute(user.id))


@players_router.put(
    "/games-and-money",
    response_model=GamesAndMoneyResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`games_per_week_out_of_range` — outside `details.least`–"
                "`details.most`. `most_ill_pay_not_offered` — not `null` and not "
                "one of `details.choices`. Nothing was saved."
            ),
        },
    },
    summary="Save my Games & money",
    description=(
        "Both values, as the screen saves them on every tap. The same answer "
        "records nothing. Answers what is now saved."
    ),
)
async def set_games_and_money(
    body: GamesAndMoneyRequest, user: CurrentUserDep, save: SetGamesAndMoneyDep
) -> GamesAndMoneyResponse:
    saved = await save.execute(
        SetGamesAndMoneyCommand(
            player_id=user.id,
            games_per_week=body.games_per_week,
            most_ill_pay_grosze=body.most_ill_pay_grosze,
        )
    )
    return GamesAndMoneyResponse.from_settings(saved)


@seat_charges_router.post(
    "/{seat_charge_id}/confirmation",
    response_model=YesAnswerResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`seat_charge_not_found` — no such charge **for this player**. "
                "`proposal_not_found` — they are no longer in the game's group."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`payment_not_confirmed` — the provider still waits for the "
                "player (`details.status`), or the charge was never a payment to "
                "confirm (`NOTHING_TO_CONFIRM`): confirm it in the app, or accept "
                "the terms or save a method and say yes. "
                + _OVER
                + " `proposal_is_full` — somebody else took the seat. On both, "
                "the payment the player confirmed is let go and nobody pays it. "
                "`live_yeses_exhausted` and `no_longer_fits` as a yes meets them."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "`payments_unavailable` — " + _FILL_UNAVAILABLE,
        },
    },
    summary="I confirmed my payment — my yes again",
    description=(
        "*Confirm your payment to keep your seat.* The player confirmed, in the "
        "app, the payment that could not be held when the game filled. It is "
        "**asked of the provider**, never taken on the phone's word; held now, it "
        "is the player's yes again — and if theirs was the seat still open, the "
        "game books on it and everybody else is charged then. Answers as a yes "
        "does. Somebody else took the seat first: the payment is let go."
    ),
)
async def confirm_payment(
    seat_charge_id: UUID, user: CurrentUserDep, confirm: ConfirmPaymentDep
) -> YesAnswerResponse:
    answer = await confirm.execute(
        ConfirmPaymentCommand(seat_charge_id=seat_charge_id, player_id=user.id)
    )
    return YesAnswerResponse.from_answer(answer)

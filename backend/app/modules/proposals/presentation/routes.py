"""The player surface's proposal routes: the three answers to a card, the
reader's live yeses (#538; the mechanics §6, §10.2; the screens A2.4, A7.3), a
group's deck and the reader's Games & money (#539; the mechanics §6.6, §8,
§17.1; the screens A2, A7.1), Home and a game's two details — still filling,
or booked (#542; the mechanics §14; the screens A4, A8) — leaving a booked
game (#544; the mechanics §12.3, §13), rescues: a group's *Fill in*, taking
an open seat and saying no to one (#545; the mechanics §10.1; the screens A3,
A4.3), and posting a game: the grid, a cell's sheet and the post (#546; the
mechanics §9; the screens A5).

Mounted on the player surface (``app/api/v1/player.py``). Every route takes a
player's token and answers for that player only.

**A yes and a no are silent**: nothing here tells anybody anything, and a
repeated tap records nothing. **Nothing is charged by a yes — except the last**
(#541): the yes that leaves no seat open books the game, every seat charged
together or nobody, and its answer says which. Confirming a refused payment is
that player's yes again, ``POST /seat-charges/{id}/confirmation``.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.core.exception_handlers import ErrorResponse
from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, instant
from app.modules.proposals.application.commands import (
    FriendsGameCommand,
    SendAFriendsGameCommand,
    AnswerProposalCommand,
    ConfirmPaymentCommand,
    FriendsLineUpCommand,
    DealThePoolNowCommand,
    LeaveTheGameCommand,
    PostAGameCommand,
    PostingCommand,
    ReadDeckCountsCommand,
    ReadFillInCommand,
    ReadGroupDeckCommand,
    ReadPostingGridCommand,
    ReadFriendsCardCommand,
    ReadPostingSlotCommand,
    RescueCommand,
    SetGamesAndMoneyCommand,
)
from app.modules.proposals.domain.overlap import DayRange
from app.modules.proposals.domain.post import Who
from app.modules.proposals.presentation.dependencies import (
    AcceptAFriendsGameDep,
    DeclineAFriendsGameDep,
    CallOffAFriendsGameDep,
    SendAFriendsGameDep,
    ConfirmPaymentDep,
    DealThePoolNowDep,
    SayNoToARescueDep,
    JoinARescueDep,
    LeaveTheGameDep,
    PostAGameDep,
    ReadBookingDetailsDep,
    ReadDeckCountsDep,
    ReadFillInDep,
    ReadFriendsCardDep,
    ReadFriendsCourtsDep,
    ReadHomeDep,
    ReadPaymentsToConfirmDep,
    ReadPostingGridDep,
    ReadPostingSlotDep,
    ReadGamesAndMoneyDep,
    ReadGroupDeckDep,
    ReadLiveYesesDep,
    ReadProposalDetailsDep,
    SayNoDep,
    SayYesDep,
    SetGamesAndMoneyDep,
    WithdrawYesDep,
)
from app.modules.proposals.presentation.schemas import (
    FriendsGameAnswerResponse,
    FriendsGameSentResponse,
    SendFriendsGameRequest,
    BookingDetailsResponse,
    DeckCountsResponse,
    DepartureResponse,
    FillInResponse,
    FriendsCardResponse,
    FriendsCourtsResponse,
    GamesAndMoneyRequest,
    GamesAndMoneyResponse,
    GroupDeckResponse,
    HomeResponse,
    LiveYesesResponse,
    PaymentsToConfirmResponse,
    PostedResponse,
    PostingGridResponse,
    PostingSlotResponse,
    PostRequest,
    ProposalDetailsResponse,
    YesAnswerResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/proposals", tags=["proposals"])
players_router = APIRouter(prefix="/players/me", tags=["proposals"])
pools_router = APIRouter(prefix="/pools", tags=["proposals"])
seat_charges_router = APIRouter(prefix="/seat-charges", tags=["proposals"])
home_router = APIRouter(prefix="/home", tags=["proposals"])
bookings_router = APIRouter(prefix="/bookings", tags=["proposals"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`proposal_not_found` — no such game **for this player**: it does not "
            "exist, it was never dealt to them (a yes on a post is the exception: "
            "a member may join one they were never dealt, #546), or (for a yes) "
            "they are no longer in its group. One code for all three."
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
    "saved payment method: save one, then say yes. `no_longer_fits` — "
    "somebody In now is somebody this player does not fit, a post is not "
    "for them (#546), or their Play intent no longer wants the game's kind "
    "(Q127); the card has gone, and who or why is not said. "
    "`post_not_open_to_you` — joining a post they were never dealt, they could "
    "not be dealt it now (#546). Nothing was recorded — except on "
    "`proposal_is_over` "
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
        "**A member may join a post they were never dealt** (#546) — *I'm in* on a "
        "sheet's *Already happening here*: a yes like any other, held to who the "
        "post is for (`no_longer_fits` otherwise) and to what dealing it would ask "
        "of them now — free for its hour, no game then, within their Games & "
        "money (`post_not_open_to_you`, which is not said).\n\n"
        "**The last yes books the game** (the client gives its ten seconds of "
        "*Undo* before sending it): every seat's share is held on the club's "
        "account, all or none — kept until the club's cut-off, which takes them, "
        "or taken at once after it (#637) — `booked` names the booking and its "
        "Game, and everybody is emailed *It's a game! · 30 zł held* (*you paid* "
        "after the cut-off). When a "
        "share could not be held, **nobody paid**: that player's seat is open "
        "again (`open_seats`), and when it is this player's own, `your_payment` "
        "names the refused payment to confirm. **No club confirms the game**: "
        "the last yes books it at every club (#669)."
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
        "them.\n\n"
        "**While a full game waits for one payment, this is *Leave the game*** "
        "(#625): nobody has paid; the leaver's hold is let go, the payer's time "
        "runs on, and the game is back in the decks with this seat open — the "
        "others still In, and on their Home as `SEAT_OPEN` with `filling_again` "
        "(Q106); past its book-by it is `CALLED_OFF` · `BOOK_BY_PASSED` for them "
        "instead. On a game already `filling_again`, it takes the game off the "
        "player's own Home."
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


@pools_router.post(
    "/{pool_id}/deal",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`pool_not_found` — no such group, or the caller is not in it. One "
                "code for both, as the deck's."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`block_state_unavailable` — whether the members fit each other "
                "could not be read, so the dealing stopped there; whatever it "
                "had applied stands. Read the deck as it stands — the jobs deal "
                "the rest."
            ),
        },
    },
    summary="Deal my group now",
    description=(
        "Right after an intent answer on the **Games** tab (Q127): Raketa deals "
        "this group's games now — the proposer's own batch for its pool, in every "
        "sport it plays, the one the jobs run — and answers once it has been "
        "applied, so the phone can show *Finding for-fun games for you…* for as "
        "long as it takes and then read the deck. It never makes a card itself: "
        "what it deals is exactly what the jobs would have, a moment later. Safe "
        "beside the jobs and beside itself — a repeat deals nothing new — and "
        "what it records is told as the jobs' is (*Your new game* among it). "
        "No body."
    ),
)
async def deal_the_pool_now(
    pool_id: UUID, user: CurrentUserDep, deal: DealThePoolNowDep
) -> Response:
    await deal.execute(DealThePoolNowCommand(player_id=user.id, pool_id=pool_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@players_router.get(
    "/deck-counts",
    response_model=DeckCountsResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`block_state_unavailable` — whether the reader fits the people on "
                "the cards could not be read. Retry."
            ),
        },
    },
    summary="My cards per kind, across my groups",
    description=(
        "You › *What kind of game*, one sport expanded (Q127): how many cards "
        "each kind deals the reader **now**, summed over every group they are "
        "in — each group's number exactly the count its switch shows, Seat open "
        "cards included — so a change of intent can say what it costs (*Your 7 "
        "competitive cards in your groups go*). A kind the reader's Play intent "
        "does not show is `0`, and a sport they have declared nothing in is `0` "
        "and `0`. Nothing is recorded."
    ),
)
async def read_deck_counts(
    sport: Sport, user: CurrentUserDep, read: ReadDeckCountsDep
) -> DeckCountsResponse:
    return DeckCountsResponse.from_counts(
        await read.execute(ReadDeckCountsCommand(player_id=user.id, sport=sport))
    )


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
                "`proposal_not_found` — they are no longer in the game's group; "
                "`booking_not_found` on a rescue's payment (#545), which is let "
                "go."
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
                "`no_longer_fits` as a yes meets it. "
                "**On a rescue's payment** (#545), as `POST /bookings/{id}/seats` "
                "meets them: `seat_just_taken`, `booking_is_called_off` (with "
                "`details.reason` and `details.club_cancel_reason`), "
                "`game_has_started`, `rescue_not_offered` — and the payment is "
                "let go."
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
        "does. Somebody else took the seat first: the payment is let go.\n\n"
        "**A rescue's payment** (#545) — refused when the player went for an "
        "open seat on a booked game — confirmed is **the join again**: the seat "
        "that opened first is theirs, as `POST /bookings/{id}/seats` takes one, "
        "and the answer is the join's, `money` included. Within their time the "
        "seat was kept for them alone (#640); past it, their time runs out "
        "first and the seat is theirs only if nobody took it meanwhile."
    ),
)
async def confirm_payment(
    seat_charge_id: UUID, user: CurrentUserDep, confirm: ConfirmPaymentDep
) -> YesAnswerResponse:
    answer = await confirm.execute(
        ConfirmPaymentCommand(seat_charge_id=seat_charge_id, player_id=user.id)
    )
    return YesAnswerResponse.from_answer(answer)


@router.get(
    "/{proposal_id}",
    response_model=ProposalDetailsResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`proposal_not_found` — no such game **for this player**: it does "
                "not exist, it was never dealt to them, they are no longer in its "
                "group, or somebody In is somebody they may not share a court with "
                "while they are not In — the deck withholds that card, and this is "
                "the same card. One code for all four."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`block_state_unavailable` — whether the reader fits the people on "
                "it could not be read. Retry."
            ),
        },
    },
    summary="A game still filling",
    description=(
        "The game details of a proposal, for anybody dealt it — a card's **i**, "
        "a You're In row, a payment to confirm: who is In (the **IN** tags), the "
        "sides and their forecast, the club and its distance **with no court "
        "number** (one is given at booking), the share and the book-by, the "
        "overlap grid, and **what the reader may do now** (`actions`). A reader "
        "still deciding sees their own card as the deck deals it; a reader In "
        "sees everybody In. Answered for a game that has ended too, with nothing "
        "to do; a `FILLED` game's booking has the same id. Nothing is recorded."
    ),
)
async def read_proposal_details(
    proposal_id: UUID, user: CurrentUserDep, read: ReadProposalDetailsDep
) -> ProposalDetailsResponse:
    return ProposalDetailsResponse.from_details(
        await read.execute(proposal_id, user.id), reader=user.id
    )


@home_router.get(
    "",
    response_model=HomeResponse,
    summary="Home",
    description=(
        "**The reader's games from the moment they fill**, soonest first, each "
        "with its status and money line, and **how many need them** — Home's "
        "badge. The status is folded at `read_at` from the booking, its Game's "
        "result and the clock: *Booked* until the hour, then the result states "
        "as today's cards name them. **Only what Home draws is sent**: live "
        "games, games that ended less than a day after their hour, and games "
        "that need the reader. A game a Classic play challenge opened is "
        "not here — it is `GET /games`'. Nothing is recorded."
    ),
)
async def read_home(user: CurrentUserDep, read: ReadHomeDep) -> HomeResponse:
    return HomeResponse.from_home(await read.execute(user.id), reader=user.id)


@bookings_router.get(
    "/{booking_id}",
    response_model=BookingDetailsResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`booking_not_found` — no such booked game **for this player**: it "
                "does not exist, or they have no seat on it and its open seat is "
                "not offered to them. One code for all three."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`block_state_unavailable` — for a reader with no seat on it, "
                "whether they fit the people on it could not be read. Retry."
            ),
        },
    },
    summary="A booked game",
    description=(
        "The game details of a booked game, for a player in it: the sides with "
        "each seat's face, Level and *paid* tag, the status, WHERE (the club, the "
        "court and how far it is), the hour, the money line, and whether the "
        "balance forecast is drawn (`GET /games/{game_id}/pairing` draws it). "
        "**The chat is the reader's room whose `booking_id` is this booking's**, "
        "in `GET /conversations`.\n\n"
        "**A rescue seen from outside** (#545): a member its open seat is "
        "offered to reads the same game standing in the seat that opened first "
        "(their tile unpaid — *You?*), with `rescue` — no `leaving`. Nothing is "
        "recorded."
    ),
)
async def read_booking_details(
    booking_id: UUID, user: CurrentUserDep, read: ReadBookingDetailsDep
) -> BookingDetailsResponse:
    return BookingDetailsResponse.from_details(
        await read.execute(booking_id, user.id), reader=user.id
    )


@bookings_router.post(
    "/{booking_id}/departure",
    response_model=DepartureResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`booking_not_found` — no such game **for this player**: it does "
                "not exist, or they have no seat on it — including one they "
                "already left. One code for all three."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`game_has_started` — its hour has begun; there is nothing to "
                "leave. `booking_is_called_off` — the game is off (refused, "
                "unanswered, short at its cut-off, cancelled, or gone back to "
                "filling and past its book-by) and everybody still in is "
                "refunded, or nobody paid. Nothing was recorded."
            ),
        },
    },
    summary="Leave a booked game",
    description=(
        "*Leave the game* (the client shows the sheet first: the booking's "
        "`leaving` says what it costs). **Before the club's cut-off** nothing is "
        "taken: the leaver's hold is let go, nobody is refunded (#637), and the "
        "seat is offered to others — on their record only if the game is then "
        "called off because of it. **After the cut-off** the seat stays paid "
        "and is offered to others until the start; the leaver is refunded, "
        "less the fee, when "
        "somebody takes it, and it is on their record if nobody does. **While "
        "a payment is awaited** nobody has paid: the yes is withdrawn, as "
        "`DELETE /proposals/{id}/yes` does, and the game is filling again — and "
        "so it is on a game already `filling_again` (Q106). "
        "The leaver leaves the game's chat with their seat; everybody else's "
        "Home reads `SEAT_OPEN` (with `filling_again` when nobody had paid). "
        "Refused once the hour has begun."
    ),
)
async def leave_the_game(
    booking_id: UUID, user: CurrentUserDep, leave: LeaveTheGameDep
) -> DepartureResponse:
    left = await leave.execute(
        LeaveTheGameCommand(booking_id=booking_id, player_id=user.id)
    )
    return DepartureResponse(left=left)


@pools_router.get(
    "/{pool_id}/fill-in",
    response_model=FillInResponse,
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
                "a game could not be read. Retry."
            ),
        },
    },
    summary="A group's Fill in",
    description=(
        "**Seats to fill** in one sport, and the tab's badge: the open seats of "
        "the group's **booked** games that lost a player, which the reader fits "
        "— the pair rule against everybody on the game, the kind their Play "
        "intent wants — and is free for — the hour in their week, no game of "
        "theirs then — within their Games & money. **Before the cut-off** a seat "
        "*fills by* it or the game is off; **after it**, it is *offered until the "
        "start*. Games still filling are never here — they are the deck's. "
        "Nothing is recorded."
    ),
)
async def read_fill_in(
    pool_id: UUID, sport: Sport, user: CurrentUserDep, read: ReadFillInDep
) -> FillInResponse:
    fill_in = await read.execute(
        ReadFillInCommand(player_id=user.id, pool_id=pool_id, sport=sport)
    )
    return FillInResponse.from_fill_in(fill_in, reader=user.id)


@bookings_router.post(
    "/{booking_id}/seats",
    response_model=YesAnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`booking_not_found` — no such booked game, or the reader is not in "
                "its group. One code for both."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`seat_just_taken` — **the first join wins**: somebody took the "
                "seat a moment before, or none is open — *Someone just took it* — "
                "or the one open is kept for a refused rescuer while their time "
                "runs (#640). "
                "`booking_is_called_off` — the game is off, and `details.reason` "
                "says why: `SHORT_AT_THE_CUT_OFF`, or `CANCELLED_BY_THE_CLUB` with "
                "the club's own `details.club_cancel_reason` (`WEATHER`, `REPAIR`, "
                "`DOUBLE_BOOKING`, `OTHER`). "
                "`game_has_started` — its hour has begun. `rescue_not_offered` — "
                "the seat is not one this player is offered (fit, free, Games & "
                "money, a seat they left); which is not said. "
                "`payment_to_confirm` — their earlier *I'm in* here waits on their "
                "bank: confirming it (`details.seat_charge_id`) is the join again. "
                "`payment_method_required` — no saved method. Nothing was recorded "
                "and nobody charged."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`block_state_unavailable` — whether the player fits the people on "
                "the game could not be read. `payments_unavailable` — the provider "
                "could not be reached to hold the share. Nothing was recorded; "
                "retry."
            ),
        },
    },
    summary="Take an open seat",
    description=(
        "*I'm in · 27 zł* on a rescue — a Seat open card, a Seats to fill row, "
        "a rescue's details (the client gives its ten seconds of *Undo* "
        "first). **The share is held** on the club's account until the cut-off, "
        "like every seat's — or, far ahead of it, the card checked and the "
        "share held at its Holding time — or taken at once after it (#637, "
        "#639, #640), and `money` says which: `HELD`, `CHECKED` or `TAKEN`. The "
        "player takes **the seat that opened first**, on its side — `booked` "
        "names the booking and its Game, now on their Home, and they are "
        "emailed *It's a game! · 30 zł held* (*you paid* after the cut-off); "
        "they join the game's chat, and are free to leave until the cut-off "
        "like everybody else. **The leaver who left after the cut-off is "
        "refunded, less exactly the fee kept on their payment, the moment this "
        "payment succeeds** — told once the refund is made (*You've been "
        "refunded 38,24 zł · your seat was taken*), which waits for a fee not "
        "yet known (#641); one who left before it had nothing taken. "
        "`open_seats` is what is still open. **When the share could not be "
        "held**, nothing was taken, and **a seat is kept for the player alone** "
        "(#640): `your_payment` names the refused payment, and its "
        "`confirm_by` and `time_to` the window — thirty minutes to fix the card "
        "before the cut-off (`FIX_THE_CARD`), or to pay after it (`PAY`), never "
        "past the start — emailed and told *Fix your card by 14:40 to take the "
        "seat* or *Confirm your payment by 14:40 to take the seat*. Meanwhile "
        "it is offered to nobody else; confirming the payment "
        "(`POST /seat-charges/{id}/confirmation`) is the join again, and a "
        "refusal for terms or a missing method is fixed and joined again here. "
        "Run out, the seat is offered again — still theirs to take while it is "
        "free, but never kept for them again on this game. A player already on "
        "the game is answered the same `booked`, and nothing is recorded."
    ),
)
async def join_a_rescue(
    booking_id: UUID, user: CurrentUserDep, join: JoinARescueDep
) -> YesAnswerResponse:
    answer = await join.execute(RescueCommand(booking_id=booking_id, player_id=user.id))
    return YesAnswerResponse.from_answer(answer)


@bookings_router.post(
    "/{booking_id}/no",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`booking_not_found` — no such open seat **offered to this "
                "player**: it does not exist, they are not in its group, or it is "
                "taken, off or not theirs to be offered."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`block_state_unavailable` — whether the player fits the people on "
                "the game could not be read. Retry."
            ),
        },
    },
    summary="Not this time, on a Seat open card",
    description=(
        "A swipe left on a **Seat open** card: **silent, and never on the "
        "player's record.** The card does not come back to their deck; the seat "
        "stays on their *Seats to fill*, which lists every rescue they fit. A "
        "second no records nothing."
    ),
)
async def say_no_to_a_rescue(
    booking_id: UUID, user: CurrentUserDep, say_no: SayNoToARescueDep
) -> Response:
    await say_no.execute(RescueCommand(booking_id=booking_id, player_id=user.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# Posting a game (#546)
# --------------------------------------------------------------------------- #

_POSTING_BAD = (
    "`level_range_too_wide` — a bound outside the engine's window, "
    "`details.low`–`details.high`: narrow it, never widen it. "
    "`level_range_inverted` — the lower bound is above the upper. "
    "`mixed_pairs_only_in_doubles` — `MIXED_PAIRS` in a sport played one a side."
)
_POSTING_REFUSED = (
    "`not_rated_in_the_sport` — the poster holds no Level in it. "
    "`who_leaves_you_out` — the game's *Who* is everybody's on it, and not the "
    "poster's own (which is not said)."
)
_POSTING_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": _POSTING_BAD},
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`pool_not_found` — no such group, or the reader is not in it. One code "
            "for both."
        ),
    },
    status.HTTP_409_CONFLICT: {"model": ErrorResponse, "description": _POSTING_REFUSED},
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": (
            "`block_state_unavailable` — whether the poster fits the members could "
            "not be read. Retry."
        ),
    },
}

_LevelLow = Annotated[
    float | None,
    Query(description="The narrowed lower Level bound; left out is the engine's."),
]
_LevelHigh = Annotated[
    float | None,
    Query(description="The narrowed upper Level bound; left out is the engine's."),
]


def _posting(
    user_id: UUID,
    pool_id: UUID,
    *,
    sport: Sport,
    kind: SearchMode,
    who: Who,
    level_low: float | None,
    level_high: float | None,
) -> PostingCommand:
    return PostingCommand(
        player_id=user_id,
        pool_id=pool_id,
        sport=sport,
        kind=kind,
        who=who,
        level_low=level_low,
        level_high=level_high,
    )


@pools_router.get(
    "/{pool_id}/posting-grid",
    response_model=PostingGridResponse,
    responses=_POSTING_RESPONSES,
    summary="The posting grid",
    description=(
        "**WHEN** on *Post a game*: one week of 7 days × Morning 07–12 / Afternoon "
        "12–17 / Evening 17–23, for the sport, kind, *Who* and Level range the "
        "controls hold. A cell's number is **how many of the poster's best fits "
        "are free together with them at the best hour in its range that has a "
        "free court** — never people who overlap them at different hours — and "
        "around it whether a court is free, whether a full game's worth are, "
        "whether the poster's week covers it, whether it is earlier today, and "
        "whether a game is already happening there. A best fit is a member the "
        "post would be dealt to then: rated, wanting the kind, free for the whole "
        "hour, no game then, within their Games & money, fitting the poster, and "
        "whom it is for. **Week 1 starts today.** The Level range starts as the "
        "engine's own window for the kind (`engine_level_range`) and may only be "
        "narrowed. Nothing is recorded."
    ),
)
async def read_posting_grid(
    pool_id: UUID,
    sport: Sport,
    kind: SearchMode,
    who: Who,
    user: CurrentUserDep,
    read: ReadPostingGridDep,
    level_low: _LevelLow = None,
    level_high: _LevelHigh = None,
    week: Annotated[int, Query(ge=1, le=2)] = 1,
) -> PostingGridResponse:
    grid = await read.execute(
        ReadPostingGridCommand(
            posting=_posting(
                user.id,
                pool_id,
                sport=sport,
                kind=kind,
                who=who,
                level_low=level_low,
                level_high=level_high,
            ),
            week=week,
        )
    )
    return PostingGridResponse.from_week(grid)


@pools_router.get(
    "/{pool_id}/posting-grid/slot",
    response_model=PostingSlotResponse,
    responses=_POSTING_RESPONSES,
    summary="A posting grid cell's sheet",
    description=(
        "Tapping a cell: the headline (its cell again), **the best fits free "
        "then** — at the cell's best hour, best fit first, each with how even a "
        "game with the poster is forecast — **the free courts** in the range, "
        "home club first, each with its hour, club, distance, share, book-by and "
        "**its own count** of fits free then; and **already happening here**: "
        "rescues the poster is offered, then somebody else's posts still filling "
        "the poster could join. Nothing is recorded."
    ),
)
async def read_posting_slot(
    pool_id: UUID,
    sport: Sport,
    kind: SearchMode,
    who: Who,
    day: date,
    range_: Annotated[
        DayRange, Query(alias="range", description="A third of the day.")
    ],
    user: CurrentUserDep,
    read: ReadPostingSlotDep,
    level_low: _LevelLow = None,
    level_high: _LevelHigh = None,
) -> PostingSlotResponse:
    slot = await read.execute(
        ReadPostingSlotCommand(
            posting=_posting(
                user.id,
                pool_id,
                sport=sport,
                kind=kind,
                who=who,
                level_low=level_low,
                level_high=level_high,
            ),
            day=day,
            day_range=range_,
        )
    )
    return PostingSlotResponse.from_slot(slot)


@pools_router.post(
    "/{pool_id}/posts",
    response_model=PostedResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        **_POSTING_RESPONSES,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                _POSTING_REFUSED
                + " `court_hour_not_for_sale` — no court the grid offers at that "
                "club and hour: not one of the group's clubs, no longer selling, or "
                "past its book-by. **The button's three, in its order**: "
                "`payment_method_required` — no saved method (the setup opens); "
                "`live_posts_exhausted` — `details.cap` posts live already; "
                "`games_per_week_booked` — the poster's games per week are booked "
                "for the week from Monday `details.week`. Then "
                "`you_play_then` — the poster has a game at that hour; "
                "`nobody_fits_then` — none of their best fits is free then. "
                "Nothing was posted."
            ),
        },
    },
    summary="Post a game",
    description=(
        "*Post — you're In*: **posting is the poster's yes**. The game is made at "
        "the court hour picked — its share and book-by read off the club — for "
        "the *Who* and Level range the controls hold, both stored on it, and "
        "**dealt as up to three versions** to the poster's best fits free then: "
        "one per full set of them, the evenest first (in doubles 9 or more fits "
        "are three, 6–8 two, 3–5 one; fewer, one version with seats open). They "
        "see it as a *Challenge* (`CHALLENGE`), and until its book-by it keeps "
        "being dealt to anybody who becomes a fit. It is in the poster's *You're "
        "In* (`GET /players/me/live-yeses`), withdrawn there (`DELETE "
        "/proposals/{id}/yes`): with others In the game carries on without them; "
        "with nobody, the post is gone. Not full by its book-by, it disappears "
        "and nobody paid."
    ),
)
async def post_a_game(
    pool_id: UUID, body: PostRequest, user: CurrentUserDep, post: PostAGameDep
) -> PostedResponse:
    posted = await post.execute(
        PostAGameCommand(
            posting=_posting(
                user.id,
                pool_id,
                sport=body.sport,
                kind=body.kind,
                who=body.who,
                level_low=body.level_low,
                level_high=body.level_high,
            ),
            club_id=body.club_id,
            start=instant(body.starts_at),
        )
    )
    return PostedResponse.from_posted(posted)


# --------------------------------------------------------------------------- #
# The friends card (#750)
# --------------------------------------------------------------------------- #

_LINE_UP_REFUSED = (
    "Each names nobody. `not_a_friend` — somebody seated is not the reader's "
    "friend now: the seat is emptied. `no_level` — somebody seated, or the "
    "reader, holds no level in the sport. `cannot_play_together` — two of them "
    "blocked each other, either way round: *These four can't all play together. "
    "Swap someone.* — never which two."
)

_FRIENDS_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": (
            "`wrong_line_up_size` — not the friends the sport seats beside the "
            "reader, each once and never the reader: `details.friends`, three in "
            "doubles, one in singles."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`pool_not_found` — no such group, or the reader is not in it. One "
            "code for both. The friends need not be in it: a friend who is not "
            "a member plays as a guest."
        ),
    },
    status.HTTP_409_CONFLICT: {"model": ErrorResponse, "description": _LINE_UP_REFUSED},
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": (
            "`block_state_unavailable` — whether two of them blocked each other "
            "could not be read. Retry."
        ),
    },
}

_FriendIds = Annotated[
    list[UUID],
    Query(
        description=(
            "The friends seated beside the reader, in the order seated: three in "
            "doubles, one in singles."
        )
    ),
]

_LINE_UP_RULES = (
    " **Friends choose each other**: blocks and a level in the sport apply, and "
    "the level window, the kind's tolerance, gender preferences, a Play intent "
    "and *most I'll pay* don't. A friend who is not in the group plays as a "
    "guest. Nothing is recorded: no game is made and no court is held."
)


@pools_router.get(
    "/{pool_id}/friends-card",
    response_model=FriendsCardResponse,
    responses={
        **_FRIENDS_RESPONSES,
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                _FRIENDS_RESPONSES[status.HTTP_400_BAD_REQUEST]["description"]
                + " `sides_not_of_the_line_up` — `partner_id` is not one of the "
                "friends seated, or the sport is singles. `court_hour_incomplete` "
                "— `court_id` without `starts_at`, or the other way round."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                _LINE_UP_REFUSED
                + " `court_hour_not_for_sale` — the court-hour sent is not one *Find "
                "a court* lists now: taken, past its book-by, not under the group's "
                "court rule, or an hour one of them now has a game at. Read the "
                "card again without it."
            ),
        },
    },
    summary="The friends card",
    description=(
        "The **Friends** tab, every seat filled: the deck's card without its "
        "tiles, for the reader and the friends they seated. **The sides** are "
        "the evenest way they can stand, by the engine's own forecast — or, "
        "after a swap, the way with `partner_id` beside the reader — and the "
        "court above the card draws the same. **The court** is the one picked "
        "in *Find a court* (`court_id` and `starts_at`), or the one proposed: "
        "the soonest hour, up to 14 days ahead, where the whole line-up is free, "
        "a court is free under the group's court rule and none of them has a "
        "game — failing that, the soonest where most of them are free — and "
        "`null` when there is none. Around it the overlap of their weeks and "
        "the club's cut-off." + _LINE_UP_RULES
    ),
)
async def read_friends_card(
    pool_id: UUID,
    sport: Sport,
    kind: SearchMode,
    friend_ids: _FriendIds,
    user: CurrentUserDep,
    read: ReadFriendsCardDep,
    partner_id: Annotated[
        UUID | None,
        Query(
            description=(
                "After a swap, the friend beside the reader (doubles only); left "
                "out, the evenest sides."
            )
        ),
    ] = None,
    court_id: Annotated[
        UUID | None, Query(description="A court picked in *Find a court*.")
    ] = None,
    starts_at: Annotated[
        datetime | None, Query(description="Its hour, as listed.")
    ] = None,
) -> FriendsCardResponse:
    card = await read.execute(
        ReadFriendsCardCommand(
            line_up=FriendsLineUpCommand(
                player_id=user.id, pool_id=pool_id, sport=sport, friend_ids=friend_ids
            ),
            kind=kind,
            partner_id=partner_id,
            court_id=court_id,
            starts_at=None if starts_at is None else instant(starts_at),
        )
    )
    return FriendsCardResponse.from_card(card)


@pools_router.get(
    "/{pool_id}/friends-card/courts",
    response_model=FriendsCourtsResponse,
    responses=_FRIENDS_RESPONSES,
    summary="Find a court",
    description=(
        "*Pick a different court* on the friends card: **every court the line-up "
        "could take**, from the soonest hour still sellable to 14 days ahead, "
        "under the group's court rule — for an official group, another club's "
        "only at an hour the home club has none free, marked `home_club_full`. "
        "Each row says how many of them are free for the whole hour and who is "
        "busy — outside their weekly hours. An hour where one of them already "
        "has a game, or whose week already holds all the games they play, is "
        "left out." + _LINE_UP_RULES
    ),
)
async def read_friends_courts(
    pool_id: UUID,
    sport: Sport,
    friend_ids: _FriendIds,
    user: CurrentUserDep,
    read: ReadFriendsCourtsDep,
) -> FriendsCourtsResponse:
    courts = await read.execute(
        FriendsLineUpCommand(
            player_id=user.id, pool_id=pool_id, sport=sport, friend_ids=friend_ids
        )
    )
    return FriendsCourtsResponse.from_courts(courts)


# --------------------------------------------------------------------------- #
# A friends game (#751; docs/adr/0202 §5–§6)
# --------------------------------------------------------------------------- #


@pools_router.post(
    "/{pool_id}/friends-games",
    response_model=FriendsGameSentResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_FRIENDS_RESPONSES,
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                _FRIENDS_RESPONSES[status.HTTP_400_BAD_REQUEST]["description"]
                + " `sides_not_of_the_line_up` — `partner_id` is not one of the "
                "friends seated, or the sport is singles."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                _FRIENDS_RESPONSES[status.HTTP_404_NOT_FOUND]["description"]
                + " `booking_not_found` — `booking_id` is a game somebody else "
                "sent."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                _LINE_UP_REFUSED
                + " In the send sheet's order: `payment_method_required` — save a "
                "method first; `friends_games_waiting` — 2 friends games already "
                "wait for answers (`details.cap`); `you_play_then` — the sender "
                "has a game at that hour; `games_per_week_booked` — the sender's "
                "week is full (`details.games_per_week`, `details.week`); "
                "`court_just_taken` — another game took the court a moment ago: "
                "nothing was charged, read the card again; `court_hour_not_for_"
                "sale` — the club no longer sells it."
            ),
        },
    },
    summary="Send a friends game, and book its court",
    description=(
        "*Send game and pay* on the send sheet: **the court is booked at once** "
        "(`docs/adr/0202` §5). The line-up is read exactly as the friends card "
        "reads it; then the sender's own share and **a cover for every other "
        "seat** — the whole court — are held on their card **all or nothing, "
        "with them present**, and the most they agreed to is recorded with "
        "their terms. Held until the club's cut-off (or, far ahead, checked "
        "and held four days before it). **Every hold in**, the booking is born "
        "with the sender In and every friend's seat held for them for 24 hours, "
        "never past the cut-off; the chat opens; the sender's other yeses at "
        "that hour are withdrawn; each friend is told. **A refused card books "
        "nothing**: `your_payments` names each payment to confirm in the app, "
        "then send again with `booking_id`. A retried send that booked answers "
        "what it booked. At the cut-off each seat's own held share is taken, "
        "and a cover only for a seat without its own payment."
    ),
)
async def send_a_friends_game(
    pool_id: UUID,
    body: SendFriendsGameRequest,
    user: CurrentUserDep,
    send: SendAFriendsGameDep,
) -> FriendsGameSentResponse:
    sent = await send.execute(
        SendAFriendsGameCommand(
            line_up=FriendsLineUpCommand(
                player_id=user.id,
                pool_id=pool_id,
                sport=body.sport,
                friend_ids=body.friend_ids,
            ),
            kind=body.kind,
            court_id=body.court_id,
            starts_at=instant(body.starts_at),
            pay_mode=body.pay_mode,
            partner_id=body.partner_id,
            booking_id=body.booking_id,
        )
    )
    return FriendsGameSentResponse.of(sent)


_INVITATION_NOT_FOUND = {
    "model": ErrorResponse,
    "description": (
        "`booking_not_found` — no such friends game **for this player**: it does "
        "not exist, or they were never invited to it. One code for both."
    ),
}

_INVITATION_GONE = (
    "`invitation_not_waiting` — they answered it already, or their 24 hours "
    "ended. `booking_is_called_off` — the game is off (`details.reason`). "
    "`game_has_started`. Nothing was recorded."
)


@bookings_router.post(
    "/{booking_id}/invitation/acceptance",
    response_model=FriendsGameAnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: _INVITATION_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                _INVITATION_GONE
                + " `you_play_then` — *You already have a game at 10:00.* "
                "`games_per_week_booked` — *Your week is full: 3 games, the most "
                "you set in Games & money.* (`details.games_per_week`). "
                "`payment_method_required` — with *Split the cost*, save a method "
                "first."
            ),
        },
    },
    summary="Accept a friends game",
    description=(
        "*Accept and pay 25 zł* — or, with *Whole court*, *Accept* — on a "
        "FRIENDS GAME card. **With *Split the cost*** the reader's own share is "
        "held on their card until the cut-off, with them present: a bank "
        "confirmation is completed in the app (`your_payment`, then `POST "
        "/seat-charges/{id}/confirmation`, which accepts), and a refused card "
        "leaves the seat theirs to retry until their invitation ends. **With "
        "*Whole court*** nothing is held. Accepted, they are In and in the "
        "chat, and their other yeses at that hour are withdrawn; the card moves "
        "to Your games. When the last seat is taken, all four are told *It's a "
        "game!*. A second accept answers the same."
    ),
)
async def accept_a_friends_game(
    booking_id: UUID, user: CurrentUserDep, accept: AcceptAFriendsGameDep
) -> FriendsGameAnswerResponse:
    accepted = await accept.execute(
        FriendsGameCommand(player_id=user.id, booking_id=booking_id)
    )
    return FriendsGameAnswerResponse.of(accepted)


@bookings_router.post(
    "/{booking_id}/invitation/decline",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_404_NOT_FOUND: _INVITATION_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": _INVITATION_GONE,
        },
    },
    summary="Decline a friends game",
    description=(
        "*Not this time* on a FRIENDS GAME card: the card leaves Home, the seat "
        "is empty, and the sender is told *Ania can't make it*. A second tap "
        "records nothing."
    ),
)
async def decline_a_friends_game(
    booking_id: UUID, user: CurrentUserDep, decline: DeclineAFriendsGameDep
) -> Response:
    await decline.execute(
        FriendsGameCommand(player_id=user.id, booking_id=booking_id)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@bookings_router.post(
    "/{booking_id}/call-off",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`booking_not_found` — no such friends game **sent by this "
                "player**. One code for both."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`cut_off_has_passed` — the club's cut-off came: it can no longer "
                "be called off for free. `booking_is_called_off` — it is off "
                "already. `game_has_started`. Nothing was recorded."
            ),
        },
    },
    summary="Call a friends game off",
    description=(
        "The sender's *Call it off for everyone*, before the club's cut-off: "
        "every hold and cover is let go — nobody pays — the court is the club's "
        "again, the chat closes, and everybody In and every friend still "
        "invited is told *Tomek called off Saturday 10:00 · Nobody paid*."
    ),
)
async def call_off_a_friends_game(
    booking_id: UUID, user: CurrentUserDep, call_off: CallOffAFriendsGameDep
) -> Response:
    await call_off.execute(
        FriendsGameCommand(player_id=user.id, booking_id=booking_id)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


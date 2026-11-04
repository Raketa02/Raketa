"""**The club's Raketa bookings**, on the club surface: **the club runs them** —
a day of bookings, Move and Cancel (#547; the mechanics §16.7, §16.9, §16.14;
the screens B4, B6), the Cancel dialog's preview, and a cancel another court
absorbs (#672). The desk's Check in is removed (#651), and so are On
request's waiting list, Accept and Refuse (#669; ``docs/adr/0196`` §1): no club
confirms a game.

Mounted under ``/api/v1/club``, which only the club website consumes
(``docs/adr/0187`` §5), and it takes a **club-audience** token: a desk runs its
own club's bookings. **Signed by this context** because a cancel refunds and
owes a new card, and every act on a game locks its proposal first.

**What the club sees of a player is their nickname, and whether they paid or
their share is only held** (§16.14; ``docs/adr/0199`` §5). The field keeps the
word ``name`` until #725 renames it.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from app.core.exception_handlers import ErrorResponse
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, invariant
from app.modules.clubs.presentation.dependencies import CurrentClubAccountDep
from app.modules.proposals.application.club_bookings import (
    ClubBookingRow,
    ClubDay,
)
from app.modules.proposals.application.club_money import ClubMoney, MoneyRow
from app.modules.proposals.domain.club_bookings import (
    CancelOutcome,
    ClubFilter,
    ClubStatus,
    CourtToMoveTo,
    price_of,
)
from app.modules.proposals.domain.deck import GAME_LENGTH
from app.modules.proposals.domain.home import BookedGame, ClubCancelReason
from app.modules.proposals.presentation.dependencies import (
    CancelTheGameDep,
    MoveTheGameDep,
    PreviewTheCancelDep,
    ReadClubBookingsDep,
    ReadClubMoneyDep,
    ReadFreeCourtsDep,
)

router = APIRouter(prefix="/bookings", tags=["club"])
#: The Money page reads here (#548).
money_router = APIRouter(prefix="/money", tags=["club"])


# The two reasons a booking of the club's can come to, as its desk reads them.
# The players' reasons for a game that never booked (``BOOK_BY_PASSED``,
# ``COURT_HOUR_LOST``, ``PAYMENT_NOT_IN_TIME``, #625) are never the club's — such
# a game is on no page of its — so the club's document keeps the players'
# enum's name and its own values, and says nothing of them.
class CalledOffReason(StrEnum):
    """Why a game will not be played (the mechanics §14.1, §16.7)."""

    SHORT_AT_THE_CUT_OFF = "SHORT_AT_THE_CUT_OFF"
    CANCELLED_BY_THE_CLUB = "CANCELLED_BY_THE_CLUB"


def _reason_for_the_club(game: BookedGame, *, read_at: Instant) -> CalledOffReason:
    reason = invariant(
        game.called_off_reason(read_at),
        f"{game.booking_id} is called off for the club with no reason",
    )
    return CalledOffReason(reason.value)


# --------------------------------------------------------------------------- #
# The club runs its bookings (#547)
# --------------------------------------------------------------------------- #


class ClubBookingPlayerSchema(BaseModel):
    """A player on the game, as the club sees them — **a name, and whether they
    paid or their share is only held**, and nothing else (§16.14)."""

    player_id: UUID
    name: str | None = Field(
        description=(
            "Their nickname, whole (docs/adr/0199 §5). `null` for an account "
            "that can no longer be named."
        )
    )
    paid: bool = Field(description="Their share was taken — *paid ✓*.")
    held: bool = Field(
        description=(
            "Their share is held on their card, and taken at the cut-off — "
            "*held*. Not paid, and not in `collected_grosze` (#637). Never "
            "`true` with `paid`."
        )
    )


class ClubBookingMoneySchema(BaseModel):
    price_grosze: int = Field(description="The court's price for the hour.")
    collected_grosze: int = Field(
        description=(
            "Every share taken from the players, on your account — at your "
            "cut-off, or at once after it. A share only held is not collected "
            "(#637)."
        )
    )
    refunded_grosze: int | None = Field(
        description=(
            "Everything given back of a share taken — to a leaver whose seat "
            "was taken after the cut-off, less exactly the fee kept on their "
            "payment; in full on a game cancelled after it. A hold let go "
            "before the cut-off refunds nothing: nothing was taken. Refunds are "
            "automatic: you never refund anybody by hand. `null` — *not yet "
            "known* — while a refund less the fee waits for a fee the provider "
            "has not told you yet (#641); never an estimate."
        )
    )


class BookedFromSchema(BaseModel):
    """The group the game was booked in — *where it came from*."""

    group_id: UUID
    name: str
    official: bool = Field(
        description="One of your official groups — or `false`, a player group."
    )


class ClubCountsSchema(BaseModel):
    """How many of the day's bookings each filter shows."""

    all: int
    seat_open: int
    called_off: int


class ClubBookingSchema(BaseModel):
    """One Raketa booking at the club."""

    booking_id: UUID
    starts_at: datetime = Field(description="The court hour's start; games are 1 h.")
    ends_at: datetime
    court_name: str = Field(description="The court it is on.")
    indoor: bool = Field(
        description="The court's kind — *Court 3 · indoor* — as the players see it."
    )
    sport: Sport
    kind: SearchMode = Field(description="Competitive, or for fun (a friendly).")
    status: ClubStatus = Field(
        description=(
            "`BOOKED` — full; each share held until your cut-off and taken at "
            "it (#637). `SEAT_OPEN` — "
            "a player left and Raketa is finding a replacement; before the "
            "cut-off, a seat still open at it calls the game off and the court "
            "comes back to you. `CALLED_OFF` — see `called_off_reason`; everybody "
            "was refunded or nobody paid, and the hour is free again — but the "
            "court you cancelled stays closed for it, an exception you remove to "
            "sell it again (#673). `PLAYED` — "
            "the hour has passed; you are paid whatever happened on the court."
        )
    )
    called_off_reason: CalledOffReason | None = Field(
        description=(
            "Why a `CALLED_OFF` game will not be played — `null` otherwise. "
            "`SHORT_AT_THE_CUT_OFF` — a seat was still empty at your cut-off. "
            "`CANCELLED_BY_THE_CLUB` — you cancelled it (`cancel_reason`)."
        )
    )
    cancel_reason: ClubCancelReason | None = Field(
        description="Why you cancelled it — on a game you cancelled, else `null`."
    )
    players: list[ClubBookingPlayerSchema] = Field(
        description="Everybody with a seat on it, the first side first."
    )
    open_seats: int = Field(description="Seats a leaver left open.")
    money: ClubBookingMoneySchema
    booked_from: BookedFromSchema | None = Field(
        description="The group it came from — `null` for a group that is gone."
    )
    may_move_or_cancel: bool = Field(
        description=(
            "**Move** and **Cancel** are yours: booked or with a seat open, and "
            "not started yet."
        )
    )

    @classmethod
    def of(cls, row: ClubBookingRow, *, day: ClubDay) -> "ClubBookingSchema":
        game = row.game
        return cls(
            booking_id=game.booking_id,
            starts_at=game.start,
            ends_at=game.start + GAME_LENGTH,
            court_name=game.court_name,
            indoor=game.indoor,
            sport=game.sport,
            kind=game.kind,
            status=row.status,
            called_off_reason=_reason_for_the_club(game, read_at=day.read_at)
            if row.status is ClubStatus.CALLED_OFF
            else None,
            cancel_reason=(
                game.cancel_reason if row.status is ClubStatus.CALLED_OFF else None
            ),
            players=[
                ClubBookingPlayerSchema(
                    player_id=player,
                    name=day.names.get(player),
                    paid=player in row.takings.paid,
                    held=player in row.takings.held,
                )
                for player in game.players
            ],
            open_seats=game.open_seats,
            money=ClubBookingMoneySchema(
                price_grosze=price_of(game),
                collected_grosze=row.takings.collected_grosze,
                refunded_grosze=row.takings.refunded_grosze,
            ),
            booked_from=(
                None
                if row.booked_from is None
                else BookedFromSchema(
                    group_id=game.pool_id,
                    name=row.booked_from.name,
                    official=row.booked_from.official,
                )
            ),
            may_move_or_cancel=row.still_to_be_played,
        )


class ClubBookingsResponse(BaseModel):
    """One day of the club's Raketa bookings — the Bookings page."""

    day: date = Field(description="The club's calendar day read.")
    read_at: datetime = Field(
        description="The instant every status and countdown here was read at."
    )
    filter: ClubFilter
    counts: ClubCountsSchema
    bookings: list[ClubBookingSchema] = Field(
        description=("Soonest first. Empty: *No Raketa bookings on this day.*")
    )

    @classmethod
    def of(cls, day: ClubDay) -> "ClubBookingsResponse":
        return cls(
            day=day.day,
            read_at=day.read_at,
            filter=day.chosen,
            counts=ClubCountsSchema(
                all=day.counts[ClubFilter.ALL],
                seat_open=day.counts[ClubFilter.SEAT_OPEN],
                called_off=day.counts[ClubFilter.CALLED_OFF],
            ),
            bookings=[ClubBookingSchema.of(row, day=day) for row in day.rows],
        )


class CourtToMoveToSchema(BaseModel):
    court_id: UUID
    name: str
    indoor: bool = Field(description="Its kind — *Court 3 · indoor*.")

    @classmethod
    def of(cls, court: CourtToMoveTo) -> "CourtToMoveToSchema":
        return cls(court_id=court.court_id, name=court.name, indoor=court.indoor)


class FreeCourtsResponse(BaseModel):
    courts: list[CourtToMoveToSchema] = Field(
        description=(
            "Every other court of the game's sport you still have for Raketa at "
            "its hour **that keeps the game's kind** — the same kind, or an "
            "indoor court for an outdoor game, never outdoors from indoors — in "
            "your own order, each with its kind. Empty: there is none — "
            "**Cancel** with *repair* if the court cannot be played."
        )
    )


class MoveRequest(BaseModel):
    court_id: UUID = Field(description="One of the game's free courts.")


class CancelRequest(BaseModel):
    reason: ClubCancelReason = Field(
        description=(
            "`WEATHER`, `REPAIR`, `DOUBLE_BOOKING` or `OTHER` — told to the "
            "players with what comes of their money, or, when another of your "
            "courts takes the game, as why the court it left can't be played."
        )
    )
    anyway: bool = Field(
        default=False,
        description=(
            "**Cancel the game anyway** — for a club closing the whole hour (an "
            "event, a power cut): the game is called off even when another "
            "court would take it."
        ),
    )


class CancelOutcomeKind(StrEnum):
    """What a cancel came to — or, in its preview, would come to (#672)."""

    #: Another of the club's courts took the game: *This game moves to Court 3
    #: · indoor · the players are told, nobody is refunded*.
    MOVED = "MOVED"
    #: The game is called off.
    CALLED_OFF = "CALLED_OFF"


class CancelOutcomeSchema(BaseModel):
    outcome: CancelOutcomeKind = Field(
        description=(
            "`MOVED` — a free court of yours at the game's hour, sold at its "
            "price, of its kind or indoor for an outdoor game (indoor only for "
            "`WEATHER`), takes the game: every hold or payment stays as it is, "
            "nobody is refunded, and the players are told *Game moved*. "
            "`CALLED_OFF` — the game is off, the money as the cancel says."
        )
    )
    court: CourtToMoveToSchema | None = Field(
        description="The court the game moves to, and its kind; `null` when called off."
    )

    @classmethod
    def of(cls, outcome: CancelOutcome) -> "CancelOutcomeSchema":
        if outcome.moved_to is None:
            return cls(outcome=CancelOutcomeKind.CALLED_OFF, court=None)
        return cls(
            outcome=CancelOutcomeKind.MOVED,
            court=CourtToMoveToSchema.of(outcome.moved_to),
        )


_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "`booking_not_found` — no such booking at this club.",
    }
}

_NOT_TO_BE_PLAYED = (
    "`booking_is_called_off` — it is off already. `game_has_started` — its hour "
    "has begun. Nothing was recorded."
)


@router.get(
    "",
    response_model=ClubBookingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Your bookings, by day",
    description=(
        "Every Raketa booking at this club on one of its calendar days — the "
        "Bookings page — each with its status, its players (name, *paid*, "
        "*held*), its money (the court's price, collected, refunded) and the "
        "group it came from. `filter` narrows the list; `counts` are the "
        "whole day's."
    ),
)
async def bookings_on_a_day(
    account: CurrentClubAccountDep,
    read: ReadClubBookingsDep,
    day: date | None = Query(
        default=None, alias="date", description="The day — today when left out."
    ),
    chosen: ClubFilter = Query(default=ClubFilter.ALL, alias="filter"),
) -> ClubBookingsResponse:
    return ClubBookingsResponse.of(
        await read.execute(account.club_id, day=day, chosen=chosen)
    )


@router.get(
    "/{booking_id}/free-courts",
    response_model=FreeCourtsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": _NOT_TO_BE_PLAYED,
        },
    },
    summary="Where a game can be moved",
    description="The Move dialog: the free courts of the game's sport at its hour.",
)
async def free_courts(
    booking_id: UUID, account: CurrentClubAccountDep, read: ReadFreeCourtsDep
) -> FreeCourtsResponse:
    courts = await read.execute(club_id=account.club_id, booking_id=booking_id)
    return FreeCourtsResponse(courts=[CourtToMoveToSchema.of(one) for one in courts])


@router.post(
    "/{booking_id}/move",
    response_model=CourtToMoveToSchema,
    status_code=status.HTTP_200_OK,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                f"{_NOT_TO_BE_PLAYED} `court_not_free` — that court is not a free "
                "court of the game's sport at its hour, or is outdoors for an "
                "indoor game. `court_just_taken` — another game took it a moment "
                "ago; read the free courts again."
            ),
        },
    },
    summary="Move a game to another court",
    description=(
        "**Move** a booked game — whole or with a seat open — onto another free "
        "court of its sport at the same hour, of the same kind or indoor for an "
        "outdoor game, until it starts. The players read the new number and "
        "its kind, and are told *Game moved*; nothing else about the game "
        "changes. Answers the court it is on now."
    ),
)
async def move(
    booking_id: UUID,
    payload: MoveRequest,
    account: CurrentClubAccountDep,
    move: MoveTheGameDep,
) -> CourtToMoveToSchema:
    return CourtToMoveToSchema.of(
        await move.execute(
            club_id=account.club_id, booking_id=booking_id, court_id=payload.court_id
        )
    )


@router.get(
    "/{booking_id}/cancellation/preview",
    response_model=CancelOutcomeSchema,
    status_code=status.HTTP_200_OK,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": _NOT_TO_BE_PLAYED,
        },
    },
    summary="What a cancel would do",
    description=(
        "The Cancel dialog: what cancelling with this `reason` would do now — "
        "**move the game** to another of your courts at its hour (`MOVED`, "
        "with the court and its kind), or **call it off** (`CALLED_OFF`). A "
        "court takes the game when it is free at the game's hour, sold at the "
        "game's price, and of the same kind or indoor for an outdoor game — "
        "indoor only for `WEATHER`, since an outdoor court at the same hour is "
        "rained on too; the same kind first, then indoor, in your own order. "
        "When it would move, offer **Cancel the game anyway**. The cancel "
        "itself decides afresh."
    ),
)
async def cancellation_preview(
    booking_id: UUID,
    account: CurrentClubAccountDep,
    read: PreviewTheCancelDep,
    reason: ClubCancelReason = Query(description="The reason the desk chose."),
) -> CancelOutcomeSchema:
    return CancelOutcomeSchema.of(
        await read.execute(
            club_id=account.club_id, booking_id=booking_id, because=reason
        )
    )


@router.post(
    "/{booking_id}/cancellation",
    response_model=CancelOutcomeSchema,
    status_code=status.HTTP_200_OK,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                f"{_NOT_TO_BE_PLAYED} `court_just_taken` — the court that would "
                "have taken the game went to another game a moment ago; cancel "
                "again and it decides afresh."
            ),
        },
    },
    summary="Cancel a game",
    description=(
        "**Cancel** a booked game, with your reason, until it starts. **First, "
        "another of your courts takes it when one can** — free at the game's "
        "hour, sold at its price, of its kind or indoor for an outdoor game, "
        "indoor only for `WEATHER` — read afresh now, whatever the preview "
        "said: the game **moves** there, every hold or payment stays exactly as "
        "it is, nobody is refunded, nobody is owed a new game, and the players "
        "are told *Game moved* with why the court they left can't be played. "
        "**Otherwise, or with `anyway`, the game is called off**: **before your "
        "cut-off** every share is only held, and every hold is let go — nothing "
        "was taken, nobody is refunded and nobody pays a fee, you included "
        "(#637); **after it** everybody is **refunded in full** — the card fees "
        "on those payments are not returned, and as the seller you bear them. "
        "Either way it goes on **nobody's record**, and the players are told "
        "you cancelled, with the reason, and dealt a new game first. **Moved or "
        "called off, the court the game was on is closed for that hour** — it "
        "can't be played then — as an exception on your list, worded by the "
        "reason; remove it to sell the court again. Answers which it was."
    ),
)
async def cancel(
    booking_id: UUID,
    payload: CancelRequest,
    account: CurrentClubAccountDep,
    cancel: CancelTheGameDep,
) -> CancelOutcomeSchema:
    return CancelOutcomeSchema.of(
        await cancel.execute(
            club_id=account.club_id,
            booking_id=booking_id,
            because=payload.reason,
            anyway=payload.anyway,
        )
    )


# --------------------------------------------------------------------------- #
# Money (#548)
# --------------------------------------------------------------------------- #


class MoneyTotalsSchema(BaseModel):
    collected_grosze: int = Field(
        description=(
            "Every share taken from the players — at your cut-off, or at once "
            "after it; never a share only held (#637)."
        )
    )
    refunded_grosze: int | None = Field(
        description=(
            "Everything given back — automatically: you never refund anybody by "
            "hand. `null` while a booking's is not yet known."
        )
    )
    card_fees_grosze: int | None = Field(
        description=(
            "The provider's card fee on every share taken, yours to pay as at "
            "your own terminal. A refund never returns it. **The real fees, or "
            "`null` — *not yet known*** — while any booking's is (#641): a club "
            "on its own negotiated pricing is told its fees after the take. "
            "Never an estimate."
        )
    )
    net_grosze: int | None = Field(
        description=(
            "Yours: collected, less refunded, less the card fees. Below nought "
            "when games given back whole cost you their card fees. `null` while "
            "the card fees or the refunds are not yet known."
        )
    )


class MoneyBookingSchema(BaseModel):
    """One booking's money, on your account — you are the seller."""

    booking_id: UUID
    starts_at: datetime = Field(description="The court hour's start — the row's date.")
    court_name: str
    sport: Sport
    status: ClubStatus = Field(
        description="What the booking is now, as on the Bookings page."
    )
    collected_grosze: int
    refunded_grosze: int | None = Field(
        description="`null` while a refund less the fee kept is not yet known."
    )
    card_fees_grosze: int | None = Field(
        description=(
            "The real fee the provider kept on each share taken, or `null` — "
            "*not yet known* — until it has said every one (#641)."
        )
    )
    net_grosze: int | None = Field(
        description="`null` while the card fees or the refunds are not yet known."
    )
    paid_out: bool = Field(
        description=(
            "A payout carried its money to your bank. Until then it waits on "
            "your account: **you are paid after the game is played**, at the "
            "close of its day, since a refund before the start comes out of it."
        )
    )

    @classmethod
    def of(cls, row: MoneyRow) -> "MoneyBookingSchema":
        game, takings = row.game, row.takings
        return cls(
            booking_id=game.booking_id,
            starts_at=game.start,
            court_name=game.court_name,
            sport=game.sport,
            status=row.status,
            collected_grosze=takings.collected_grosze,
            refunded_grosze=takings.refunded_grosze,
            card_fees_grosze=takings.card_fees_grosze,
            net_grosze=takings.net_grosze,
            paid_out=takings.paid_out,
        )


class ClubMoneyResponse(BaseModel):
    """A month of your Raketa money — the Money page."""

    month: str = Field(description="The month read, `YYYY-MM`.", examples=["2026-10"])
    read_at: datetime
    totals: MoneyTotalsSchema = Field(description="The month's, at the top.")
    bookings: list[MoneyBookingSchema] = Field(
        description=(
            "Every booking played — or to be played — in the month that took "
            "money, soonest first. A request nobody paid for is not money and "
            "is not listed."
        )
    )

    @classmethod
    def of(cls, money: ClubMoney) -> "ClubMoneyResponse":
        totals = money.totals
        return cls(
            month=f"{money.month:%Y-%m}",
            read_at=money.read_at,
            totals=MoneyTotalsSchema(
                collected_grosze=totals.collected_grosze,
                refunded_grosze=totals.refunded_grosze,
                card_fees_grosze=totals.card_fees_grosze,
                net_grosze=totals.net_grosze,
            ),
            bookings=[MoneyBookingSchema.of(row) for row in money.rows],
        )


#: A month as the page asks for it.
_MONTH = r"^\d{4}-(0[1-9]|1[0-2])$"


@money_router.get(
    "",
    response_model=ClubMoneyResponse,
    status_code=status.HTTP_200_OK,
    summary="Your money, by month",
    description=(
        "A month of your Raketa money, booking by booking — by the day each "
        "game is played on — with what the players paid, what was given back, "
        "the card fees and what is yours, and the month's totals. **You are the "
        "seller**: every figure is your own account's. Your payouts are "
        "`GET /api/v1/club/payouts`."
    ),
)
async def money_by_month(
    account: CurrentClubAccountDep,
    read: ReadClubMoneyDep,
    month: str | None = Query(
        default=None,
        pattern=_MONTH,
        description="`YYYY-MM` — this month when left out.",
    ),
) -> ClubMoneyResponse:
    return ClubMoneyResponse.of(
        await read.execute(
            account.club_id,
            month=None if month is None else date.fromisoformat(f"{month}-01"),
        )
    )

"""The club's courts, their Raketa hours, exceptions, prices and settings, on the
club surface (#535, the mechanics §16, the screens B2–B5).

Mounted only on the club surface (``app/api/v1/club.py``), and every route takes
a **club-audience** token: a desk sets up its own club and no other, so the club
is always the session's and never a path's.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.clubs.application.commands import (
    AddCourtCommand,
    AddExceptionCommand,
    ChangeCourtCommand,
    RemoveCourtCommand,
    PriceBandInput,
    RemoveExceptionCommand,
    SaveRaketaSettingsCommand,
    SetPricesCommand,
    SetRaketaHoursCommand,
    SportPriceInput,
)
from app.modules.clubs.domain.club_courts import ClubCourts
from app.modules.clubs.presentation.courts_schemas import (
    CourtChangeRequest,
    CourtRequest,
    CourtResponse,
    CourtsResponse,
    ExceptionRequest,
    ExceptionResponse,
    ExceptionsResponse,
    PricesRequest,
    PricesResponse,
    RaketaHoursRequest,
    RaketaSettingsRequest,
    RaketaSettingsResponse,
    SetupResponse,
)
from app.modules.clubs.presentation.dependencies import (
    AddCourtDep,
    AddExceptionDep,
    ChangeCourtDep,
    CurrentClubAccountDep,
    ReadClubCourtsDep,
    ReadExceptionsDep,
    ReadPricesDep,
    ReadSetupDep,
    RemoveCourtDep,
    RemoveExceptionDep,
    SaveRaketaSettingsDep,
    SetPricesDep,
    SetRaketaHoursDep,
)

router = APIRouter(tags=["club"])


def _courts(club: ClubCourts) -> CourtsResponse:
    return CourtsResponse(
        courts=[CourtResponse.from_domain(court) for court in club.courts.values()]
    )


@router.get(
    "/courts",
    response_model=CourtsResponse,
    status_code=status.HTTP_200_OK,
    summary="The club's courts, and the Raketa hours of each",
)
async def read_courts(
    account: CurrentClubAccountDep, read: ReadClubCourtsDep
) -> CourtsResponse:
    return _courts(await read.execute(account.club_id))


@router.post(
    "/courts",
    response_model=CourtResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "A field the desk has to correct, named by `details.field`: "
                "`court_name_invalid` or `court_sport_not_offered`. Nothing was "
                "recorded."
            ),
        },
    },
    summary="Add a court",
    description=(
        "A court is born **offered**, and offers nothing until its Raketa hours "
        "are painted (`PUT /raketa-hours`)."
    ),
)
async def add_court(
    payload: CourtRequest, account: CurrentClubAccountDep, add: AddCourtDep
) -> CourtResponse:
    court = await add.execute(
        AddCourtCommand(
            club_id=account.club_id,
            name=payload.name,
            sport=payload.sport,
            indoor=payload.indoor,
        )
    )
    return CourtResponse.from_domain(court)


_COURT_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`court_not_found` — no court of this club has that id; another "
            "club's is the same answer. Nothing was recorded."
        ),
    },
}


@router.put(
    "/courts/{court_id}",
    response_model=CourtResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`court_name_invalid` or `court_sport_not_offered`, under "
                "`details.field`. Nothing was recorded."
            ),
        },
        **_COURT_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`court_name_taken` — another court at the club has the name, "
                "ignoring case; or `court_has_bookings` — a new sport for a "
                "court with a booking ahead of it. Nothing was recorded."
            ),
        },
    },
    summary="Edit a court, or switch it off or on",
    description=(
        "A full replacement of the court's name, sport, roof and whether it is "
        "offered. **Switching it off is allowed whatever is booked on it** — a "
        "booked game is played as booked — and keeps its hours; a new sport "
        "is refused while a booking is ahead of it. Saving it unchanged records "
        "nothing."
    ),
)
async def change_court(
    court_id: UUID,
    payload: CourtChangeRequest,
    account: CurrentClubAccountDep,
    change: ChangeCourtDep,
) -> CourtResponse:
    court = await change.execute(
        ChangeCourtCommand(
            club_id=account.club_id,
            court_id=court_id,
            name=payload.name,
            sport=payload.sport,
            indoor=payload.indoor,
            offered=payload.offered,
        )
    )
    return CourtResponse.from_domain(court)


@router.delete(
    "/courts/{court_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        **_COURT_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`court_has_bookings` — a booking is ahead of this court, one in "
                "progress included. Switch it off instead. Nothing was recorded."
            ),
        },
    },
    summary="Delete a court",
)
async def remove_court(
    court_id: UUID, account: CurrentClubAccountDep, remove: RemoveCourtDep
) -> None:
    await remove.execute(RemoveCourtCommand(club_id=account.club_id, court_id=court_id))


@router.put(
    "/raketa-hours",
    response_model=CourtsResponse,
    status_code=status.HTTP_200_OK,
    responses=_COURT_NOT_FOUND,
    summary="Set the Raketa hours of one court or several",
    description=(
        "The same week on every court named — one court's *Save hours*, *Copy to "
        "other courts* or *All courts of a sport*. Recorded per court, only where "
        "the week moved. **Never refused over a booking or a card**: a booked "
        "game is played as booked, and the pattern is what the club offers from "
        "now on. Answers every court of the club."
    ),
)
async def set_raketa_hours(
    payload: RaketaHoursRequest,
    account: CurrentClubAccountDep,
    set_hours: SetRaketaHoursDep,
) -> CourtsResponse:
    club = await set_hours.execute(
        SetRaketaHoursCommand(
            club_id=account.club_id,
            court_ids=tuple(payload.court_ids),
            hours=tuple((cell.day, cell.hour) for cell in payload.hours),
        )
    )
    return _courts(club)


@router.get(
    "/exceptions",
    response_model=ExceptionsResponse,
    status_code=status.HTTP_200_OK,
    summary="The hours the club has closed, that are not over yet",
)
async def read_exceptions(
    account: CurrentClubAccountDep, read: ReadExceptionsDep
) -> ExceptionsResponse:
    return ExceptionsResponse(
        exceptions=[
            ExceptionResponse.from_domain(exception)
            for exception in await read.execute(account.club_id)
        ]
    )


@router.post(
    "/exceptions",
    response_model=ExceptionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "A field the desk has to correct, named by `details.field`: "
                "`exception_reason_invalid` (`reason`), `exception_hours_invalid` "
                "(`hours`), `exception_days_invalid` or `exception_in_the_past` "
                "(`days`), `exception_courts_required` (`courts`). Nothing was "
                "recorded."
            ),
        },
        **_COURT_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`court_booked_then` — a booking holds an hour it would close. "
                "`details` names the first: `court_id`, `booking_id` and "
                "`starts_at`. Cancel the booking first. Nothing was recorded."
            ),
        },
    },
    summary="Close hours without touching the weekly pattern",
    description=(
        "An hour, a day or a run of days, on every court or some. **Allowed over "
        "an hour with cards on it** — the cards move to another court or "
        "disappear, and nobody was charged — and refused over a booking."
    ),
)
async def add_exception(
    payload: ExceptionRequest,
    account: CurrentClubAccountDep,
    add: AddExceptionDep,
) -> ExceptionResponse:
    exception = await add.execute(
        AddExceptionCommand(
            club_id=account.club_id,
            court_ids=None if payload.court_ids is None else tuple(payload.court_ids),
            first_day=payload.first_day,
            last_day=payload.last_day,
            from_hour=payload.from_hour,
            until_hour=payload.until_hour,
            reason=payload.reason,
        )
    )
    return ExceptionResponse.from_domain(exception)


@router.delete(
    "/exceptions/{exception_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`exception_not_found` — no exception of this club has that id; "
                "another club's is the same answer."
            ),
        },
    },
    summary="Remove an exception, opening its hours again",
)
async def remove_exception(
    exception_id: UUID, account: CurrentClubAccountDep, remove: RemoveExceptionDep
) -> None:
    await remove.execute(
        RemoveExceptionCommand(club_id=account.club_id, exception_id=exception_id)
    )


@router.get(
    "/prices",
    response_model=PricesResponse,
    status_code=status.HTTP_200_OK,
    summary="What a court-hour costs, per sport the club offers",
)
async def read_prices(
    account: CurrentClubAccountDep, read: ReadPricesDep
) -> PricesResponse:
    return PricesResponse.of(await read.execute(account.club_id))


@router.put(
    "/prices",
    response_model=PricesResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "A row the desk has to correct — `details.field` is `prices` and "
                "`details.sport` names the row: `price_sport_not_offered`, "
                "`price_sport_repeated`, `price_out_of_range` (with `least` and "
                "`most`), `price_does_not_split` (with `seats`), "
                "`price_band_hours_invalid` or `price_bands_overlap`. Rows are read "
                "in the order sent. Nothing was recorded."
            ),
        },
    },
    summary="Save the whole price table",
    description=(
        "A full replacement: a sport left out is no longer priced. Money is "
        "**integer grosze**. **New prices apply to new cards only** — a card "
        "already dealt, and a game already booked, keep their price."
    ),
)
async def set_prices(
    payload: PricesRequest, account: CurrentClubAccountDep, set_prices: SetPricesDep
) -> PricesResponse:
    prices = await set_prices.execute(
        SetPricesCommand(
            club_id=account.club_id,
            prices=tuple(
                SportPriceInput(
                    sport=row.sport,
                    price_grosze=row.price_grosze,
                    bands=tuple(
                        PriceBandInput(
                            days=band.days,
                            from_hour=band.from_hour,
                            until_hour=band.until_hour,
                            price_grosze=band.price_grosze,
                        )
                        for band in row.bands
                    ),
                )
                for row in payload.prices
            ),
        )
    )
    return PricesResponse.of(prices)


@router.get(
    "/raketa-settings",
    response_model=RaketaSettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="The club's Raketa settings",
    description=(
        "Every setting, **at its default until the club confirms it**. Only "
        "Raketa is the one way of working: Raketa sells the club's Raketa "
        "hours alone until each one's release time, the release lead before "
        "it, so there is no way to choose."
    ),
)
async def read_raketa_settings(
    account: CurrentClubAccountDep, read: ReadClubCourtsDep
) -> RaketaSettingsResponse:
    return RaketaSettingsResponse.from_domain(await read.execute(account.club_id))


@router.put(
    "/raketa-settings",
    response_model=RaketaSettingsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`setting_out_of_range` — `details.field` names the setting and "
                "`least` and `most` its range. Nothing was recorded."
            ),
        },
    },
    summary="Save — the first time, confirm — the club's Raketa settings",
    description=(
        "Every setting, defaults included: **the first save confirms them**, "
        "the setup checklist's last step. A changed setting applies to games "
        "booked after the change. Pausing stops new cards on the club's courts; "
        "booked games are played as booked."
    ),
)
async def save_raketa_settings(
    payload: RaketaSettingsRequest,
    account: CurrentClubAccountDep,
    save: SaveRaketaSettingsDep,
) -> RaketaSettingsResponse:
    club = await save.execute(
        SaveRaketaSettingsCommand(
            club_id=account.club_id,
            release_lead_days=payload.release_lead_days,
            cut_off_hours=payload.cut_off_hours,
            other_clubs_courts=payload.other_clubs_courts.offered,
            other_clubs_within_km=payload.other_clubs_courts.within_km,
            paused=payload.paused,
        )
    )
    return RaketaSettingsResponse.from_domain(club)


@router.get(
    "/setup",
    response_model=SetupResponse,
    status_code=status.HTTP_200_OK,
    summary="The setup checklist, and whether the club is live",
    description=(
        "Read off everything the club has set, never stored. The Overview shows "
        "it until `live`, and then gives way."
    ),
)
async def read_setup(
    account: CurrentClubAccountDep, read: ReadSetupDep
) -> SetupResponse:
    return SetupResponse.from_domain(await read.execute(account.club_id))

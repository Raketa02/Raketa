"""The club surface's shapes for Courts & prices and Raketa settings (#535).

**The requests declare types and nothing else**, for the reason the details'
do (``presentation/schemas.py``): every content rule — a name's length, a
price's range, a setting's bounds — is the domain's, and is refused with a code
the website writes its sentence from. What stays here is what nobody types: a
sport is a registry code, a day a date, a court an id.

**An hour cell is the player's own** (``WeeklyHourResource``): the same seven
days by sixteen hours from 07:00, bounded on the wire because a cell outside
the grid is not a thing any client draws.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.kernel import Sport
from app.modules.clubs.domain.club_courts import ClubCourts
from app.modules.clubs.domain.courts import Court
from app.modules.clubs.domain.hours_exceptions import HoursException
from app.modules.clubs.domain.prices import BandDays, SportPrices, seats, share_of
from app.modules.clubs.domain.raketa_terms import WayOfWorking
from app.modules.clubs.domain.payments_account import PaymentsStatus
from app.modules.clubs.domain.setup import SetupChecklist, SetupStep, StepState
from app.modules.player_profile.presentation.schemas import WeeklyHourResource


class CourtRequest(BaseModel):
    """A court as the desk types it into *Add a court* or its edit form."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description=(
            "What the club calls it — *Court 2*, *Kort centralny*. Trimmed, runs "
            "of whitespace collapsed, 1–40 characters: `court_name_invalid`. "
            "Unique among the club's courts, ignoring case: `409 court_name_taken`."
        )
    )
    sport: Sport = Field(
        description=(
            "One sport, from the club's own: `court_sport_not_offered` otherwise."
        )
    )
    indoor: bool = Field(description="Indoor, or outdoor. Shown on a player's card.")


class CourtChangeRequest(CourtRequest):
    """A court's edit form: the three facts it was added with, and whether it
    is offered — **all four on every save**, a full replacement."""

    offered: bool = Field(
        description=(
            "`false` switches it off: kept, with its hours, and selling nothing "
            "new. Allowed whatever is booked on it."
        )
    )


class RaketaHoursRequest(BaseModel):
    """*Weekly hours for Raketa*, saved on one court or several at once —
    which is what *Copy to other courts* and *All courts of a sport* send."""

    model_config = ConfigDict(extra="forbid")

    court_ids: list[UUID] = Field(
        min_length=1,
        description=(
            "Each court to give this week. One the club does not have refuses "
            "the whole save with `404 court_not_found`. A court named twice is "
            "named once."
        ),
    )
    hours: list[WeeklyHourResource] = Field(
        description=(
            "The week, as the player's grid spells it. **Empty is allowed**: a "
            "court offering nothing. A cell sent twice is one cell."
        )
    )


class CourtResponse(BaseModel):
    """A court as the desk's table shows it."""

    id: UUID
    name: str
    sport: Sport
    indoor: bool
    offered: bool = Field(
        description=(
            "Offered to Raketa, or switched off — kept, with its hours, and "
            "selling nothing."
        )
    )
    hours: list[WeeklyHourResource] = Field(
        description=(
            "The hours of an ordinary week this court is offered to Raketa, "
            "Monday-first and in the grid's order. Empty until they are painted."
        )
    )

    @classmethod
    def from_domain(cls, court: Court) -> "CourtResponse":
        return cls(
            id=court.id,
            name=court.name.value,
            sport=court.sport,
            indoor=court.indoor,
            offered=court.offered,
            hours=[
                WeeklyHourResource(day=day, hour=hour)
                for day, hour in court.hours.cells
            ],
        )


class CourtsResponse(BaseModel):
    courts: list[CourtResponse] = Field(
        description="Every court the club has, in the order they were added."
    )


class ExceptionRequest(BaseModel):
    """*Add an exception*: what, when, and why.

    The three forms the desk is offered are one shape: **a date** is a run of
    one day, **a range** a run of several, and **hours on a date** a run of one
    day with its hours — hours on a run of several close them on each day.
    """

    model_config = ConfigDict(extra="forbid")

    court_ids: list[UUID] | None = Field(
        description=(
            "`null` closes **every** court, one added later included; a list "
            "closes those — at least one (`exception_courts_required`), each the "
            "club's (`404 court_not_found`)."
        )
    )
    first_day: date = Field(description="The first local day it closes.")
    last_day: date = Field(
        description=(
            "The last local day it closes, inclusive — on or after `first_day` "
            "(`exception_days_invalid`), and not already over "
            "(`exception_in_the_past`)."
        )
    )
    from_hour: int | None = Field(
        description=(
            "With `until_hour`, the hours it closes on each day — 9 and 12 close "
            "09:00–12:00. Both `null` close the whole day; one alone, or hours "
            "outside 07:00–23:00, is `exception_hours_invalid`."
        )
    )
    until_hour: int | None = Field(description="The hour it closes until, exclusive.")
    reason: str = Field(
        description=(
            "For the club's own records, and the label its list shows. Trimmed, "
            "1–80 characters: `exception_reason_invalid`. No player reads it."
        )
    )


class ExceptionResponse(BaseModel):
    id: UUID
    court_ids: list[UUID] | None = Field(
        description=(
            "`null` for every court; otherwise the courts it closes, in the "
            "club's order. A deleted court leaves the list, and an exception "
            "left naming none is gone."
        )
    )
    first_day: date
    last_day: date
    from_hour: int | None
    until_hour: int | None
    reason: str

    @classmethod
    def from_domain(cls, exception: HoursException) -> "ExceptionResponse":
        return cls(
            id=exception.id,
            court_ids=(
                None if exception.court_ids is None else list(exception.court_ids)
            ),
            first_day=exception.first_day,
            last_day=exception.last_day,
            from_hour=None if exception.hours is None else exception.hours.opens,
            until_hour=None if exception.hours is None else exception.hours.closes,
            reason=exception.reason.value,
        )


class ExceptionsResponse(BaseModel):
    exceptions: list[ExceptionResponse] = Field(
        description=(
            "Every exception not over yet — its last day today or later, at the "
            "club — by its first day, then the hour it closes from (a whole day "
            "first), then the order they were added."
        )
    )


class PriceBandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: BandDays = Field(description="Monday to Friday, or Saturday and Sunday.")
    from_hour: int = Field(
        description=(
            "With `until_hour`, the hours it prices — 17 and 22 price "
            "17:00–22:00. Within 07:00–23:00, at least one hour: "
            "`price_band_hours_invalid`. Two bands of the same days may not "
            "overlap: `price_bands_overlap`."
        )
    )
    until_hour: int = Field(description="The hour it prices until, exclusive.")
    price_grosze: int = Field(
        description="The court-hour's price in those hours, in grosze."
    )


class SportPriceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sport: Sport = Field(
        description=(
            "A sport the club offers (`price_sport_not_offered`), once per save "
            "(`price_sport_repeated`)."
        )
    )
    price_grosze: int = Field(
        description=(
            "The standard court-hour, in grosze — 12000 is 120 zł. Between "
            "`least` and `most` (`price_out_of_range`, which carries both), and "
            "splitting into whole grosze among the sport's seats "
            "(`price_does_not_split`, which carries `seats`) — so is every band's."
        )
    )
    bands: list[PriceBandRequest] = Field(
        description="Optional hours priced differently. Empty is none."
    )


class PricesRequest(BaseModel):
    """The whole price table, **a full replacement**: a sport left out is no
    longer priced."""

    model_config = ConfigDict(extra="forbid")

    prices: list[SportPriceRequest]


class PriceBandResponse(BaseModel):
    days: BandDays
    from_hour: int
    until_hour: int
    price_grosze: int
    share_grosze: int = Field(
        description="What one player pays of it: the price divided by the seats."
    )


class SportPriceResponse(BaseModel):
    sport: Sport
    seats: int = Field(description="How many players a game of this sport seats.")
    price_grosze: int | None = Field(
        description="The standard court-hour in grosze, or `null` — not priced yet."
    )
    share_grosze: int | None = Field(
        description=(
            "What one player pays of the standard price — the price divided by "
            "the seats, exact to the grosz. `null` beside a `null` price."
        )
    )
    bands: list[PriceBandResponse] = Field(
        description="Weekdays first, then by the hour each opens."
    )

    @classmethod
    def from_domain(
        cls, sport: Sport, prices: SportPrices | None
    ) -> "SportPriceResponse":
        return cls(
            sport=sport,
            seats=seats(sport),
            price_grosze=None if prices is None else prices.grosze,
            share_grosze=None if prices is None else prices.share,
            bands=[]
            if prices is None
            else [
                PriceBandResponse(
                    days=band.days,
                    from_hour=band.opens,
                    until_hour=band.closes,
                    price_grosze=band.grosze,
                    share_grosze=share_of(band.grosze, sport),
                )
                for band in prices.bands
            ],
        )


class PricesResponse(BaseModel):
    prices: list[SportPriceResponse] = Field(
        description=(
            "Every sport the club offers, in the registry's order, priced or not. "
            "**New prices apply to new cards only**: a card already dealt keeps "
            "the price it was dealt with."
        )
    )

    @classmethod
    def of(cls, prices: list[tuple[Sport, SportPrices | None]]) -> "PricesResponse":
        return cls(
            prices=[SportPriceResponse.from_domain(sport, row) for sport, row in prices]
        )


class WayOfWorkingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    way_of_working: WayOfWorking = Field(
        description=(
            "`ONLY_RAKETA` — Raketa sells the club's Raketa hours alone, until "
            "the release lead; `INSTANT` — both sell and a Raketa booking is "
            "final; `ON_REQUEST` — the club confirms each full game within its "
            "time to confirm, and nobody pays until it does."
        )
    )


class OtherClubsCourtsSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    offered: bool = Field(
        description=(
            "*Offer our groups other clubs' courts when ours are full*. Off by default."
        )
    )
    within_km: int = Field(
        description="How far such a court may be, in kilometres — kept while off."
    )


class RaketaSettingsRequest(BaseModel):
    """The settings form — every field on every save, defaults included, since
    the first save is the club **confirming** them. Each number is bounded by
    the domain: `setting_out_of_range` names the field and carries `least` and
    `most`."""

    model_config = ConfigDict(extra="forbid")

    release_lead_days: int = Field(
        description=(
            "Only Raketa: days before a game unsold hours return to the club. "
            "1–13, default 3."
        )
    )
    cut_off_hours: int = Field(
        description=(
            "Hours before a game players may leave free, and a game still short "
            "is called off. 0–72, default 24."
        )
    )
    minimum_notice_hours: int = Field(
        description=(
            "Instant and On request: the latest a Raketa game can book, in hours "
            "before it. 1–48, default 2."
        )
    )
    time_to_confirm_minutes: int = Field(
        description=(
            "On request: minutes the club has to answer a full game. 5–60, "
            "default 30 — never more than the shortest minimum notice."
        )
    )
    other_clubs_courts: OtherClubsCourtsSchema = Field(
        description="The distance is 1–50 km, default 10."
    )
    check_in: bool = Field(description="*We check players in*. Off by default.")
    paused: bool = Field(
        description=(
            "*Pause Raketa bookings*: no new cards on the club's courts; booked "
            "games are played as booked, and cards already dealt keep their "
            "court until their book-by."
        )
    )


class RaketaSettingsResponse(BaseModel):
    """How the club works with Raketa, and every setting — **at its default
    until the club confirms it**, so the form can show what it would save."""

    way_of_working: WayOfWorking | None = Field(
        description="`null` until the club chooses."
    )
    release_lead_days: int
    cut_off_hours: int
    minimum_notice_hours: int
    time_to_confirm_minutes: int
    other_clubs_courts: OtherClubsCourtsSchema
    check_in: bool
    paused: bool

    @classmethod
    def from_domain(cls, club: ClubCourts) -> "RaketaSettingsResponse":
        settings = club.settings
        return cls(
            way_of_working=club.way,
            release_lead_days=settings.release_lead_days,
            cut_off_hours=settings.cut_off_hours,
            minimum_notice_hours=settings.minimum_notice_hours,
            time_to_confirm_minutes=settings.time_to_confirm_minutes,
            other_clubs_courts=OtherClubsCourtsSchema(
                offered=settings.other_clubs_courts.offered,
                within_km=settings.other_clubs_courts.within_km,
            ),
            check_in=settings.check_in,
            paused=club.paused,
        )


class SetupStepSchema(BaseModel):
    step: SetupStep
    state: StepState = Field(
        description=(
            "`DONE`, `TO_DO` or `LOCKED` — waiting on the step it needs: hours "
            "and prices on a court, the settings on a way of working. *Next* is "
            "the first `TO_DO`."
        )
    )


class SetupResponse(BaseModel):
    """The Overview's checklist, shown until the club is live."""

    steps: list[SetupStepSchema] = Field(
        description=(
            "The five, in the Overview's order: `CONNECT_PAYMENTS` (the "
            "provider says the account is ready), `WAY_OF_WORKING`, `COURTS` "
            "(an offered court), `HOURS_AND_PRICES` (an offered court with hours, "
            "and every such court's sport priced) and `SETTINGS` (confirmed)."
        )
    )
    payments: PaymentsStatus = Field(
        description=(
            "Where the club's payments account stands, for the first step's "
            "row: `NOT_STARTED` — *Connect with Stripe* — `NEEDS_DETAILS` — "
            "*Stripe needs more details*, and *Continue with Stripe* — or "
            "`READY`. **Ready can be lost**: the provider may want more later, "
            "and the club is not live again until it has it."
        )
    )
    live: bool = Field(
        description=(
            "Every step is done: the club's courts can reach players' decks. A "
            "paused club is still live."
        )
    )

    @classmethod
    def from_domain(cls, checklist: SetupChecklist) -> "SetupResponse":
        return cls(
            steps=[
                SetupStepSchema(step=step, state=state)
                for step, state in checklist.steps
            ],
            payments=checklist.payments,
            live=checklist.live,
        )

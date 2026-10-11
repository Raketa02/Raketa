"""The Club courts aggregate — event-sourced, one stream per club.

Everything a club offers Raketa and how it sells it (``docs/adr/0189`` §3, §5;
the mechanics §16): its **courts** and the **Raketa hours** each is offered for.

**Born by being used.** ``unwritten`` is a club that has done nothing here yet
— no courts, and nothing to sell — and every write starts from it, so no act
has to spell a birth and no sign-up has to write a stream it does not need.

**The hours a club can sell are never stored here.** They are derived from the
pattern and what else stands against it (``domain/sellable.py``), so the stream
records acts and nothing that a clock or a booking could make stale.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import Collection, Iterable
from uuid import UUID

from app.kernel import Sport, invariant
from app.modules.clubs.domain.club_courts_events import (
    CourtAdded,
    CourtChanged,
    CourtRemoved,
    CourtSwitchedOff,
    CourtSwitchedOn,
    ExceptionAdded,
    ExceptionRemoved,
    PaymentsAccountOpened,
    PaymentsStatusChanged,
    PricesSet,
    RaketaHoursSet,
    RaketaPaused,
    RaketaResumed,
    RaketaSettingsChanged,
    WayOfWorkingChosen,
)
from app.modules.clubs.domain.courts import Court, CourtName
from app.modules.clubs.domain.errors import (
    CourtNameTaken,
    CourtNotFound,
    CourtSportNotOffered,
    ExceptionNotFound,
    WayOfWorkingNotChosen,
)
from app.modules.clubs.domain.hours_exceptions import (
    ClosedHours,
    ExceptionReason,
    HoursException,
)
from app.modules.clubs.domain.payments_account import PaymentsAccount, PaymentsStatus
from app.modules.clubs.domain.prices import PriceBand, SportPrices
from app.modules.clubs.domain.raketa_terms import (
    OtherClubsCourts,
    RaketaSettings,
    WayOfWorking,
)
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class ClubCourts:
    """One club's courts and terms, as its stream leaves them."""

    club_id: UUID
    #: The courts, **in the order they were added** — which is the order the
    #: desk reads its table in and the order a derivation breaks a tie by.
    courts: dict[UUID, Court] = field(default_factory=dict)
    #: The exceptions, in the order they were added. One whose every named
    #: court was deleted closes nothing and is no longer here.
    exceptions: dict[UUID, HoursException] = field(default_factory=dict)
    #: Each priced sport's prices. A sport the club stopped offering may keep a
    #: row here, inert — no court of it can exist — until the next save.
    prices: dict[Sport, SportPrices] = field(default_factory=dict)
    #: How the club works with Raketa — ``None`` until it chooses.
    way: WayOfWorking | None = None
    #: The settings, **at their defaults until the club confirms them**.
    settings: RaketaSettings = field(default_factory=RaketaSettings)
    #: Whether the club has saved its settings at least once.
    settings_confirmed: bool = False
    paused: bool = False
    #: The club's account at the payment provider — ``None`` until the desk
    #: first asks to connect.
    payments: PaymentsAccount | None = None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def unwritten(cls, club_id: UUID) -> "ClubCourts":
        """A club that has done nothing here: no courts and nothing to sell."""

        return cls(club_id=club_id)

    @classmethod
    def from_history(cls, club_id: UUID, events: Iterable[DomainEvent]) -> "ClubCourts":
        club = cls.unwritten(club_id)
        for event in events:
            club._apply(event)
        return club

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # ----------------------------------------------------------------- courts

    def add_court(
        self,
        *,
        court_id: UUID,
        name: CourtName,
        sport: Sport,
        indoor: bool,
        offered_sports: Collection[Sport],
        occurred_at: datetime,
    ) -> Court:
        """Refused when the club offers no such sport, or another of its
        courts has the name."""

        self._refuse_a_sport_not_offered(sport, offered_sports)
        self._refuse_a_taken_name(name, but_for=None)
        self._record_that(
            CourtAdded(
                club_id=self.club_id,
                court_id=court_id,
                name=name.value,
                sport=sport.value,
                indoor=indoor,
                occurred_at=occurred_at,
            )
        )
        return self.courts[court_id]

    def court(self, court_id: UUID) -> Court:
        """The court with this id, or ``court_not_found`` — which is also the
        answer for another club's court, since a desk reaches only its own."""

        found = self.courts.get(court_id)
        if found is None:
            raise CourtNotFound()
        return found

    def selling_courts(self) -> list[Court]:
        """The courts that offer Raketa something: switched on, with Raketa
        hours. Whether their sport is priced is the next question, asked by
        whoever needs it."""

        return [
            court for court in self.courts.values() if court.offered and court.hours
        ]

    def in_court_order(self, court_ids: Collection[UUID]) -> tuple[UUID, ...]:
        """These courts, once each, in the order the club added them."""

        return tuple(court_id for court_id in self.courts if court_id in court_ids)

    def change_court(
        self,
        court_id: UUID,
        *,
        name: CourtName,
        sport: Sport,
        indoor: bool,
        offered: bool,
        offered_sports: Collection[Sport],
        occurred_at: datetime,
    ) -> Court:
        """A full replacement of the court's four facts. The name, sport and
        roof are one event and whether it is offered is another, each recorded
        only when it moved. A new sport must be one the club offers; keeping the
        one it has is allowed even after the club stopped offering it, since
        nothing about the court changed."""

        court = self.court(court_id)
        if sport != court.sport:
            self._refuse_a_sport_not_offered(sport, offered_sports)
        self._refuse_a_taken_name(name, but_for=court_id)
        if (name, sport, indoor) != (court.name, court.sport, court.indoor):
            self._record_that(
                CourtChanged(
                    club_id=self.club_id,
                    court_id=court_id,
                    name=name.value,
                    sport=sport.value,
                    indoor=indoor,
                    occurred_at=occurred_at,
                )
            )
        if offered != court.offered:
            switched = CourtSwitchedOn if offered else CourtSwitchedOff
            self._record_that(
                switched(
                    club_id=self.club_id, court_id=court_id, occurred_at=occurred_at
                )
            )
        return self.courts[court_id]

    def remove_court(self, court_id: UUID, *, occurred_at: datetime) -> None:
        """The desk deletes a court. Whether a booking is ahead of it is asked
        by the use case first, since bookings are not this aggregate's to
        know."""

        self.court(court_id)
        self._record_that(
            CourtRemoved(
                club_id=self.club_id, court_id=court_id, occurred_at=occurred_at
            )
        )

    def set_hours(
        self, court_ids: Collection[UUID], hours: WeeklyHours, *, occurred_at: datetime
    ) -> None:
        """The same Raketa hours on every one of these courts — one court, or
        the courts *Copy to other courts* and *All courts of a sport* reach —
        all or none: an unknown court refuses the whole save. Recorded per
        court, and only where the week moved."""

        courts = [self.court(court_id) for court_id in court_ids]
        for court in courts:
            if court.hours != hours:
                self._record_that(
                    RaketaHoursSet(
                        club_id=self.club_id,
                        court_id=court.id,
                        hours=hours.codes,
                        occurred_at=occurred_at,
                    )
                )

    # ------------------------------------------------------------- exceptions

    def add_exception(
        self, exception: HoursException, *, today: date, occurred_at: datetime
    ) -> HoursException:
        """Close hours without touching the pattern. Whether a booking holds
        one of its hours is asked by the use case first, between
        ``admit_exception`` and this."""

        self.admit_exception(exception, today=today)
        self._record_that(
            ExceptionAdded(
                club_id=self.club_id,
                exception_id=exception.id,
                court_ids=(
                    None
                    if exception.court_ids is None
                    else self.in_court_order(exception.court_ids)
                ),
                first_day=exception.first_day.isoformat(),
                last_day=exception.last_day.isoformat(),
                from_hour=None if exception.hours is None else exception.hours.opens,
                until_hour=None if exception.hours is None else exception.hours.closes,
                reason=exception.reason.value,
                occurred_at=occurred_at,
            )
        )
        return self.exceptions[exception.id]

    def admit_exception(self, exception: HoursException, *, today: date) -> None:
        """Refuse an exception naming a court the club does not have, or
        closing only days already over."""

        for court_id in exception.court_ids or ():
            self.court(court_id)
        exception.refuse_if_over(today=today)

    def remove_exception(self, exception_id: UUID, *, occurred_at: datetime) -> None:
        if exception_id not in self.exceptions:
            raise ExceptionNotFound()
        self._record_that(
            ExceptionRemoved(
                club_id=self.club_id,
                exception_id=exception_id,
                occurred_at=occurred_at,
            )
        )

    def exceptions_not_over(self, *, today: date) -> list[HoursException]:
        """The exceptions the desk's list shows: every one not over yet, by
        its first day, then the hour it closes from (a whole day first), then
        the order they were added."""

        return sorted(
            (
                exception
                for exception in self.exceptions.values()
                if not exception.is_over(today=today)
            ),
            key=lambda exception: (
                exception.first_day,
                0 if exception.hours is None else exception.hours.opens,
            ),
        )

    # ----------------------------------------------------------------- prices

    def set_prices(
        self, table: Iterable[SportPrices], *, occurred_at: datetime
    ) -> None:
        """The whole price table, replaced: a sport absent from it is no longer
        priced. Recorded per sport, in the registry's order, only where its
        prices moved. **A card already dealt keeps its price** (the mechanics
        §16.5) — it was fixed on the card, and nothing here reaches it."""

        saving = {prices.sport: prices for prices in table}
        for sport in Sport:
            now_priced = saving.get(sport)
            if self.prices.get(sport) == now_priced:
                continue
            self._record_that(
                PricesSet(
                    club_id=self.club_id,
                    sport=sport.value,
                    price_grosze=None if now_priced is None else now_priced.grosze,
                    bands=()
                    if now_priced is None
                    else tuple(band.code for band in now_priced.bands),
                    occurred_at=occurred_at,
                )
            )

    def prices_of(
        self, offered_sports: Collection[Sport]
    ) -> list[tuple[Sport, SportPrices | None]]:
        """The price table as the desk reads it: every sport the club offers,
        in the registry's order, priced or not."""

        return [
            (sport, self.prices.get(sport))
            for sport in Sport
            if sport in offered_sports
        ]

    # --------------------------------------------------- the way and settings

    def choose_way(self, way: WayOfWorking, *, occurred_at: datetime) -> None:
        """One way for the whole club, changeable later; choosing the one it
        has records nothing."""

        if way is self.way:
            return
        self._record_that(
            WayOfWorkingChosen(
                club_id=self.club_id, way=way.value, occurred_at=occurred_at
            )
        )

    def save_settings(
        self, settings: RaketaSettings, *, paused: bool, occurred_at: datetime
    ) -> None:
        """The club saves its settings form. **The first save is the club
        confirming them**, so it records even when every value is a default;
        after that, only a save that moved something does. Pausing and resuming
        are acts of their own. Refused until a way of working is chosen."""

        if self.way is None:
            raise WayOfWorkingNotChosen()
        if settings != self.settings or not self.settings_confirmed:
            self._record_that(
                RaketaSettingsChanged(
                    club_id=self.club_id,
                    release_lead_days=settings.release_lead_days,
                    cut_off_hours=settings.cut_off_hours,
                    minimum_notice_hours=settings.minimum_notice_hours,
                    time_to_confirm_minutes=settings.time_to_confirm_minutes,
                    other_clubs_courts=settings.other_clubs_courts.offered,
                    other_clubs_within_km=settings.other_clubs_courts.within_km,
                    occurred_at=occurred_at,
                )
            )
        if paused != self.paused:
            toggled = RaketaPaused if paused else RaketaResumed
            self._record_that(toggled(club_id=self.club_id, occurred_at=occurred_at))

    # --------------------------------------------------------------- payments

    @property
    def payments_status(self) -> PaymentsStatus:
        """Where the club's payments account stands — not started while there
        is none."""

        if self.payments is None:
            return PaymentsStatus.NOT_STARTED
        return self.payments.status

    def open_payments_account(self, account_id: str, *, occurred_at: datetime) -> None:
        """Raketa opened the club's account at the provider. **Once**: a club
        with an account continues it, and opening a second is a bug in the
        caller."""

        invariant(self.payments is None, "a club opens one payments account")
        self._record_that(
            PaymentsAccountOpened(
                club_id=self.club_id, account_id=account_id, occurred_at=occurred_at
            )
        )

    def record_payments_status(
        self, status: PaymentsStatus, *, occurred_at: datetime
    ) -> None:
        """The account as the provider says it stands now. Recorded only when
        it moved, so the same reading twice — a notice and the link's own read,
        or a notice delivered again — records it once."""

        account = invariant(self.payments, "a status for a club with no account")
        if status is account.status:
            return
        self._record_that(
            PaymentsStatusChanged(
                club_id=self.club_id, status=status.value, occurred_at=occurred_at
            )
        )

    def _refuse_a_sport_not_offered(
        self, sport: Sport, offered_sports: Collection[Sport]
    ) -> None:
        if sport not in offered_sports:
            raise CourtSportNotOffered()

    def _refuse_a_taken_name(self, name: CourtName, *, but_for: UUID | None) -> None:
        if any(
            court.name.folded == name.folded
            for court in self.courts.values()
            if court.id != but_for
        ):
            raise CourtNameTaken()

    # -------------------------------------------------------------------- fold

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, CourtAdded):
            self.courts[event.court_id] = Court(
                id=event.court_id,
                name=CourtName(event.name),
                sport=Sport(event.sport),
                indoor=event.indoor,
            )
        elif isinstance(event, CourtChanged):
            self.courts[event.court_id] = replace(
                self.courts[event.court_id],
                name=CourtName(event.name),
                sport=Sport(event.sport),
                indoor=event.indoor,
            )
        elif isinstance(event, (CourtSwitchedOff, CourtSwitchedOn)):
            self.courts[event.court_id] = replace(
                self.courts[event.court_id],
                offered=isinstance(event, CourtSwitchedOn),
            )
        elif isinstance(event, CourtRemoved):
            del self.courts[event.court_id]
            self.exceptions = {
                exception.id: kept
                for exception in self.exceptions.values()
                if (kept := exception.without({event.court_id})) is not None
            }
        elif isinstance(event, ExceptionAdded):
            self.exceptions[event.exception_id] = HoursException(
                id=event.exception_id,
                court_ids=event.court_ids,
                first_day=date.fromisoformat(event.first_day),
                last_day=date.fromisoformat(event.last_day),
                hours=ClosedHours.of(event.from_hour, event.until_hour),
                reason=ExceptionReason(event.reason),
            )
        elif isinstance(event, ExceptionRemoved):
            del self.exceptions[event.exception_id]
        elif isinstance(event, WayOfWorkingChosen):
            self.way = WayOfWorking(event.way)
        elif isinstance(event, RaketaSettingsChanged):
            self.settings = RaketaSettings(
                release_lead_days=event.release_lead_days,
                cut_off_hours=event.cut_off_hours,
                minimum_notice_hours=event.minimum_notice_hours,
                time_to_confirm_minutes=event.time_to_confirm_minutes,
                other_clubs_courts=OtherClubsCourts(
                    offered=event.other_clubs_courts,
                    within_km=event.other_clubs_within_km,
                ),
            )
            self.settings_confirmed = True
        elif isinstance(event, (RaketaPaused, RaketaResumed)):
            self.paused = isinstance(event, RaketaPaused)
        elif isinstance(event, PricesSet):
            sport = Sport(event.sport)
            if event.price_grosze is None:
                self.prices.pop(sport, None)
            else:
                self.prices[sport] = SportPrices(
                    sport=sport,
                    grosze=event.price_grosze,
                    bands=tuple(PriceBand.from_code(code) for code in event.bands),
                )
        elif isinstance(event, RaketaHoursSet):
            self.courts[event.court_id] = replace(
                self.courts[event.court_id],
                hours=WeeklyHours.from_codes(event.hours),
            )
        elif isinstance(event, PaymentsAccountOpened):
            self.payments = PaymentsAccount(
                account_id=event.account_id, status=PaymentsStatus.NOT_STARTED
            )
        elif isinstance(event, PaymentsStatusChanged):
            self.payments = replace(
                invariant(self.payments, "a status recorded before its account"),
                status=PaymentsStatus(event.status),
            )
        else:
            raise TypeError(f"Unsupported club courts event {event!r}")
        self.version += 1

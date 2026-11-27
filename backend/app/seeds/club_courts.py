"""The clubs' courts: what each seeded club offers Rakieta, and how (#535).

**A seeded court is a court a desk added** (``docs/adr/0029``): every write
here is the use case the club website's Courts & prices and Rakieta settings
run — ``AddCourt``, ``SetRakietaHours``, ``AddException``, ``SetPrices``,
``SaveRakietaSettings`` — so each club's **Club courts** stream is the one a
desk would have left, and nothing opens a table.

**The eight are arranged across every state the club website draws**
(the screens B2–B5, the mechanics §16):

- **every club works Only Rakieta**, the one way (#670; ``docs/adr/0196`` §1):
  Ogrody 33, Bonarka Arena and Nowa Huta Squash worked Instant, and Kazimierz
  Padel and Prądnik Tennis On request, until both were removed (#669, #670).
  **Each keeps a release lead that leaves its seeded games fillable**: the
  clubs whose games the run fills — Bonarka Arena, where her group plays,
  Kazimierz Padel, where her next week's game is, and Ogrody 33, whose played
  history is filled two days ahead — release their hours **a day ahead**, the
  shortest lead, as Prądnik Tennis does, so every hour from tomorrow is
  Rakieta's to sell and a card dealt there outlives a day of developing
  against it; Centrum Ruchu keeps two days, and Nowa Huta Squash and Zabłocie
  Sport the default three;
- **courts per sport**, indoor and outdoor, a weekly pattern of Rakieta hours on
  weekday evenings and weekend mornings — where the protagonists' own weeks
  are — **one exception** each, and **price bands** (dearer evenings or
  weekends) on every priced sport. **At least one live club has indoor and
  outdoor courts of one sport at the same Rakieta hours** (#671, Q122), so a
  move that keeps the kind, a weather cancel and a card's kind can all be
  walked, and the run refuses a seed with none: Bonarka Arena's padel Court 4
  is outdoor beside Courts 1–3 indoors — a padel card there promises neither
  kind, her game books Court 1 and may move to 2 or 3, never 4 — and Ogrody
  33's tennis has Kort centralny outdoors beside Court 4 indoors, where a game
  books the outdoor court first and may move indoors;
- **Zabłocie Sport is paused**: live, selling what its cards would need, and
  dealing nothing new;
- **Wisła Park is not live**: it added courts with hours, closed a few days
  for resurfacing and confirmed its settings, and never priced its courts —
  half its checklist done, two steps of four — and it is **half connected**:
  it went to the provider's pages and the provider says *Stripe needs more
  details*.
- **Every other club's payments are ready** (#537): each desk asked for the
  link through ``ConnectPayments``, the use case *Connect with Stripe* runs,
  and a fake provider finished its onboarding the moment the link was made —
  so the read that follows the link found the account ready, as a laptop's does.
  Wisła Park's is told apart by ``HeedPaymentsAccount``, the use case the
  provider's notice runs. **A club with no account yet is connected on any
  run**, so a database seeded before payments existed goes live on the next.
  **On the Stripe sandbox** (#712, ``money.py``) a ready club is connected to
  the account a person onboarded for it, and reads ready because Stripe says
  so; Wisła Park opens a new account and stays as Stripe opened it, *not
  started*.

**The exception is placed from the run's own clock**, a few days ahead, so a
fresh run always shows one on the list; and **re-running adds nothing to a
club whose desk has already set anything**, which leaves a walk's edits as the
developer left them.

**The run then reads what it wrote, through the port the proposer will read**:
every live club must have hours for sale in the next fourteen days, and a
declaration that cannot sell any fails the seed by name rather than leaving a
deck with nothing to deal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from functools import partial
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_club_account_repository,
    build_club_courts_repository,
    build_club_repository,
    build_court_bookings,
    build_domain_event_store,
    build_event_publisher,
    build_mail_queue,
    build_onboarding_pages,
    build_sellable_court_hours,
    build_unit_of_work,
)
from app.core.config import Settings
from app.kernel import Instant, Sport
from app.modules.clubs.application.club_courts import AddCourt, SetRakietaHours
from app.modules.clubs.application.commands import (
    AddCourtCommand,
    AddExceptionCommand,
    ConnectPaymentsCommand,
    PriceBandInput,
    SaveRakietaSettingsCommand,
    SetPricesCommand,
    SetRakietaHoursCommand,
    SportPriceInput,
)
from app.modules.clubs.application.hours_exceptions import AddException
from app.modules.clubs.application.payments_account import (
    ConnectPayments,
    HeedPaymentsAccount,
)
from app.modules.clubs.application.prices import SetPrices
from app.modules.clubs.application.rakieta_settings import SaveRakietaSettings
from app.modules.clubs.domain.court_hours import local_day
from app.modules.clubs.domain.payments_account import PaymentsStatus
from app.modules.clubs.domain.prices import BandDays, PriceBand
from app.modules.clubs.domain.ports import ClubAccountRepository
from app.modules.clubs.domain.rakieta_terms import OtherClubsCourts, RakietaSettings
from app.modules.clubs.domain.setup import checklist_of
from app.modules.payments.domain.provider import ClubAccountStatus
from app.modules.player_profile.domain.weekly_hours import WEEKEND_DAYS
from app.modules.users.domain.value_objects import Email
from app.seeds.clock import FixedClock
from app.seeds.clubs import SEED_CLUBS, SeedClub, SeededClubs, desk_email
from app.seeds.money import THE_FAKE, SeedMoney

#: How far ahead the fortnight the self-check reads is — a deck's own horizon.
HORIZON: Final = timedelta(days=14)

_WEEKDAYS: Final = (1, 2, 3, 4, 5)
_WEEKEND: Final = tuple(sorted(WEEKEND_DAYS))


class ClubCourtsRefused(RuntimeError):
    """A seeded club that should be live sells nothing in the next fortnight."""


def _week(days: tuple[int, ...], first: int, until: int) -> tuple[tuple[int, int], ...]:
    """Every hour from ``first`` until ``until`` on each of ``days``."""

    return tuple((day, hour) for day in days for hour in range(first, until))


#: Weekday evenings and weekend mornings, the club's busiest Rakieta hours.
EVENINGS_AND_WEEKENDS: Final = _week(_WEEKDAYS, 17, 22) + _week(_WEEKEND, 9, 15)


@final
@dataclass(frozen=True, slots=True)
class SeedCourt:
    name: str
    sport: Sport
    indoor: bool = True


@final
@dataclass(frozen=True, slots=True)
class SeedPrice:
    """A sport's standard court-hour and one band, in grosze — whole złoty,
    which always split among the seats."""

    sport: Sport
    grosze: int
    band: PriceBand | None = None


@final
@dataclass(frozen=True, slots=True)
class SeedException:
    """``days_ahead`` of the run's own day, for ``days`` days; on one court
    (by its place in the club's list) or every court; the whole day or between
    two hours."""

    reason: str
    days_ahead: int
    days: int = 1
    court: int | None = None
    hours: tuple[int, int] | None = None


@final
@dataclass(frozen=True, slots=True)
class SeedClubCourts:
    club: str
    courts: tuple[SeedCourt, ...]
    week: tuple[tuple[int, int], ...]
    prices: tuple[SeedPrice, ...] = ()
    exception: SeedException | None = None
    #: The settings the desk confirms — the defaults but for the release
    #: lead, **a day ahead** unless a club says otherwise: the shortest, so the
    #: most of its hours stay Rakieta's to sell.
    settings: RakietaSettings = field(
        default_factory=lambda: RakietaSettings(release_lead_days=1)
    )
    paused: bool = False
    #: What the provider says of its account once the desk has been to the
    #: provider's pages — ready, unless it stopped half way.
    payments: ClubAccountStatus = ClubAccountStatus.READY


def _padel(*numbers: int) -> tuple[SeedCourt, ...]:
    return tuple(SeedCourt(f"Court {number}", Sport.PADEL) for number in numbers)


SEED_CLUB_COURTS: Final[tuple[SeedClubCourts, ...]] = (
    SeedClubCourts(
        club="Ogrody 33",
        courts=(
            *_padel(1, 2),
            SeedCourt("Kort centralny", Sport.TENNIS, indoor=False),
            SeedCourt("Court 4", Sport.TENNIS),
        ),
        week=EVENINGS_AND_WEEKENDS,
        prices=(
            SeedPrice(
                Sport.PADEL, 120_00, PriceBand(BandDays.WEEKDAYS, 17, 22, 140_00)
            ),
            SeedPrice(Sport.TENNIS, 80_00, PriceBand(BandDays.WEEKEND, 7, 23, 100_00)),
        ),
        exception=SeedException("Repair", days_ahead=5, court=1, hours=(9, 12)),
    ),
    SeedClubCourts(
        club="Centrum Ruchu",
        courts=(
            *_padel(1, 2),
            SeedCourt("Court 3", Sport.SQUASH),
            SeedCourt("Court 4", Sport.SQUASH),
        ),
        week=_week(_WEEKDAYS, 7, 10) + _week(_WEEKDAYS, 17, 22) + _week((6,), 9, 14),
        prices=(
            SeedPrice(
                Sport.PADEL, 110_00, PriceBand(BandDays.WEEKDAYS, 17, 22, 130_00)
            ),
            SeedPrice(Sport.SQUASH, 60_00, PriceBand(BandDays.WEEKDAYS, 17, 22, 70_00)),
        ),
        exception=SeedException("Tournament", days_ahead=9, days=2),
        settings=RakietaSettings(release_lead_days=2),
    ),
    SeedClubCourts(
        club="Kazimierz Padel",
        courts=_padel(1, 2, 3),
        week=_week((2, 3, 4, 5, 6, 7), 16, 23),
        prices=(
            SeedPrice(Sport.PADEL, 100_00, PriceBand(BandDays.WEEKEND, 7, 23, 120_00)),
        ),
        exception=SeedException("Holiday", days_ahead=12),
        # A day ahead, the seed's default: the protagonist's game booked here
        # (``bookings.py``) is at an hour it still sells.
    ),
    SeedClubCourts(
        club="Bonarka Arena",
        courts=(
            *_padel(1, 2, 3),
            # Outdoor beside three indoor courts: a card here promises neither
            # kind, and a game on Court 1 never moves here (#671, Q122).
            SeedCourt("Court 4", Sport.PADEL, indoor=False),
            SeedCourt("Court 5", Sport.TENNIS, indoor=False),
            SeedCourt("Court 6", Sport.TENNIS, indoor=False),
            SeedCourt("Court 7", Sport.BADMINTON),
            SeedCourt("Court 8", Sport.BADMINTON),
        ),
        week=_week(_WEEKDAYS, 17, 22) + _week(_WEEKEND, 9, 17),
        prices=(
            SeedPrice(
                Sport.PADEL, 140_00, PriceBand(BandDays.WEEKDAYS, 17, 22, 160_00)
            ),
            SeedPrice(Sport.TENNIS, 90_00, PriceBand(BandDays.WEEKEND, 7, 23, 110_00)),
            SeedPrice(
                Sport.BADMINTON, 60_00, PriceBand(BandDays.WEEKEND, 7, 23, 72_00)
            ),
        ),
        exception=SeedException("Repair", days_ahead=3, court=4),
    ),
    SeedClubCourts(
        club="Zabłocie Sport",
        courts=(
            SeedCourt("Court 1", Sport.SQUASH),
            SeedCourt("Court 2", Sport.SQUASH),
            SeedCourt("Court 3", Sport.BADMINTON),
        ),
        week=_week(_WEEKDAYS, 17, 22) + _week((6,), 9, 13),
        prices=(
            SeedPrice(Sport.SQUASH, 60_00, PriceBand(BandDays.WEEKDAYS, 17, 22, 70_00)),
            SeedPrice(
                Sport.BADMINTON, 48_00, PriceBand(BandDays.WEEKEND, 7, 23, 56_00)
            ),
        ),
        exception=SeedException("Tournament", days_ahead=6),
        settings=RakietaSettings(),
        paused=True,
    ),
    SeedClubCourts(
        club="Prądnik Tennis",
        courts=(
            SeedCourt("Court 1", Sport.TENNIS, indoor=False),
            SeedCourt("Court 2", Sport.TENNIS, indoor=False),
            SeedCourt("Court 3", Sport.TENNIS),
            SeedCourt("Court 4", Sport.SQUASH),
        ),
        week=_week(_WEEKDAYS, 7, 10)
        + _week(_WEEKDAYS, 16, 22)
        + _week(_WEEKEND, 8, 14),
        prices=(
            SeedPrice(Sport.TENNIS, 70_00, PriceBand(BandDays.WEEKDAYS, 16, 22, 90_00)),
            SeedPrice(Sport.SQUASH, 56_00, PriceBand(BandDays.WEEKDAYS, 16, 22, 64_00)),
        ),
        exception=SeedException("Repair", days_ahead=4, court=1, hours=(16, 19)),
        settings=RakietaSettings(
            release_lead_days=1,
            other_clubs_courts=OtherClubsCourts(offered=True, within_km=8),
        ),
    ),
    SeedClubCourts(
        club="Wisła Park",
        courts=(
            SeedCourt("Court 1", Sport.TENNIS, indoor=False),
            SeedCourt("Court 2", Sport.TENNIS, indoor=False),
        ),
        week=EVENINGS_AND_WEEKENDS,
        exception=SeedException("Resurfacing", days_ahead=7, days=3),
        payments=ClubAccountStatus.NEEDS_DETAILS,
    ),
    SeedClubCourts(
        club="Nowa Huta Squash",
        courts=(
            SeedCourt("Court 1", Sport.SQUASH),
            SeedCourt("Court 2", Sport.SQUASH),
            SeedCourt("Court 3", Sport.SQUASH),
            SeedCourt("Court 4", Sport.BADMINTON),
        ),
        week=_week(_WEEKDAYS, 16, 22) + _week(_WEEKEND, 10, 16),
        prices=(
            SeedPrice(Sport.SQUASH, 50_00, PriceBand(BandDays.WEEKDAYS, 16, 22, 60_00)),
            SeedPrice(
                Sport.BADMINTON, 40_00, PriceBand(BandDays.WEEKEND, 7, 23, 48_00)
            ),
        ),
        exception=SeedException("Repair", days_ahead=2, court=2, hours=(18, 19)),
        # The default three days: nothing is seeded here to fill.
        settings=RakietaSettings(),
    ),
)

# Every seeded club is declared once, and every declaration names a seeded club.
assert sorted(entry.club for entry in SEED_CLUB_COURTS) == sorted(
    club.name for club in SEED_CLUBS
), "every seeded club is declared once in SEED_CLUB_COURTS"


def declared_ready() -> tuple[str, ...]:
    """The clubs whose payments the seed declares ready — each on a sandbox
    account a person onboarded, when the run is on Stripe (#712)."""

    return tuple(
        entry.club
        for entry in SEED_CLUB_COURTS
        if entry.payments is ClubAccountStatus.READY
    )


@final
@dataclass(frozen=True, slots=True)
class SeededClubCourts:
    declared: SeedClubCourts
    #: Whether this run set the club up, or found its desk had already.
    set_up_by_this_run: bool
    live: bool
    paused: bool
    #: Where the club's payments account stands.
    payments: PaymentsStatus
    #: Court hours for sale in the next fortnight, as the port reads them.
    for_sale: int


@final
@dataclass(frozen=True, slots=True)
class SeededCourts:
    clubs: tuple[SeededClubCourts, ...]


async def write_the_club_courts(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    clubs: SeededClubs,
    money: SeedMoney = THE_FAKE,
) -> SeededCourts:
    """Set every seeded club up as declared, unless its desk already has.

    One session for the layer, and each act commits through its own unit of
    work, as the club website's would. Its desks walk ``money``'s pages.
    """

    signed_up = {entry.club.name for entry in clubs.clubs}
    clock = FixedClock(at=now)
    seeded: list[SeededClubCourts] = []
    async with session_factory() as session:
        event_store = build_domain_event_store(session)
        events = build_event_publisher(session)
        accounts = build_club_account_repository(
            session, event_store=event_store, events=events
        )
        club_repository = build_club_repository(
            session, event_store=event_store, events=events
        )
        courts = build_club_courts_repository(
            session, event_store=event_store, events=events
        )
        uow = build_unit_of_work(session)
        bookings = build_court_bookings(session)
        # The run's own provider's pages: on the fake, a fake that finishes a
        # club's onboarding when told to; on the sandbox, the accounts a person
        # onboarded (``money.py``).
        provider_pages = money.pages()
        pages = build_onboarding_pages(settings)
        connect = ConnectPayments(
            clubs=club_repository,
            courts=courts,
            payments_accounts=provider_pages.accounts,
            pages=pages,
            uow=uow,
            clock=clock,
        )
        heed = HeedPaymentsAccount(
            clubs=club_repository,
            club_accounts=accounts,
            courts=courts,
            payments_accounts=provider_pages.accounts,
            mail=build_mail_queue(session),
            pages=pages,
            clock=clock,
        )

        for declared in SEED_CLUB_COURTS:
            if declared.club not in signed_up:
                continue
            club_id = await _club_id(accounts, declared.club)
            untouched = (await courts.load(club_id)).version == 0
            if untouched:
                await _set_up(
                    declared,
                    club_id,
                    now=now,
                    add_court=AddCourt(
                        clubs=club_repository, courts=courts, uow=uow, clock=clock
                    ),
                    set_hours=SetRakietaHours(courts=courts, uow=uow, clock=clock),
                    add_exception=AddException(
                        courts=courts, bookings=bookings, uow=uow, clock=clock
                    ),
                    set_prices=SetPrices(
                        clubs=club_repository, courts=courts, uow=uow, clock=clock
                    ),
                    save=SaveRakietaSettings(courts=courts, uow=uow, clock=clock),
                )
            if (await courts.load(club_id)).payments is None:
                # The desk's *Connect with Stripe*: the link, and the provider's
                # pages — finished in one visit for a club that is ready, and
                # left needing more for one that is not, which the provider's
                # notice then says.
                noticed = await provider_pages.walk(
                    club_id,
                    as_far_as=declared.payments,
                    connect=partial(
                        connect.execute,
                        ConnectPaymentsCommand(
                            club_id=club_id,
                            email=desk_email(_seed_club(declared.club)),
                        ),
                    ),
                )
                if noticed is not None:
                    await heed.execute(noticed)
                    await uow.commit()
            club = await courts.load(club_id)
            offers = await build_sellable_court_hours(session).between(
                [club_id], start=now, end=now + HORIZON, now=now
            )
            offer = offers.get(club_id)
            seeded.append(
                SeededClubCourts(
                    declared=declared,
                    set_up_by_this_run=untouched,
                    live=checklist_of(club).live,
                    paused=club.paused,
                    payments=club.payments_status,
                    for_sale=0 if offer is None else len(offer.hours),
                )
            )

    _refuse_a_live_club_with_nothing_for_sale(seeded)
    _refuse_a_seed_with_no_club_of_both_kinds(seeded)
    return SeededCourts(clubs=tuple(seeded))


def _seed_club(name: str) -> SeedClub:
    return next(club for club in SEED_CLUBS if club.name == name)


async def _club_id(accounts: ClubAccountRepository, name: str) -> UUID:
    account = await accounts.get_by_email(Email(desk_email(_seed_club(name))))
    if account is None:
        raise ClubCourtsRefused(f"{name} has no desk to set its courts up with")
    return account.club_id


async def _set_up(
    declared: SeedClubCourts,
    club_id: UUID,
    *,
    now: Instant,
    add_court: AddCourt,
    set_hours: SetRakietaHours,
    add_exception: AddException,
    set_prices: SetPrices,
    save: SaveRakietaSettings,
) -> None:
    """The desk's own order: the courts and their hours, the exception, the
    prices — for a club that got that far — and the settings."""

    court_ids = [
        (
            await add_court.execute(
                AddCourtCommand(
                    club_id=club_id,
                    name=court.name,
                    sport=court.sport,
                    indoor=court.indoor,
                )
            )
        ).id
        for court in declared.courts
    ]
    await set_hours.execute(
        SetRakietaHoursCommand(
            club_id=club_id, court_ids=tuple(court_ids), hours=declared.week
        )
    )
    if declared.exception is not None:
        exception = declared.exception
        first = local_day(now) + timedelta(days=exception.days_ahead)
        await add_exception.execute(
            AddExceptionCommand(
                club_id=club_id,
                court_ids=(
                    None if exception.court is None else (court_ids[exception.court],)
                ),
                first_day=first,
                last_day=first + timedelta(days=exception.days - 1),
                from_hour=None if exception.hours is None else exception.hours[0],
                until_hour=None if exception.hours is None else exception.hours[1],
                reason=exception.reason,
            )
        )
    if declared.prices:
        await set_prices.execute(
            SetPricesCommand(
                club_id=club_id,
                prices=tuple(
                    SportPriceInput(
                        sport=price.sport,
                        price_grosze=price.grosze,
                        bands=()
                        if price.band is None
                        else (
                            PriceBandInput(
                                days=price.band.days,
                                from_hour=price.band.opens,
                                until_hour=price.band.closes,
                                price_grosze=price.band.grosze,
                            ),
                        ),
                    )
                    for price in declared.prices
                ),
            )
        )
    settings = declared.settings
    await save.execute(
        SaveRakietaSettingsCommand(
            club_id=club_id,
            release_lead_days=settings.release_lead_days,
            cut_off_hours=settings.cut_off_hours,
            other_clubs_courts=settings.other_clubs_courts.offered,
            other_clubs_within_km=settings.other_clubs_courts.within_km,
            paused=declared.paused,
        )
    )


def _refuse_a_live_club_with_nothing_for_sale(
    seeded: list[SeededClubCourts],
) -> None:
    for entry in seeded:
        if entry.declared.prices and not entry.live:
            raise ClubCourtsRefused(
                f"{entry.declared.club} was set up to be live and its checklist "
                "says it is not"
            )
        if entry.live and entry.for_sale == 0:
            raise ClubCourtsRefused(
                f"{entry.declared.club} is live and has no court hour for sale in "
                "the next fourteen days"
            )


def sports_of_both_kinds(declared: SeedClubCourts) -> tuple[Sport, ...]:
    """The sports this club offers on indoor and on outdoor courts alike — at
    the same Rakieta hours, since a seeded club's week is every court's."""

    return tuple(
        sport
        for sport in Sport
        if {court.indoor for court in declared.courts if court.sport is sport}
        == {True, False}
    )


def _refuse_a_seed_with_no_club_of_both_kinds(
    seeded: list[SeededClubCourts],
) -> None:
    """A move that keeps the kind, a weather cancel and a card's kind are
    walked at a live club with both kinds of one sport (#671, Q122)."""

    if not any(entry.live and sports_of_both_kinds(entry.declared) for entry in seeded):
        raise ClubCourtsRefused(
            "no live club has indoor and outdoor courts of one sport at the "
            "same Rakieta hours — a move that keeps the kind cannot be walked"
        )


#: The payments step as the Overview words it.
_PAYMENTS_WORDS: Final = {
    PaymentsStatus.NOT_STARTED: "not started",
    PaymentsStatus.NEEDS_DETAILS: "need more details",
    PaymentsStatus.READY: "ready",
}


def club_courts_lines(seeded: SeededCourts) -> list[str]:
    """The report's section: every club, its release lead, and what it has for
    sale."""

    new = sum(1 for entry in seeded.clubs if entry.set_up_by_this_run)
    lines = [
        f"Club courts — {len(seeded.clubs)} clubs, {new} set up by this run. Each "
        "desk's Courts & prices, Rakieta settings and Overview draw from these:"
    ]
    for entry in seeded.clubs:
        declared = entry.declared
        state = (
            "paused"
            if entry.live and entry.paused
            else "live"
            if entry.live
            else "not live (half its checklist)"
        )
        payments = _PAYMENTS_WORDS[entry.payments]
        both = sports_of_both_kinds(declared)
        kinds = (
            f" · indoor and outdoor {', '.join(s.value.lower() for s in both)}"
            if both
            else ""
        )
        lines.append(
            f"  {declared.club} · "
            f"releases its hours {declared.settings.release_lead_days} day(s) ahead · "
            f"{len(declared.courts)} courts{kinds} · {state} · payments {payments} · "
            f"{entry.for_sale} court hours for sale in the next 14 days"
        )
    return lines

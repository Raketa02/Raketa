"""Ogrody 33 full at one hour, and other clubs serving it then (#746;
``docs/adr/0202`` §7).

**An official group plays at another club only at an hour its own club has no
free court**, and the club's switch is on by default — so the seed makes Ogrody
33, where both official groups play, **full on the first Saturday at 10:00 from
two days out**: its desk closes every court for that hour for its own *Club
tournament*, through ``AddException``, the use case the club website's Hours &
exceptions run (``docs/adr/0029``). Bonarka Arena and Centrum Ruchu sell padel
then, within the 10 km Ogrody 33 never changed: *Ogrody 33 Club* is offered them
at 10:00, each marked *Ogrody 33 is full at 10:00*, and only Ogrody 33 at 9:00
and 11:00, where it still has a court.

**A closure rather than bookings**, because the court source reads a court that
is not free whatever made it so, and the crowd that books (``bookings.py``) is
spoken for: two more games in one week would move the games per week every
layer after it keeps out of the way of.

**Before the games still filling**, so no layer that deals or books meets a card
at an hour the desk then closes. **On any run**: a store seeded before #746 gets
the hour on its next run; a run that finds the tournament on that Saturday adds
nothing; and a run on a later day closes a later Saturday, as a later run books
later hours.

**Proved by reading it** (``assert_the_full_hour``): her Post a game sheet in
*Ogrody 33 Club* for that morning, read through ``ReadPostingSlot`` once the
outbox is drained, must offer another club at 10:00, marked, and no other club
at an hour Ogrody 33 still has a court — or the run fails by name.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_club_account_repository,
    build_club_courts_repository,
    build_court_bookings,
    build_domain_event_store,
    build_event_publisher,
    build_read_posting_slot,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport
from app.modules.clubs.application.commands import AddExceptionCommand
from app.modules.clubs.application.hours_exceptions import AddException
from app.modules.clubs.domain.court_hours import CLUB_ZONE, hour_start, local_day
from app.modules.proposals.application.commands import (
    PostingCommand,
    ReadPostingSlotCommand,
)
from app.modules.proposals.domain.overlap import DayRange
from app.modules.proposals.domain.post import Who
from app.modules.users.domain.value_objects import Email
from app.seeds.administrators import THE_CLUB
from app.seeds.catalog import THE_POPULATED_PLAYER
from app.seeds.clock import FixedClock
from app.seeds.clubs import desk_email
from app.seeds.official_groups import SEED_OFFICIAL_GROUPS, SeededOfficialGroups
from app.seeds.screens import ScreenIsEmpty

#: Why the desk closed the hour — the words its exceptions list shows.
REASON: Final = "Club tournament"
#: Saturday (ISO weekday 6), 10:00 — the hour the friends grilling found
#: Ogrody 33 full at.
SATURDAY: Final = 6
HOUR: Final = 10
#: How far ahead the Saturday is, at least: past a day of developing against
#: it, and inside every seeded club's release lead.
DAYS_OUT: Final = 2

#: The official group whose sheet proves it, and the protagonist reading it.
GROUP: Final = SEED_OFFICIAL_GROUPS[0]
SPORT: Final = Sport.PADEL


@final
@dataclass(frozen=True, slots=True)
class SeededFullHour:
    start: Instant
    #: Whether this run closed it, or found it closed already.
    closed_by_this_run: bool
    #: *Ogrody 33 Club* — ``None`` when it was not created.
    group_id: UUID | None


def the_saturday(now: Instant) -> date:
    """The first Saturday at least ``DAYS_OUT`` days after the run's day."""

    first = local_day(now) + timedelta(days=DAYS_OUT)
    return first + timedelta(days=(SATURDAY - first.isoweekday()) % 7)


async def make_ogrody_33_full(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    now: Instant,
    official_groups: SeededOfficialGroups,
) -> SeededFullHour:
    """Close every court at Ogrody 33 for its tournament at that Saturday's
    10:00, unless an earlier run did."""

    day = the_saturday(now)
    start = hour_start(day, HOUR)
    clock = FixedClock(at=now)
    async with session_factory() as session:
        event_store = build_domain_event_store(session)
        events = build_event_publisher(session)
        account = await build_club_account_repository(
            session, event_store=event_store, events=events
        ).get_by_email(Email(desk_email(THE_CLUB)))
        if account is None:
            raise RuntimeError(
                f"{THE_CLUB.name} has not signed up — the clubs run first"
            )
        courts = build_club_courts_repository(
            session, event_store=event_store, events=events
        )
        club = await courts.load(account.club_id)
        closed_by_this_run = not any(
            exception.reason.value == REASON
            and exception.first_day <= day <= exception.last_day
            for exception in club.exceptions.values()
        )
        if closed_by_this_run:
            await AddException(
                courts=courts,
                bookings=build_court_bookings(session),
                uow=build_unit_of_work(session),
                clock=clock,
            ).execute(
                AddExceptionCommand(
                    club_id=account.club_id,
                    court_ids=None,
                    first_day=day,
                    last_day=day,
                    from_hour=HOUR,
                    until_hour=HOUR + 1,
                    reason=REASON,
                )
            )
    group_id = next(
        (
            seeded.group_id
            for seeded in official_groups.groups
            if seeded.group.name == GROUP.name
        ),
        None,
    )
    return SeededFullHour(
        start=start, closed_by_this_run=closed_by_this_run, group_id=group_id
    )


async def assert_the_full_hour(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    full: SeededFullHour,
) -> str:
    """*Ogrody 33 Club is offered other clubs only where Ogrody 33 is full*
    (``docs/adr/0202`` §7): her Post a game sheet for the Saturday morning lists
    another club at 10:00, marked as offered because Ogrody 33 is full, and no
    other club at an hour Ogrody 33 has a court."""

    when = f"{full.start.astimezone(CLUB_ZONE):%a %d %b %H:%M}"
    where = f"Post a game · {THE_POPULATED_PLAYER.slug} · {GROUP.name} · {when}"
    if full.group_id is None:
        return f"{where}: not read — {GROUP.name} was not created"
    async with session_factory() as session:
        user = await build_user_repository(session).get_by_email(
            THE_POPULATED_PLAYER.email
        )
        if user is None:
            raise ScreenIsEmpty(f"{where}: {THE_POPULATED_PLAYER.slug} is missing")
        slot = await build_read_posting_slot(
            session, settings=settings, clock=FixedClock(at=now)
        ).execute(
            ReadPostingSlotCommand(
                posting=PostingCommand(
                    player_id=user.id,
                    pool_id=full.group_id,
                    sport=SPORT,
                    kind=SearchMode.COMPETITIVE,
                    who=Who.ANYONE,
                ),
                day=local_day(full.start),
                day_range=DayRange.MORNING,
            )
        )
    at_home = {court.hour.start for court in slot.free_courts if court.home}
    elsewhere = [court for court in slot.free_courts if not court.home]
    then = [court for court in elsewhere if court.hour.start == full.start]
    if full.start in at_home or not then:
        raise ScreenIsEmpty(
            f"{where} offers no other club at the hour {THE_CLUB.name} is full"
        )
    if not all(court.home_club_full for court in elsewhere) or any(
        court.hour.start in at_home for court in elsewhere
    ):
        raise ScreenIsEmpty(
            f"{where} offers another club at an hour {THE_CLUB.name} has a court, "
            "or one not marked as offered because it is full"
        )
    clubs = sorted(slot.club_names.get(court.hour.club_id, "?") for court in then)
    return (
        f"{where}: {THE_CLUB.name} full, {', '.join(clubs)} offered then, marked; "
        f"only {THE_CLUB.name} at its other {len(at_home)} morning hour(s)"
    )


def full_hour_lines(seeded: SeededFullHour) -> list[str]:
    """The report's section: the hour Ogrody 33 is full, and why."""

    state = "closed" if seeded.closed_by_this_run else "already closed"
    return [
        f"{THE_CLUB.name} full at "
        f"{seeded.start.astimezone(CLUB_ZONE):%a %d %b %H:%M} — every court closed "
        f"for its {REASON.lower()} ({state}): its official groups are offered "
        "other clubs within its distance then, and only it at every hour it has "
        "a court."
    ]

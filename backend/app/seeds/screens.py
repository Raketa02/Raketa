"""What the seed promises about the screens, proved by reading them.

**The second of the seed's two lists, and it is not symmetric with the first.**
The layers hold the *declarations* — what each one writes. This holds the
*assertions*, and every one of them is an outcome of a **real read path
executed as the protagonist or her club**: the group deck is dealt, Fill in is
read, the posting grid is drawn, the club's Bookings day is listed. Nothing here
is asserted about a number a layer chose; a check computed from what was written
could only ever pass.

**The matcher's battery is gone** (#578). It read the pool search, the deck, the
radar and the eleven relationships off the protagonist's own searches, and its
fixture — a layer that sent and answered challenges — went with the challenges.
Her record is asserted in ``booked_history.py`` (``assert_her_history``), off
the past booked games that make it.

**Half a gate, said out loud.** None of this runs in CI: it needs a database with
the seed in it.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_read_club_bookings,
    build_read_fill_in,
    build_read_group_deck,
    build_read_posting_grid,
)
from app.core.config import Settings
from app.kernel import Instant
from app.modules.clubs.domain.court_hours import local_day, local_hour
from app.modules.player_profile.domain.weekly_hours import DAY_RANGES
from app.modules.proposals.application.commands import (
    PostingCommand,
    ReadFillInCommand,
    ReadGroupDeckCommand,
    ReadPostingGridCommand,
)
from app.modules.proposals.domain.club_bookings import ClubFilter
from app.modules.proposals.domain.overlap import DayRange
from app.modules.proposals.domain.post import Who
from app.modules.proposals.domain.posting_grid import WEEKS, GridCell
from app.seeds.catalog import THE_POPULATED_PLAYER
from app.seeds.clock import FixedClock
from app.seeds.proposals import (
    GAMES_CLUB,
    GAMES_GROUP,
    GAMES_KIND,
    GAMES_SPORT,
    games_club_id,
    her_games_group,
)


class ScreenIsEmpty(RuntimeError):
    """A screen the cohort promised is one this database cannot draw.

    A ``RuntimeError`` for ``SeedFailed``'s reason — it is a refusal to hand a
    developer a fixture whose promise is a lie, not a bad argument a caller might
    catch. It is raised rather than warned for the same reason the whole file
    exists: a warning in a make target scrolls past, and the fixture then rots
    silently.
    """


async def assert_the_group_deck(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> str:
    """*The protagonist's group deck deals her something* (#539; the screens
    Part D).

    Read through ``ReadGroupDeck`` — the Games tab's own read, filters and all —
    as her, in the games group and the segment the proposals layer deals in. It
    is asked **beside** the battery rather than inside it: the cohort's own
    acceptance test builds a world without proposals, and a group deck is a
    claim about this layer's fixture. A deck that deals nothing — her intent
    moved, a ceiling under every share, a week at her cap, the picks expired or
    unfit — fails the run by name with what the read said around it.
    """

    async with session_factory() as session:
        found = await her_games_group(session)
        if found is None:
            raise ScreenIsEmpty(
                f"the group deck · {THE_POPULATED_PLAYER.slug} has no "
                f"{GAMES_GROUP} to read — the proposals layer runs first"
            )
        her, group_id = found
        deck = await build_read_group_deck(
            session, settings=settings, clock=FixedClock(at=now)
        ).execute(
            ReadGroupDeckCommand(
                player_id=her, pool_id=group_id, sport=GAMES_SPORT, kind=GAMES_KIND
            )
        )
    where = (
        f"group deck · {THE_POPULATED_PLAYER.slug} · {GAMES_GROUP} · "
        f"{GAMES_SPORT.value.lower()} {GAMES_KIND.value.lower()}"
    )
    if not deck.cards:
        raise ScreenIsEmpty(
            f"{where} deals nothing: segments "
            f"{[(segment.kind.value, segment.count) for segment in deck.segments]}, "
            f"{deck.games_per_week} games a week, capped weeks "
            f"{[week.starts_on.isoformat() for week in deck.capped_weeks]}"
        )
    return (
        f"{where}: {len(deck.cards)} card(s), {deck.games_badge} with somebody In, "
        f"the first {deck.cards[0].open_seats_after_your_yes} seat(s) from filling"
    )


async def assert_the_fill_in(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    expects_after_the_cut_off: bool,
) -> str:
    """*The protagonist's Fill in offers her seats to fill* (#545; the screens
    A3.1, Part D).

    Read through ``ReadFillIn`` — the tab's own read — as her, in the games
    group. A board with no seat that *fills by* the cut-off, or — when the
    rescues layer seeded one — none *offered until the start*, fails the run by
    name: her intent moved, her week no longer covers the hour, a fit gone, a
    game booked over it.
    """

    async with session_factory() as session:
        found = await her_games_group(session)
        if found is None:
            raise ScreenIsEmpty(
                f"Fill in · {THE_POPULATED_PLAYER.slug} has no {GAMES_GROUP} to "
                f"read — the proposals layer runs first"
            )
        her, group_id = found
        board = await build_read_fill_in(
            session, settings=settings, clock=FixedClock(at=now)
        ).execute(ReadFillInCommand(player_id=her, pool_id=group_id, sport=GAMES_SPORT))
    where = f"Fill in · {THE_POPULATED_PLAYER.slug} · {GAMES_GROUP}"
    before = sum(1 for row in board.seats_to_fill if row.fills_by_the_cut_off)
    after = len(board.seats_to_fill) - before
    if before == 0 or (expects_after_the_cut_off and after == 0):
        raise ScreenIsEmpty(
            f"{where} offers {before} seat(s) that fill by the cut-off and {after} "
            f"offered until the start"
        )
    return (
        f"{where}: {board.badge} seat(s) to fill — {before} by the cut-off, "
        f"{after} until the start"
    )


async def assert_the_club_bookings(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    now: Instant,
    on: Instant,
) -> str:
    """*Her club's Bookings page lists the games booked there* (#547; the
    screens B4, Part D).

    Read through ``ReadClubBookings`` — the page's own read — as the club, on
    the day of her first seeded booked game. An empty day fails the run by
    name: the bookings layer seated nothing, or the club's day no longer reads
    its own bookings.
    """

    async with session_factory() as session:
        club_id = await games_club_id(session)
        day = await build_read_club_bookings(session, clock=FixedClock(at=now)).execute(
            club_id, day=local_day(on), chosen=ClubFilter.ALL
        )
    where = f"Bookings · {GAMES_CLUB.name} · {day.day.isoformat()}"
    if not day.rows:
        raise ScreenIsEmpty(f"{where} lists no Raketa booking")
    paid = sum(len(row.takings.paid) for row in day.rows)
    return f"{where}: {len(day.rows)} booking(s), {paid} share(s) paid"


#: The looks of a posting grid cell the server decides (the screens A5.2) —
#: *your pick* is the client's own.
POSTING_LOOKS: tuple[str, ...] = (
    "dead",
    "few · no court",
    "enough · no court",
    "court, thin",
    "hot",
    "outside your hours",
    "past",
    "happening here",
)


def looks_of(cell: GridCell) -> frozenset[str]:
    """Which of the grid's looks a cell takes, as the client draws them from
    its values."""

    if cell.past:
        return frozenset({"past"})
    looks: set[str] = set()
    if cell.fits_free == 0:
        looks.add("dead")
    elif not cell.court_free:
        looks.add("enough · no court" if cell.full_game else "few · no court")
    else:
        looks.add("hot" if cell.full_game else "court, thin")
    if cell.outside_your_hours:
        looks.add("outside your hours")
    if cell.happening:
        looks.add("happening here")
    return frozenset(looks)


async def assert_the_posting_grid(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    now: Instant,
) -> str:
    """*The protagonist's posting grid draws every look* (#546; the screens
    A5.2, Part D).

    Read through ``ReadPostingGrid`` — the WHEN grid's own read — as her, in the
    games group, over **both weeks, for anybody and for women**: the controls
    as the screen opens them, and one tap on *Who*. Every look the server
    decides must be drawn somewhere among the four — *earlier today* only once
    the morning is over — or the run fails by name with the looks missing:
    the cohort's weeks moved, a club's hours moved, or her intent did.
    """

    async with session_factory() as session:
        found = await her_games_group(session)
        if found is None:
            raise ScreenIsEmpty(
                f"the posting grid · {THE_POPULATED_PLAYER.slug} has no "
                f"{GAMES_GROUP} to read — the proposals layer runs first"
            )
        her, group_id = found
        reader = build_read_posting_grid(session, clock=FixedClock(at=now))
        drawn: set[str] = set()
        for who in (Who.ANYONE, Who.WOMEN):
            for week in WEEKS:
                read = await reader.execute(
                    ReadPostingGridCommand(
                        posting=PostingCommand(
                            player_id=her,
                            pool_id=group_id,
                            sport=GAMES_SPORT,
                            kind=GAMES_KIND,
                            who=who,
                        ),
                        week=week,
                    )
                )
                for cell in read.cells:
                    drawn |= looks_of(cell)
    where = f"posting grid · {THE_POPULATED_PLAYER.slug} · {GAMES_GROUP}"
    # Earlier today is drawn once the morning's last hour has begun.
    morning_over = local_hour(now) >= DAY_RANGES[DayRange.MORNING.value][-1]
    expected = [look for look in POSTING_LOOKS if look != "past" or morning_over]
    missing = [look for look in expected if look not in drawn]
    if missing:
        raise ScreenIsEmpty(
            f"{where} draws no {', no '.join(missing)} over two weeks for anybody "
            f"or for women"
        )
    return f"{where}: every look over two weeks for anybody and for women" + (
        "" if morning_over else " (earlier today: not yet, the morning is not over)"
    )

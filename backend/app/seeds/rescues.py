"""Rescues she fits: seats to fill (#545; the screens A3.1, Part D).

**A rescue is a booked game that lost a player** (``docs/adr/0029``): each is
made as her booked games are — ``MakeProposal`` at an hour Bonarka Arena sells
padel, filled by four ``SayYes`` from *Padel po pracy*'s crowd, never her — and
then one of the four leaves through ``LeaveTheGame``, the use case the phone's
*Leave the game* runs. The seat is open, and **she is offered it**: the hour is
one of her own week's, she has no game then, her week has room, and she fits
the three still on it. Nothing here opens a table.

**Two states the board draws**:

- **fills by the cut-off** — a game more than a day past Bonarka's cut-off,
  left now: the leaver's hold let go (#637), the seat open until the
  cut-off, when the game is off unless it is taken. Always seedable: her week
  has an hour that far ahead in every fortnight;
- **offered until the start** — a game inside the cut-off, booked as if
  earlier and left now: the seat open until the hour, the leaver refunded only
  when somebody takes it. No game fills later than its release time, a day
  before it at Bonarka (#670; ``docs/adr/0196`` §1), so this one filled an hour
  before its release time and the cut-off job ran at its cut-off, as the API's
  would have then (#637). **Seedable only while an hour of her week Bonarka
  sells falls inside its cut-off** — her week is Tuesday to Friday evenings and
  Saturday until three, so a run from Saturday afternoon to Monday evening, or
  late on a weekday evening, finds none — and otherwise skipped by name.

**Out of the other layers' way**: neither hour is one of her booked games',
answered picks' or waiting game's, and the four on each are crowd members with
**no game that week yet and no yes at that hour** — so the fill withdraws no
seeded yes and pauses nobody's week.

**Re-running seeds nothing twice**: a rescue of either state already on her
board is left as it is, and a later run on a later day seeds later hours.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_booked_games,
    build_club_terms,
    build_leave_the_game,
    build_players_in_play,
    build_pools,
    build_proposal_directory,
    build_read_fill_in,
)
from app.core.config import Settings
from app.kernel import Instant, hours, shifted
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.clubs.domain.raketa_terms import before_any_deadline
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.player_profile.domain.weekly_hours import free_for_the_hour
from app.modules.proposals.application.commands import (
    LeaveTheGameCommand,
    ReadFillInCommand,
)
from app.modules.proposals.domain.deck import GAME_LENGTH, week_of, week_window
from app.seeds.bookings import (
    NotEnoughToBook,
    SeededBookings,
    all_say_yes,
    padel_hours_on_sale,
    the_cut_off_if_it_passed,
    when_it_fills,
)
from app.seeds.clock import FixedClock
from app.seeds.money import THE_FAKE, SeedMoney
from app.seeds.proposals import (
    GAMES_CLUB,
    GAMES_SPORT,
    SeededProposals,
    games_club_id,
    her_games_group,
)

#: The two states, in the order they are seeded.
FILLS_BY_THE_CUT_OFF: Final = "fills by the cut-off"
OFFERED_UNTIL_THE_START: Final = "offered until the start"

#: How far past the cut-off the first state's hour is, so its seat outlives a
#: day of developing against it.
LEAD_PAST_THE_CUT_OFF: Final = timedelta(days=1)


@final
@dataclass(frozen=True, slots=True)
class SeededRescue:
    state: str
    start: Instant
    #: Whether this run made it, or found it on her board already.
    made: bool


@final
@dataclass(frozen=True, slots=True)
class SeededRescues:
    rescues: tuple[SeededRescue, ...]
    #: Why *offered until the start* is not seeded this run — ``None`` when it
    #: is.
    skipped: str | None = None


async def seed_the_rescues(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    seeded: SeededProposals,
    bookings: SeededBookings,
    money: SeedMoney = THE_FAKE,
) -> SeededRescues:
    """Her two rescues — **after her booked games**, whose hours, crowd and
    weeks it reads and keeps out of the way of."""

    clock = FixedClock(at=now)
    provider = money.provider()
    async with session_factory() as session:
        found = await her_games_group(session)
        if found is None:
            raise NotEnoughToBook("the proposals layer has not gathered her group")
        her, group_id = found
        club_id = await games_club_id(session)
        board = await build_read_fill_in(
            session, settings=settings, clock=clock
        ).execute(ReadFillInCommand(player_id=her, pool_id=group_id, sport=GAMES_SPORT))
        on_board = {
            FILLS_BY_THE_CUT_OFF: next(
                (row for row in board.seats_to_fill if row.fills_by_the_cut_off), None
            ),
            OFFERED_UNTIL_THE_START: next(
                (row for row in board.seats_to_fill if not row.fills_by_the_cut_off),
                None,
            ),
        }
        terms = (await build_club_terms(session).of([club_id], now=now)).get(club_id)
        if terms is None:
            raise NotEnoughToBook(f"{GAMES_CLUB.name} sells nothing at {now}")
        cut_off = shifted(now, hours(terms.cut_off_hours))
        week = (await build_players_in_play(session).of([her], sport=GAMES_SPORT))[
            her
        ].week
        taken = [
            *bookings.starts,
            *(pick.start for pick in seeded.picks),
            *(row.game.start for row in board.seats_to_fill),
        ]
        # As Bonarka sold them before any deadline: an hour inside its release
        # lead is filled as if earlier, when it was on sale.
        hers = [
            hour
            for hour in await padel_hours_on_sale(
                session, club_id, now=now, on_sale_at=before_any_deadline(now)
            )
            if free_for_the_hour(week, start=hour.start, zone=CLUB_ZONE)
            and not any(abs(hour.start - other) < GAME_LENGTH for other in taken)
        ]
        wanted = {
            FILLS_BY_THE_CUT_OFF: next(
                (
                    hour
                    for hour in hers
                    if hour.start >= cut_off + LEAD_PAST_THE_CUT_OFF
                ),
                None,
            ),
            OFFERED_UNTIL_THE_START: next(
                (hour for hour in hers if hour.start < cut_off), None
            ),
        }

        rescues: list[SeededRescue] = []
        skipped: str | None = None
        used: set[UUID] = set()
        for state in (FILLS_BY_THE_CUT_OFF, OFFERED_UNTIL_THE_START):
            existing = on_board[state]
            if existing is not None:
                rescues.append(SeededRescue(state, existing.game.start, made=False))
                continue
            hour = wanted[state]
            if hour is None:
                if state == FILLS_BY_THE_CUT_OFF:
                    raise NotEnoughToBook(
                        f"{GAMES_CLUB.name} sells no padel hour of her week a day "
                        f"past its cut-off from "
                        f"{now.astimezone(CLUB_ZONE):%a %d %b %H:%M}"
                    )
                skipped = (
                    f"no hour of her week that {GAMES_CLUB.name} still sells, clear "
                    f"of her games, falls inside its {terms.cut_off_hours}-hour "
                    f"cut-off from {now.astimezone(CLUB_ZONE):%a %H:%M}"
                )
                continue
            four = await _four_free_at(
                session, group_id, her, hour.start, excluding=used, now=now
            )
            used.update(four)
            await _a_game_left_by_one(
                session,
                settings=settings,
                clock=clock,
                provider=provider,
                pool_id=group_id,
                club_id=club_id,
                start=hour.start,
                four=four,
                filled_at=when_it_fills(hour, now=now),
            )
            rescues.append(SeededRescue(state, hour.start, made=True))
    return SeededRescues(rescues=tuple(rescues), skipped=skipped)


async def _four_free_at(
    session: AsyncSession,
    group_id: UUID,
    her: UUID,
    start: Instant,
    *,
    excluding: set[UUID],
    now: Instant,
) -> tuple[UUID, ...]:
    """Four of the crowd, in the order they joined, with no game in the
    hour's week and no yes at the hour — so booking them moves nothing another
    layer seeded."""

    pools = build_pools(session)
    pool = await pools.find(group_id)
    if pool is None:
        raise NotEnoughToBook("her games group has no pool")
    booked = build_booked_games(session)
    directory = build_proposal_directory(session)
    week_start, week_end = week_window([week_of(start)])
    four: list[UUID] = []
    for member in await pools.members_of(pool):
        if member == her or member in excluding:
            continue
        if await booked.starts_of(member, start=week_start, end=week_end):
            continue
        yeses = await directory.live_yeses_of(member, now=now)
        if any(abs(yes.start - start) < GAME_LENGTH for yes in yeses):
            continue
        four.append(member)
        if len(four) == 4:
            return tuple(four)
    raise NotEnoughToBook(
        f"the crowd has no four free of games the week of "
        f"{start.astimezone(CLUB_ZONE):%a %d %b %H:%M} to leave a seat for her"
    )


async def _a_game_left_by_one(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: FixedClock,
    provider: PaymentProvider,
    pool_id: UUID,
    club_id: UUID,
    start: Instant,
    four: Sequence[UUID],
    filled_at: Instant,
) -> None:
    """The four's game booked at ``filled_at``, and the last of them leaving it
    now, on ``clock``."""

    answer = await all_say_yes(
        session,
        settings=settings,
        clock=FixedClock(at=filled_at),
        provider=provider,
        pool_id=pool_id,
        club_id=club_id,
        start=start,
        players=tuple(four),
    )
    if answer is None or answer.booked is None:
        raise NotEnoughToBook(
            f"the rescue at {start.astimezone(CLUB_ZONE):%a %d %b %H:%M} filled and "
            f"did not book: {answer!r}"
        )
    await the_cut_off_if_it_passed(
        session,
        settings=settings,
        booking_id=answer.booked.booking_id,
        filled_at=filled_at,
        now=clock.at,
    )
    await build_leave_the_game(session, clock=clock, settings=settings).execute(
        LeaveTheGameCommand(booking_id=answer.booked.booking_id, player_id=four[-1])
    )


def rescue_lines(seeded: SeededRescues) -> list[str]:
    """The report's section: the rescues on her board."""

    lines = [f"Rescues she fits at {GAMES_CLUB.name}, one seat open on each:"]
    for rescue in seeded.rescues:
        state = "left open" if rescue.made else "already on her board"
        lines.append(
            f"  {rescue.start.astimezone(CLUB_ZONE):%a %d %b %H:%M} · "
            f"{rescue.state} · {state}"
        )
    if seeded.skipped is not None:
        lines.append(f"  {OFFERED_UNTIL_THE_START}: not seeded — {seeded.skipped}")
    return lines

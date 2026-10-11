"""Her own post (#546; the screens A5, Part D).

**A post is a member's yes on a court hour they picked** (``docs/adr/0029``):
hers is made by ``PostAGame``, the use case *Post — you're In* runs, as her, in
*Padel po pracy* — for anybody, at the engine's own Level range — at the first
padel hour Bonarka Arena sells in her week from ``LEAD`` out that has somebody
who fits her free, **clear of every game and yes the layers above seeded**: her
booked games, her answered picks, her game waiting for the club and her
rescues. It is dealt to her best fits free then as a **Challenge** — *Ola
challenged you* in their decks — and sits in her *You're In*. Nothing here
opens a table.

**The posting grid's every look needs no more people**: the cohort's weeks
already draw them across her two weeks — Monday afternoon, the one third of a
day none of her group's clubs sells padel, is *enough · no court* for anybody
and *few · no court* for women — which ``screens.py`` asserts on every run
rather than this layer arranging.

**Re-running posts nothing twice**: a post of hers still live in the group is
left as it is, and a later run on a later day posts a later hour once that one
has gone.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_post_a_game,
    build_proposal_directory,
    build_proposal_repository,
    build_read_posting,
)
from app.kernel import Instant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.player_profile.domain.weekly_hours import free_for_the_hour
from app.modules.proposals.application.commands import (
    PostAGameCommand,
    PostingCommand,
)
from app.modules.proposals.domain.deck import GAME_LENGTH
from app.modules.proposals.domain.overlap import DayRange
from app.modules.proposals.domain.post import Who
from app.modules.proposals.domain.posting_grid import WEEKS
from app.modules.proposals.domain.proposal import Origin
from app.seeds.bookings import NotEnoughToBook, SeededBookings
from app.seeds.clock import FixedClock
from app.seeds.proposals import (
    GAMES_CLUB,
    GAMES_KIND,
    GAMES_SPORT,
    SeededProposals,
    games_club_id,
    her_games_group,
)
from app.seeds.rescues import SeededRescues

#: How far ahead her post is, so it outlives a day of developing against it.
LEAD: Final = timedelta(days=2)


@final
@dataclass(frozen=True, slots=True)
class SeededPost:
    proposal_id: UUID
    start: Instant
    #: How many of her best fits it was dealt to — ``None`` for one found.
    dealt_to: int | None
    #: Whether this run posted it, or found it live already.
    made: bool


class NothingToPost(NotEnoughToBook):
    """No hour of her week at the club has somebody who fits her free, clear of
    the games and yeses the layers above seeded."""


def her_posting(her: UUID, group_id: UUID) -> PostingCommand:
    """The controls as the screen opens them: her sport, her kind, anybody, the
    engine's own Level range."""

    return PostingCommand(
        player_id=her,
        pool_id=group_id,
        sport=GAMES_SPORT,
        kind=GAMES_KIND,
        who=Who.ANYONE,
    )


async def post_her_game(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    now: Instant,
    seeded: SeededProposals,
    bookings: SeededBookings,
    rescues: SeededRescues,
) -> SeededPost:
    """Her post — **after her rescues**, the last layer that writes a game she
    is on, whose hours it keeps out of the way of."""

    clock = FixedClock(at=now)
    async with session_factory() as session:
        found = await her_games_group(session)
        if found is None:
            raise NothingToPost("the proposals layer has not gathered her group")
        her, group_id = found
        live = await _her_live_post(session, her, group_id, now)
        if live is not None:
            return live
        club_id = await games_club_id(session)
        read = await build_read_posting(session).read(
            her_posting(her, group_id), now=now
        )
        taken = [
            *bookings.starts,
            *(pick.start for pick in seeded.picks),
            *(rescue.start for rescue in rescues.rescues),
        ]
        hour = next(
            (
                court.hour
                for week in WEEKS
                for day in read.grid.days(week)
                for range_ in DayRange
                for court in read.grid.free_courts(day, range_)
                if court.hour.club_id == club_id
                and court.fits_free > 0
                and court.hour.start >= now + LEAD
                and free_for_the_hour(
                    read.poster.week, start=court.hour.start, zone=CLUB_ZONE
                )
                and not any(
                    abs(court.hour.start - other) < GAME_LENGTH for other in taken
                )
            ),
            None,
        )
        if hour is None:
            raise NothingToPost(
                f"{GAMES_CLUB.name} sells no padel hour of her week from "
                f"{LEAD.days} days out with somebody who fits her free, clear of "
                f"her games — from {now.astimezone(CLUB_ZONE):%a %d %b %H:%M}"
            )
        posted = await build_post_a_game(session, clock=clock).execute(
            PostAGameCommand(
                posting=her_posting(her, group_id),
                club_id=club_id,
                start=hour.start,
            )
        )
    return SeededPost(
        proposal_id=posted.proposal_id,
        start=hour.start,
        dealt_to=posted.dealt_to,
        made=True,
    )


async def _her_live_post(
    session: AsyncSession, her: UUID, group_id: UUID, now: Instant
) -> SeededPost | None:
    proposals = build_proposal_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    for yes in await build_proposal_directory(session).live_yeses_of(her, now=now):
        if yes.pool_id != group_id:
            continue
        proposal = await proposals.load(yes.proposal_id)
        if (
            proposal is not None
            and proposal.origin is Origin.POST
            and proposal.poster_id == her
        ):
            return SeededPost(
                proposal_id=proposal.proposal_id,
                start=proposal.start,
                dealt_to=None,
                made=False,
            )
    return None


def post_lines(seeded: SeededPost) -> list[str]:
    """The report's section: her post."""

    state = (
        f"posted, dealt to {seeded.dealt_to} of her best fits"
        if seeded.made
        else "already live"
    )
    return [
        f"Her post at {GAMES_CLUB.name}: "
        f"{seeded.start.astimezone(CLUB_ZONE):%a %d %b %H:%M} · {state}"
    ]

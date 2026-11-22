"""**Posting a game** (#546; the mechanics §9; the screens A5).

A member picks a court and an hour from a heatmap of their best fits, and the
post is dealt to those fits as a **Challenge**. Three steps share one reading:

- **the grid** (``ReadPostingGrid``) — a week of 7 days × 3 ranges, each cell's
  number the best fits free together with the poster at its best hour that has
  a free court, and what is around it (``domain/posting_grid.py``);
- **a cell's sheet** (``ReadPostingSlot``) — the fits free then, best fit
  first; the free courts in its range, home club first, each with its own
  count; and **already happening here**: rescues the poster fits first, then
  posts still filling they could join, either of which they can take instead
  of posting a second game (Q79, Q93);
- **Post — you're In** (``PostAGame``) — the poster's yes: a Proposal with
  origin *post*, who it is for stored on it, dealt as up to three versions to
  the best fits free at that hour (``versions_of_a_post``) — after three guards
  in the order the button says them: a saved method (with a live yes to
  spare), at most two live posts, and the poster's games per week for that
  week. And, past the button's three: no game of theirs at the hour, and
  somebody who fits free then — a cell nobody fits cannot be picked.

**The reading is the proposer's own** (``ReadMembers``): the pool's members
with their Level, week, gender, intent, Games & money, booked games and live
yeses; the pair rule over everybody once; the court hours the pool's clubs sell
— so the grid's number is what the post would be dealt to, and the post is
dealt what the proposer would deal. **Who it is for** — *Who* and the Level
range, narrowed from the engine's own window and never widened — is checked
before anything else is read about anybody.

**A read is recorded nowhere**; the post is one transaction, the dealer's
(``MakeProposal``), which reads the court hour off the club again, so a club
that stopped selling between the sheet and the button refuses the post.
"""

from __future__ import annotations

import asyncio
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TypeVar, final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import BalanceRules
from app.kernel import Clock, Instant, Sport, instant
from app.modules.clubs.domain.court_hours import DAY_OPENS, hour_start, local_day
from app.modules.proposals.application.friends import with_the_readers_friends
from app.modules.proposals.application.commands import (
    MakeProposalCommand,
    PostAGameCommand,
    PostingCommand,
    ReadPostingGridCommand,
    ReadPostingSlotCommand,
)
from app.modules.proposals.application.guards import Guards
from app.modules.proposals.application.making import MakeProposal
from app.modules.proposals.application.members import ReadMembers
from app.modules.proposals.application.rescues import RescueOffers, SeatToFill
from app.modules.proposals.domain.deck import (
    CardForecast,
    Sides,
    challenger_of,
    hour_taken,
    week_of,
)
from app.modules.proposals.domain.errors import (
    CourtHourNotForSale,
    GamesPerWeekBooked,
    LivePostsExhausted,
    NobodyFitsThen,
    NotRatedInTheSport,
    PoolNotFound,
    WhoLeavesYouOut,
    YouPlayThen,
)
from app.modules.proposals.domain.home import BookedGame
from app.modules.proposals.domain.limits import LIVE_POSTS
from app.modules.proposals.domain.overlap import DayRange
from app.modules.proposals.domain.pool import Pool
from app.modules.proposals.domain.ports import (
    BalanceForecasts,
    ClubDistances,
    ClubNames,
    CourtHours,
    DeckPeople,
    ReaderRelations,
    DeckPerson,
    PlayedWith,
    PlayerFit,
    PlayersTags,
    Pools,
    ProposalDirectory,
    ProposalRepository,
    WherePoolsPlay,
)
from app.modules.proposals.domain.post import LevelRange, PostedFor
from app.modules.player_profile.domain.social_tags import SocialTag
from app.modules.player_profile.domain.weekly_hours import DAYS_IN_THE_GRID
from app.modules.proposals.domain.posting_grid import (
    WEEKS,
    FreeCourt,
    GridCell,
    PostingGrid,
    open_to_join,
    range_of,
)
from app.modules.proposals.domain.proposal import Origin, Proposal
from app.modules.proposals.domain.rescues import (
    fills_by_the_cut_off,
    rescue_deadline,
)
from app.modules.proposals.domain.proposer import (
    Member,
    admitted,
    capped_weeks_of,
    may_play,
    versions_of_a_post,
)

#: How many days the grid's two weeks span, from today.
_FORTNIGHT = timedelta(days=len(WEEKS) * DAYS_IN_THE_GRID)


# --------------------------------------------------------------------------- #
# The reading every step shares
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class PostingRead:
    """One poster's posting at one instant: who it is for, their best fits and
    the courts, and the games already happening that they could join."""

    pool: Pool
    sport: Sport
    kind: SearchMode
    posted_for: PostedFor
    #: The engine's own window for the kind around the poster's Level — the
    #: bounds the range may be narrowed inside.
    window: LevelRange
    poster: Member
    #: The pool's members, the poster among them, in the pool's order.
    members: tuple[Member, ...]
    #: Every pair among them, and the people In on the posts below, that may
    #: not share a court in the kind.
    unfit: frozenset[frozenset[UUID]]
    grid: PostingGrid
    #: Booked games with a seat offered to the poster, in the sport and kind.
    rescues: tuple[BookedGame, ...]
    #: Somebody else's posts still filling the poster could join.
    posts: tuple[Proposal, ...]
    read_at: Instant

    @property
    def open_seats(self) -> int:
        """The seats besides the poster: three in doubles, one in singles."""

        return self.grid.open_seats


@final
class ReadPosting:
    def __init__(
        self,
        *,
        pools: Pools,
        where: WherePoolsPlay,
        court_hours: CourtHours,
        members: ReadMembers,
        fit: PlayerFit,
        directory: ProposalDirectory,
        proposals: ProposalRepository,
        offers: RescueOffers,
    ) -> None:
        self._pools = pools
        self._where = where
        self._court_hours = court_hours
        self._members = members
        self._fit = fit
        self._directory = directory
        self._proposals = proposals
        self._offers = offers

    async def read(self, command: PostingCommand, *, now: Instant) -> PostingRead:
        poster, sport, kind = command.player_id, command.sport, command.kind
        pool = await self._pools.find(command.pool_id)
        # A stranger learns nothing about a group's games: one code for a pool
        # that does not exist and one they are not in.
        if pool is None or not await self._pools.members_among(pool, [poster]):
            raise PoolNotFound()
        command.who.refuse_unless_offered_in(sport)
        window = await self._fit.level_window(poster, sport=sport, kind=kind, at=now)
        if window is None:
            raise NotRatedInTheSport(sport=sport.value)
        posted_for = PostedFor(
            who=command.who,
            levels=window.narrowed_to(low=command.level_low, high=command.level_high),
        )
        clubs = await self._where.of(pool, now=now)
        if clubs is None:
            raise PoolNotFound()

        member_ids = await self._pools.members_of(pool)
        members = await self._members.of(member_ids, sport=sport, now=now)
        by_id = {member.player_id: member for member in members}
        mine = by_id[poster]
        if not posted_for.includes_the_poster(
            gender=mine.gender, preference=mine.preference
        ):
            raise WhoLeavesYouOut()

        candidates = [
            proposal
            for proposal in await self._filling(pool, now)
            if proposal.origin is Origin.POST
            and proposal.sport is sport
            and proposal.kind is kind
            and poster not in proposal.yeses
        ]
        unfit = await self._fit.unfit_pairs(
            sorted(
                {
                    *member_ids,
                    *(player for proposal in candidates for player in proposal.yeses),
                },
                key=str,
            ),
            sport=sport,
            kind=kind,
            at=now,
        )
        fits = [
            member
            for member in members
            if member.player_id != poster
            and admitted(posted_for, member)
            and frozenset((poster, member.player_id)) not in unfit
        ]
        genders = {member.player_id: member.gender for member in members}
        posts = tuple(
            proposal
            for proposal in candidates
            if open_to_join(proposal, mine, unfit=unfit, genders=genders, now=now)
        )
        rescues = tuple(
            game
            for game in await self._offers.offered_to_one(
                await self._offers.in_pool(pool.id, sport=sport, now=now),
                poster,
                sport=sport,
                now=now,
            )
            if game.kind is kind
        )
        hours = await self._court_hours.on_sale(
            clubs.home_first,
            start=now,
            end=hour_start(local_day(now) + _FORTNIGHT, DAY_OPENS),
            now=now,
        )
        return PostingRead(
            pool=pool,
            sport=sport,
            kind=kind,
            posted_for=posted_for,
            window=window,
            poster=mine,
            members=tuple(members),
            unfit=unfit,
            grid=PostingGrid(
                poster=mine,
                fits=fits,
                who=posted_for.who,
                kind=kind,
                sport=sport,
                hours=hours,
                clubs=clubs,
                happening=[
                    *(game.start for game in rescues),
                    *(post.start for post in posts),
                ],
                now=now,
            ),
            rescues=rescues,
            posts=posts,
            read_at=now,
        )

    async def _filling(self, pool: Pool, now: Instant) -> list[Proposal]:
        filling: list[Proposal] = []
        for proposal_id in await self._directory.filling_in(pool.id, now=now):
            proposal = await self._proposals.load(proposal_id)
            if proposal is not None:
                filling.append(proposal)
        return filling


# --------------------------------------------------------------------------- #
# The grid
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class PostingWeek:
    read: PostingRead
    week: int
    #: Twenty-one cells, day by day and, within a day, morning first.
    cells: tuple[GridCell, ...]


@final
class ReadPostingGrid:
    def __init__(self, *, posting: ReadPosting, clock: Clock) -> None:
        self._posting = posting
        self._clock = clock

    async def execute(self, command: ReadPostingGridCommand) -> PostingWeek:
        read = await self._posting.read(command.posting, now=instant(self._clock.now()))
        return PostingWeek(
            read=read, week=command.week, cells=read.grid.week(command.week)
        )


# --------------------------------------------------------------------------- #
# A cell's sheet
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class SlotFit:
    """One of the poster's best fits free then, and how even a game of the two
    of them is forecast — the sheet's *2,75 · 93*."""

    player_id: UUID
    forecast: CardForecast | None


@final
@dataclass(frozen=True, slots=True)
class PostToJoin:
    """Somebody else's post still filling that the poster could join."""

    proposal: Proposal
    #: Who it names — ``None`` once its poster withdrew.
    challenger_id: UUID | None
    club_name: str | None


@final
@dataclass(frozen=True, slots=True)
class PostingSlot:
    read: PostingRead
    cell: GridCell
    #: Best fit first.
    fits: tuple[SlotFit, ...]
    #: Home club first, then by hour.
    free_courts: tuple[FreeCourt, ...]
    #: Rescues the poster is offered, soonest first — the *Fill in* rows.
    rescues: tuple[SeatToFill, ...]
    #: Posts still filling they could join, soonest first.
    posts: tuple[PostToJoin, ...]
    club_names: Mapping[UUID, str]
    #: How far each club is from the poster — empty with no Location area.
    distances: Mapping[UUID, float]
    #: Everybody the sheet draws.
    people: Mapping[UUID, DeckPerson]


@final
class ReadPostingSlot:
    def __init__(
        self,
        *,
        posting: ReadPosting,
        forecasts: BalanceForecasts,
        people: DeckPeople,
        clubs: ClubNames,
        distances: ClubDistances,
        relations: ReaderRelations,
        clock: Clock,
    ) -> None:
        self._relations = relations
        self._posting = posting
        self._forecasts = forecasts
        self._people = people
        self._clubs = clubs
        self._distances = distances
        self._clock = clock

    async def execute(self, command: ReadPostingSlotCommand) -> PostingSlot:
        read = await self._posting.read(command.posting, now=instant(self._clock.now()))
        day, range_ = command.day, command.day_range
        cell = read.grid.cell(day, range_)
        free = read.grid.fits_free_at(cell)
        poster = read.poster.player_id
        forecasts = await self._forecasts.forecasts(
            [Sides(yours=(poster,), theirs=(fit.player_id,)) for fit in free],
            sport=read.sport,
        )
        order = {member.player_id: index for index, member in enumerate(read.members)}
        fits = tuple(
            sorted(
                (
                    SlotFit(player_id=fit.player_id, forecast=forecast)
                    for fit, forecast in zip(free, forecasts, strict=True)
                ),
                key=lambda fit: (
                    -fit.forecast.pct if fit.forecast is not None else 1,
                    order[fit.player_id],
                ),
            )
        )
        courts = read.grid.free_courts(day, range_)
        rescues = _in_the_cell(read.rescues, day, range_)
        posts = _in_the_cell(read.posts, day, range_)
        clubs = {
            *(court.hour.club_id for court in courts),
            *(game.club_id for game in rescues),
            *(post.club_id for post in posts),
        }
        names = await self._clubs.names_of(clubs)
        now = read.read_at
        return PostingSlot(
            read=read,
            cell=cell,
            fits=fits,
            free_courts=courts,
            rescues=tuple(
                SeatToFill(
                    game=game,
                    deadline=rescue_deadline(game, now=now),
                    fills_by_the_cut_off=fills_by_the_cut_off(game, now=now),
                    club_name=names.get(game.club_id),
                )
                for game in rescues
            ),
            posts=tuple(
                PostToJoin(
                    proposal=post,
                    challenger_id=challenger_of(post),
                    club_name=names.get(post.club_id),
                )
                for post in posts
            ),
            club_names=names,
            distances=await self._distances.from_player(poster, clubs),
            # The poster's friends carry the *friend* tag (`docs/adr/0202` §2).
            people=await with_the_readers_friends(
                await self._people.people(
                    sorted(
                        {
                            *(fit.player_id for fit in fits),
                            *(player for game in rescues for player in game.players),
                            *(player for post in posts for player in post.yeses),
                        },
                        key=str,
                    ),
                    sport=read.sport,
                ),
                reader=poster,
                relations=self._relations,
            ),
        )


_Game = TypeVar("_Game", BookedGame, Proposal)


def _in_the_cell(
    games: Sequence[_Game], day: date, range_: DayRange
) -> tuple[_Game, ...]:
    return tuple(
        sorted(
            (
                game
                for game in games
                if local_day(game.start) == day and range_of(game.start) is range_
            ),
            key=lambda game: game.start,
        )
    )


# --------------------------------------------------------------------------- #
# Post — you're In
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class Posted:
    """The post, In with its poster: how many versions it was dealt in, to how
    many people, and the seats open beside the poster."""

    proposal_id: UUID
    versions: int
    dealt_to: int
    open_seats: int


@final
class PostAGame:
    def __init__(
        self,
        *,
        posting: ReadPosting,
        guards: Guards,
        directory: ProposalDirectory,
        make: MakeProposal,
        tags: PlayersTags,
        played_with: PlayedWith,
        balance: BalanceRules,
        clock: Clock,
    ) -> None:
        self._posting = posting
        self._guards = guards
        self._directory = directory
        self._make = make
        self._tags = tags
        self._played_with = played_with
        self._balance = balance
        self._clock = clock

    async def execute(self, command: PostAGameCommand) -> Posted:
        now = instant(self._clock.now())
        read = await self._posting.read(command.posting, now=now)
        poster = read.poster
        hour = read.grid.court_hour(command.club_id, command.start)
        if hour is None:
            raise CourtHourNotForSale()
        # The three the button says, in its order: a method, two live posts,
        # the week.
        await self._guards.refuse_an_unchargeable_yes(poster.player_id)
        if await self._directory.live_posts_of(poster.player_id, now=now) >= LIVE_POSTS:
            raise LivePostsExhausted(cap=LIVE_POSTS)
        week = week_of(hour.start)
        if week in capped_weeks_of(poster, now=now):
            raise GamesPerWeekBooked(
                games_per_week=poster.limits.games_per_week, week=week.isoformat()
            )
        if hour_taken(hour.start, poster.booked):
            raise YouPlayThen()
        if not read.grid.fits_free_for(hour):
            raise NobodyFitsThen()
        # A For-fun post goes to the poster's best company first
        # (`docs/adr/0207` §1): the tags now, and who knows whom, of the poster
        # and of the members dealing it could name — free for its hour,
        # wanting the kind, within their Games & money, and whom it is for.
        tags: Mapping[UUID, Collection[SocialTag]] = {}
        known: frozenset[frozenset[UUID]] = frozenset()
        if read.kind is SearchMode.FOR_FUN:
            table = sorted(
                (
                    member.player_id
                    for member in read.members
                    if member.player_id == poster.player_id
                    or (
                        admitted(read.posted_for, member)
                        and may_play(
                            member,
                            read.kind,
                            start=hour.start,
                            share_grosze=hour.share_grosze,
                            capped=capped_weeks_of(member, now=now),
                        )
                    )
                ),
                key=str,
            )
            tags = await self._tags.tags_of(table)
            known = await self._played_with.known_pairs(table, among=table, now=now)
        versions = await asyncio.to_thread(
            versions_of_a_post,
            sport=read.sport,
            members=read.members,
            unfit=read.unfit,
            poster=poster.player_id,
            kind=read.kind,
            hour=hour,
            posted_for=read.posted_for,
            balance=self._balance,
            now=now,
            tags=tags,
            known=known,
        )
        proposal_id = await self._make.execute(
            MakeProposalCommand(
                pool_id=read.pool.id,
                origin=Origin.POST,
                poster_id=poster.player_id,
                sport=read.sport,
                kind=read.kind,
                club_id=hour.club_id,
                start=hour.start,
                versions=versions,
                posted_for=read.posted_for,
            )
        )
        return Posted(
            proposal_id=proposal_id,
            versions=len(versions),
            dealt_to=sum(len(version) for version in versions),
            open_seats=read.open_seats,
        )

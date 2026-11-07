"""**The friends card** and *Find a court* (#750; ``docs/adr/0202`` §5; the
friends mechanics §7.4–§7.6; the friends screens §7.2–§7.3).

Two reads of one line-up — the reader and the friends they seated on a
group's Friends tab — and **nothing recorded**: no proposal is made, nothing is
dealt and no court is held, so *no route makes a card itself* still stands.
Sending the card is the friends game's (#751), which reads the line-up exactly
as these do (``ReadFriendsLineUp``).

**The line-up's checks, in the order that says least** — every refusal names
nobody:

- the reader in the pool (``pool_not_found``, one code for no such pool and
  one they are not in) — the friends need not be: a friend who is not a member
  plays as a **guest**;
- the line-up the sport seats (``wrong_line_up_size``);
- each friend the reader's, now (``not_a_friend``) — before anything is read
  about them;
- a level in the sport for all of them, the reader too (``no_level``);
- no block between any two, either way round (``cannot_play_together``) —
  **the pair rule's block mask alone**: the level window, the kind's
  tolerance and gender preferences don't apply, because friends choose each
  other.

**The courts are the court source's** (``PoolClubs.offered`` over
``CourtHours.on_sale``, ``docs/adr/0202`` §7), one rule with the deck and
Post a game, read for the horizon from now; the rows and the one proposed are
``domain/friends_card.py``'s. **The card** adds the sides — the deck's
arrangements, the evenest by the engine's own forecast (``BalanceForecasts``),
or the sides sent — the overlap of the line-up's weeks at the court's hour,
and the club's cut-off for that hour, which the send sheet's *until Fri 10:00*
is.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Clock, Instant, Sport, instant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.proposals.application.commands import (
    FriendsLineUpCommand,
    ReadFriendsCardCommand,
)
from app.modules.proposals.application.members import ReadMembers
from app.modules.proposals.domain.deck import CardForecast, Sides, cut_off_of
from app.modules.proposals.domain.errors import (
    CannotPlayTogether,
    CourtHourIncomplete,
    CourtHourNotForSale,
    NoLevel,
    NotAFriend,
    PoolNotFound,
)
from app.modules.proposals.domain.friends_card import (
    HORIZON,
    CourtForFriends,
    LineUp,
    court_at,
    courts_for,
    line_up_of,
    proposed_court,
    the_sides,
    ways_to_stand,
)
from app.modules.proposals.domain.overlap import Overlap, overlap_of
from app.modules.proposals.domain.pool import Pool
from app.modules.proposals.domain.ports import (
    BalanceForecasts,
    ClubNames,
    ClubTerms,
    CourtHours,
    PlayerFit,
    Pools,
    ReaderRelations,
    WherePoolsPlay,
)
from app.modules.proposals.domain.proposer import Member, PoolClubs

# --------------------------------------------------------------------------- #
# The line-up, read once
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class FriendsLineUpRead:
    """One line-up at one instant: who, where the pool plays, and every court
    they could take."""

    pool: Pool
    line_up: LineUp
    #: The line-up as the proposer reads them, the reader first.
    people: tuple[Member, ...]
    clubs: PoolClubs
    #: Every court they could take, in *Find a court*'s order.
    courts: tuple[CourtForFriends, ...]
    read_at: Instant

    @property
    def sport(self) -> Sport:
        return self.line_up.sport

    @property
    def pool_id(self) -> UUID:
        return self.pool.id

    @property
    def home_club_id(self) -> UUID:
        return self.clubs.home_club_id


@final
class ReadFriendsLineUp:
    def __init__(
        self,
        *,
        pools: Pools,
        relations: ReaderRelations,
        members: ReadMembers,
        fit: PlayerFit,
        where: WherePoolsPlay,
        court_hours: CourtHours,
    ) -> None:
        self._pools = pools
        self._relations = relations
        self._members = members
        self._fit = fit
        self._where = where
        self._court_hours = court_hours

    async def read(
        self, command: FriendsLineUpCommand, *, now: Instant
    ) -> FriendsLineUpRead:
        reader = command.player_id
        pool = await self._pools.find(command.pool_id)
        # A stranger learns nothing about a group: one code for a pool that
        # does not exist and one they are not in.
        if pool is None or not await self._pools.members_among(pool, [reader]):
            raise PoolNotFound()
        line_up = line_up_of(reader, command.friend_ids, sport=command.sport)
        friends = await self._relations.friends_among(reader, line_up.friends)
        if len(friends) != len(line_up.friends):
            raise NotAFriend()
        people = tuple(
            await self._members.of(line_up.everybody, sport=line_up.sport, now=now)
        )
        if any(person.level is None for person in people):
            raise NoLevel()
        if await self._fit.blocked_pairs(line_up.everybody):
            raise CannotPlayTogether()
        clubs = await self._where.of(pool, now=now)
        if clubs is None:
            raise PoolNotFound()
        on_sale = await self._court_hours.on_sale(
            clubs.home_first, start=now, end=now + HORIZON, now=now
        )
        return FriendsLineUpRead(
            pool=pool,
            line_up=line_up,
            people=people,
            clubs=clubs,
            courts=courts_for(people, on_sale, clubs, sport=line_up.sport, now=now),
            read_at=now,
        )


# --------------------------------------------------------------------------- #
# Find a court
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class FriendsCourts:
    read: FriendsLineUpRead
    #: The home club's, and every club a row is at.
    club_names: Mapping[UUID, str]


@final
class ReadFriendsCourts:
    def __init__(
        self, *, line_up: ReadFriendsLineUp, clubs: ClubNames, clock: Clock
    ) -> None:
        self._line_up = line_up
        self._clubs = clubs
        self._clock = clock

    async def execute(self, command: FriendsLineUpCommand) -> FriendsCourts:
        read = await self._line_up.read(command, now=instant(self._clock.now()))
        return FriendsCourts(
            read=read,
            club_names=await self._clubs.names_of(
                {read.home_club_id, *(row.club_id for row in read.courts)}
            ),
        )


# --------------------------------------------------------------------------- #
# The card
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class FriendsCard:
    read: FriendsLineUpRead
    kind: SearchMode
    sides: Sides
    #: ``None`` where it cannot be read.
    forecast: CardForecast | None
    #: The court picked, or the one proposed — ``None`` with no court in the
    #: horizon.
    court: CourtForFriends | None
    #: The line-up's weeks, the court's hour ringed — ``None`` with no court.
    overlap: Overlap | None
    #: When the club's free cancellation ends for the court's game — what the
    #: send sheet holds the cover until.
    cut_off: Instant | None
    club_names: Mapping[UUID, str]


@final
class ReadFriendsCard:
    def __init__(
        self,
        *,
        line_up: ReadFriendsLineUp,
        forecasts: BalanceForecasts,
        clubs: ClubNames,
        terms: ClubTerms,
        clock: Clock,
    ) -> None:
        self._line_up = line_up
        self._forecasts = forecasts
        self._clubs = clubs
        self._terms = terms
        self._clock = clock

    async def execute(self, command: ReadFriendsCardCommand) -> FriendsCard:
        court_id, starts_at = command.court_id, command.starts_at
        if (court_id is None) != (starts_at is None):
            raise CourtHourIncomplete()
        now = instant(self._clock.now())
        read = await self._line_up.read(command.line_up, now=now)
        options = ways_to_stand(read.line_up)
        sides, forecast = the_sides(
            read.line_up,
            options,
            await self._forecasts.forecasts(options, sport=read.sport),
            partner=command.partner_id,
        )
        if court_id is None or starts_at is None:
            court = proposed_court(read.courts)
        else:
            court = court_at(read.courts, court_id, starts_at)
            if court is None:
                raise CourtHourNotForSale()
        return FriendsCard(
            read=read,
            kind=command.kind,
            sides=sides,
            forecast=forecast,
            court=court,
            overlap=None
            if court is None
            else overlap_of(
                [person.week for person in read.people],
                start=court.start,
                zone=CLUB_ZONE,
            ),
            cut_off=None if court is None else await self._cut_off(court, now=now),
            club_names=await self._clubs.names_of(
                {read.home_club_id, *([] if court is None else [court.club_id])}
            ),
        )

    async def _cut_off(self, court: CourtForFriends, *, now: Instant) -> Instant | None:
        terms = (await self._terms.of([court.club_id], now=now)).get(court.club_id)
        if terms is None:
            return None
        return cut_off_of(court.start, cut_off_hours=terms.cut_off_hours)

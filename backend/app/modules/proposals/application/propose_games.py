"""The proposer — the engine that builds games (#540; the mechanics §5,
§6.2–§6.3, §7; the screens C3).

**Continuously, per pool and sport**: the free court hours at a pool.s clubs ×
the members free and fitting for them → *Picked for you* cards; the seats a no
left and the unanswered seats of a pick at half In → next best fits; the cards
whose last court at their club and hour went → lost, and the people who were In
dealt a new card first — as are the people still in on a booked game its club
cancelled (#547), never at that club and hour, by the first run that finds them
an hour. What to do is decided by one pure batch (``domain/proposer.py``); this
reads its facts and applies it.

**Every fact is read live and once per pool**, one read per provider where the
provider allows: the pool's members and clubs, the games filling in it, every
hour its clubs sell, each member's Level and week (``PlayersInPlay``), Play
intent (``WantedKinds``), Games & money, booked games (``BookedGames``) and
live yeses, and the pair rule per kind (``PlayerFit``) over everybody the batch
could put on a card together. The batch itself is arithmetic over those, and it
runs **off the event loop** — a large pool's walk over every four is CPU the
requests being served beside it should not wait for.

**Applied through the dealer's own acts** (``making.py``) — a pick through
``MakeProposal``, a deal through ``DealVersion`` — so a card the proposer makes
is held to exactly what a seed's or a test's is: the court hour read off the
club again, the pool and the fit checked again. **One transaction per act**, as
the book-by sweep's, and whatever the world changed in between is **refused and
counted, never forced**: a club that stopped selling, a member who left, a pair
that stopped fitting, another process that made the same pick first — a pick's
id is its game (``domain/ids.py``), so two processes cannot deal one game
twice. Safe beside itself with no lock (``docs/adr/0092``).

**When**: on a cadence over every pool, and — sooner — over the pools a change
made due (``DueForProposing``): somebody joined, set their week, their intent or
their Games & money, a club changed what it sells, somebody swiped. The due set
is this process's memory and best effort; the cadence is the guarantee.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Sequence
from dataclasses import dataclass, field
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import BalanceRules
from app.kernel import Clock, Instant, Sport, instant
from app.modules.proposals.application.commands import (
    DealVersionCommand,
    MakeProposalCommand,
)
from app.modules.proposals.application.making import DealVersion, MakeProposal
from app.modules.proposals.application.members import ReadMembers
from app.modules.proposals.domain.deck import GAME_LENGTH, named_on
from app.modules.proposals.domain.ids import pick_id
from app.modules.proposals.domain.limits import (
    NEXT_BEST_FITS_PER_SEAT,
    VERSIONS_PER_PROPOSAL,
)
from app.modules.proposals.domain.pool import Pool
from app.modules.proposals.domain.ports import (
    CourtHours,
    PlayerFit,
    Pools,
    ProposalDirectory,
    ProposalRepository,
    UndecidedCharges,
    WherePoolsPlay,
)
from app.modules.proposals.domain.proposal import Origin, Proposal, Standing
from app.modules.proposals.domain.proposer import (
    HORIZON,
    Batch,
    CourtHourOnSale,
    Deal,
    Member,
    Pick,
    PoolClubs,
    propose,
)
from app.shared.domain.errors import AppError


@final
@dataclass(frozen=True, slots=True)
class Proposed:
    """What a run did: how many pools it read, the picks it made, the deals it
    added, the cards it found had lost their court hour — and how many acts the
    world had moved past by the time they were applied, which is not an error
    and is somebody's problem only when it is most of them."""

    pools: int = 0
    made: int = 0
    dealt: int = 0
    lost: int = 0
    #: Games their club cancelled whose people were dealt a new card first.
    redealt: int = 0
    refused: int = 0

    @property
    def anything(self) -> bool:
        """Whether the run changed anything, or was refused anything."""

        return bool(
            self.made or self.dealt or self.lost or self.redealt or self.refused
        )

    def __add__(self, other: "Proposed") -> "Proposed":
        return Proposed(
            pools=self.pools + other.pools,
            made=self.made + other.made,
            dealt=self.dealt + other.dealt,
            lost=self.lost + other.lost,
            redealt=self.redealt + other.redealt,
            refused=self.refused + other.refused,
        )


@final
class ProposeGames:
    def __init__(
        self,
        *,
        pools: Pools,
        where: WherePoolsPlay,
        court_hours: CourtHours,
        members: ReadMembers,
        directory: ProposalDirectory,
        proposals: ProposalRepository,
        fit: PlayerFit,
        make: MakeProposal,
        deal: DealVersion,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
        balance: BalanceRules,
    ) -> None:
        self._undecided = undecided
        self._pools = pools
        self._where = where
        self._court_hours = court_hours
        self._members_in_play = members
        self._directory = directory
        self._proposals = proposals
        self._fit = fit
        self._make = make
        self._deal = deal
        self._uow = uow
        self._clock = clock
        self._balance = balance

    async def every_pool(self) -> Sequence[UUID]:
        """Every pool there is, oldest first — what a sweep walks."""

        return [pool.id for pool in await self._pools.every()]

    async def pools_due(self, due: "Due") -> Sequence[UUID]:
        """The pools a set of changes made due, in one order on every process."""

        if due.everywhere:
            return await self.every_pool()
        pools = set(due.pools)
        for player_id in sorted(due.players):
            pools.update(pool.id for pool in await self._pools.of_player(player_id))
        for proposal_id in sorted(due.proposals):
            proposal = await self._proposals.load(proposal_id)
            if proposal is not None:
                pools.add(proposal.pool.id)
        return sorted(pools, key=str)

    async def execute(self, pool_id: UUID) -> Proposed:
        """One pool's batch, in every sport it plays, applied. A pool that no
        longer exists is nothing to do."""

        now = instant(self._clock.now())
        pool = await self._pools.find(pool_id)
        clubs = None if pool is None else await self._where.of(pool, now=now)
        if pool is None or clubs is None:
            return Proposed()
        members = await self._pools.members_of(pool)
        filling = await self._filling(pool, now)
        owed = await self._owed(pool, now)
        end = max(
            [now + HORIZON, *(proposal.start + GAME_LENGTH for proposal in filling)]
        )
        hours = await self._court_hours.on_sale(
            [*clubs.home_first, *(proposal.club_id for proposal in filling)],
            start=now,
            end=end,
            now=now,
        )
        held = await self._court_hours.held(
            [proposal.club_id for proposal in filling], start=now, end=end
        )
        sports = [
            sport
            for sport in Sport
            if any(hour.sport is sport for hour in hours)
            or any(proposal.sport is sport for proposal in (*filling, *owed))
        ]
        done = Proposed(pools=1)
        if not sports:
            return done
        limits, booked = await self._members_in_play.limits_and_games(members, now=now)
        for sport in sports:
            in_sport = [proposal for proposal in filling if proposal.sport is sport]
            batch = await self._batch(
                sport,
                members=await self._members_in_play.in_sport(
                    members, sport=sport, limits=limits, booked=booked
                ),
                clubs=clubs,
                hours=[hour for hour in hours if hour.sport is sport],
                held=[(club, at) for club, of, at in held if of is sport],
                filling=in_sport,
                owed=[proposal for proposal in owed if proposal.sport is sport],
                now=now,
            )
            done += await self._apply(pool, sport, batch, now)
        return done

    # ------------------------------------------------------------------ reads

    async def _filling(self, pool: Pool, now: Instant) -> list[Proposal]:
        filling: list[Proposal] = []
        for proposal_id in await self._directory.filling_in(pool.id, now=now):
            proposal = await self._proposals.load(proposal_id)
            if proposal is not None and proposal.standing_at(now) is Standing.FILLING:
                filling.append(proposal)
        return filling

    async def _owed(self, pool: Pool, now: Instant) -> list[Proposal]:
        """This pool's booked games a club cancelled whose people are still owed
        a new card first."""

        owed: list[Proposal] = []
        for proposal_id in await self._directory.owed_a_new_card_in(pool.id, now=now):
            proposal = await self._proposals.load(proposal_id)
            if proposal is not None and proposal.owes_a_new_card:
                owed.append(proposal)
        return owed

    async def _batch(
        self,
        sport: Sport,
        *,
        members: Sequence[Member],
        clubs: PoolClubs,
        hours: Sequence[CourtHourOnSale],
        held: Sequence[tuple[UUID, Instant]],
        filling: Sequence[Proposal],
        owed: Sequence[Proposal],
        now: Instant,
    ) -> Batch:
        # Everybody a card could hold: the members, and whoever is still In or
        # named on a game filling — a leaver included, since their yes stands
        # until the delivery of their leaving withdraws it — or In on a game
        # owed a new card.
        everybody = sorted(
            {
                *(member.player_id for member in members),
                *(
                    player
                    for proposal in filling
                    for player in (*proposal.yeses, *named_on(proposal))
                ),
                *(player for proposal in owed for player in proposal.owed_to),
            },
            key=str,
        )
        unfit: dict[SearchMode, frozenset[frozenset[UUID]]] = {}
        for kind in SearchMode:
            unfit[kind] = await self._fit.unfit_pairs(
                everybody, sport=sport, kind=kind, at=now
            )
        return await asyncio.to_thread(
            propose,
            sport=sport,
            members=members,
            unfit=unfit,
            clubs=clubs,
            hours=hours,
            held=held,
            filling=filling,
            owed=owed,
            balance=self._balance,
            now=now,
        )

    # ----------------------------------------------------------------- writes

    async def _apply(
        self, pool: Pool, sport: Sport, batch: Batch, now: Instant
    ) -> Proposed:
        done = Proposed()
        for proposal_id in batch.lost:
            done += await self._act(self._lose(proposal_id, now), Proposed(lost=1))
        #: Each owed game whose people's new card was made: the card's game and
        #: the pick it was made from.
        dealt_after: dict[UUID, tuple[UUID, Pick]] = {}
        for pick in batch.picks:
            game_id = _game_of(pool, sport, pick)
            made = await self._act(
                self._pick(pool, sport, pick, game_id), Proposed(made=1)
            )
            done += made
            if made.made and pick.after is not None:
                dealt_after[pick.after] = (game_id, pick)
        for proposal_id in batch.redealt:
            # Owed until its people's card is really on the table.
            if proposal_id in dealt_after:
                game_id, pick = dealt_after[proposal_id]
                done += await self._act(
                    self._redealt(proposal_id, game_id, pick.named, now),
                    Proposed(redealt=1),
                )
        for deal in batch.deals:
            done += await self._act(self._dealt(deal, now), Proposed(dealt=1))
        return done

    async def _act(self, act: Awaitable[bool], counted: Proposed) -> Proposed:
        """One act in its own transaction: ``counted`` when it recorded
        something, and a refusal when the world had moved past it."""

        try:
            recorded = await act
        except (AppError, EventStreamVersionConflict):
            await self._uow.rollback()
            return Proposed(refused=1)
        return counted if recorded else Proposed()

    async def _lose(self, proposal_id: UUID, now: Instant) -> bool:
        proposal = await self._proposals.load(proposal_id)
        if proposal is None or not proposal.lose_court_hour(at=now):
            return False
        await self._proposals.save(proposal)
        # A payment a player confirmed for it is let go with the card (#541).
        await self._undecided.release(proposal_id, keeping=(), at=now)
        await self._uow.commit()
        return True

    async def _redealt(
        self,
        proposal_id: UUID,
        card_id: UUID,
        named: tuple[UUID, ...],
        now: Instant,
    ) -> bool:
        """The people on a cancelled game were dealt their new card,
        ``card_id``: it owes nothing more, and says which card it was."""

        proposal = await self._proposals.load(proposal_id)
        if proposal is None or not proposal.redeal(
            card_id=card_id, named=named, at=now
        ):
            return False
        await self._proposals.save(proposal)
        await self._uow.commit()
        return True

    async def _pick(self, pool: Pool, sport: Sport, pick: Pick, game_id: UUID) -> bool:
        await self._make.execute(
            MakeProposalCommand(
                pool_id=pool.id,
                origin=Origin.PICK,
                poster_id=None,
                sport=sport,
                kind=pick.kind,
                club_id=pick.club_id,
                start=pick.start,
                versions=[pick.named],
                proposal_id=game_id,
            )
        )
        return True

    async def _dealt(self, deal: Deal, now: Instant) -> bool:
        """The deal, trimmed to what the game can still take — nobody already
        on it, and no more than its seats allow — since another process or a
        swipe may have moved it on since the batch read it."""

        proposal = await self._proposals.load(deal.proposal_id)
        if proposal is None or proposal.standing_at(now) is not Standing.FILLING:
            return False
        players = tuple(
            player for player in deal.players if not proposal.is_on_it(player)
        )
        if deal.into is None:
            if len(proposal.versions) >= VERSIONS_PER_PROPOSAL:
                return False
            players = players[: proposal.open_seats]
        else:
            players = players[: NEXT_BEST_FITS_PER_SEAT * proposal.open_seats]
        if not players:
            return False
        await self._deal.execute(
            DealVersionCommand(
                proposal_id=deal.proposal_id,
                player_ids=players,
                into_version=deal.into,
            )
        )
        return True


def _game_of(pool: Pool, sport: Sport, pick: Pick) -> UUID:
    """The game a pick is made as — its id, the same on every process."""

    return pick_id(
        pool_id=pool.id,
        sport=sport,
        kind=pick.kind,
        club_id=pick.club_id,
        start=pick.start,
        named=pick.named,
    )


# --------------------------------------------------------------------------- #
# What made a pool due
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class Due:
    """The changes since the proposer last looked: pools, players and games
    they touched — or everywhere, for a change to what a club sells."""

    pools: frozenset[UUID] = frozenset()
    players: frozenset[UUID] = frozenset()
    proposals: frozenset[UUID] = frozenset()
    everywhere: bool = False

    @property
    def anything(self) -> bool:
        return bool(self.everywhere or self.pools or self.players or self.proposals)


@final
@dataclass
class DueForProposing:
    """**This process's memory of what changed**, filled by the outbox's
    subscriber as it delivers and emptied by the proposer's short tick — so a
    change is dealt from in seconds rather than at the next sweep. Best effort
    and nothing more: a restart forgets it, another process's delivery fills its
    own, and the sweep over every pool is what guarantees a change is seen."""

    _pools: set[UUID] = field(default_factory=set)
    _players: set[UUID] = field(default_factory=set)
    _proposals: set[UUID] = field(default_factory=set)
    _everywhere: bool = False

    def pool(self, pool_id: UUID) -> None:
        self._pools.add(pool_id)

    def player(self, player_id: UUID) -> None:
        self._players.add(player_id)

    def proposal(self, proposal_id: UUID) -> None:
        self._proposals.add(proposal_id)

    def everywhere(self) -> None:
        self._everywhere = True

    def take(self) -> Due:
        """Everything noted since the last take, and forget it."""

        due = Due(
            pools=frozenset(self._pools),
            players=frozenset(self._players),
            proposals=frozenset(self._proposals),
            everywhere=self._everywhere,
        )
        self._pools.clear()
        self._players.clear()
        self._proposals.clear()
        self._everywhere = False
        return due

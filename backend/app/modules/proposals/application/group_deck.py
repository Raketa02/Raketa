"""A group's **Games** tab: the reader's deck in one sport and segment, and what
the tab says around it (the mechanics §3, §6.6, §7, §8; the screens A1, A2).

**A read, recorded nowhere.** A deck is a projection of the proposals dealt to
the reader, recomputed at every read (``docs/adr/0189`` §5): nothing here
writes, and a card's forecast is computed for the reader's own version now.

**The order of the questions is the cost of each.** The reader's own facts first
— the pool they must be in, the kinds they want, their Games & money and the
games they have booked — then the proposals dealt to them, filtered by those
before anybody else is read about; then **one read per provider over the union
of every card left**: who is still in the pool, which pairs on them fit (per kind,
since the level window is the kind's), the forecasts of every arrangement, and
the people. Nothing is asked per card.

**The filters** (§4.1, §5.3, §6.6): a kind the reader's Play intent does not
want, a share above *most I'll pay*, a week at their games per week, an hour
they already have a game at, and a club that no longer sells are never dealt;
**blocks, gender preferences and the level gates** are the matcher's pair rule,
through ``PlayerFit`` — a card with somebody In the reader does not fit is
withheld, and a name that does not fit them or anybody on the card is left off
it (``domain/deck.py``). On a *Mixed pairs* post (#546) a reader who would be
a third of their gender is not dealt it, and the sides stand a man and a woman
each — the genders read only for such a card, and never said.

**Seat open cards** (#545; the mechanics §8.1, §10.1): a booked game in the
pool that lost a player is dealt to its **best fits** — the members it is offered
to whose game with them in the seat is forecast most even, three per open seat
(``application/rescues.py``) — as long as the reader has not said no to it. The
reader sits in the seat that opened first; the players read *paid*.

**Around the deck**: a count per segment the reader's intent shows — none while
they have declared nothing, which is the question that replaces the deck — the
Games badge (cards with somebody already In, across those segments — a rescue's
players have paid, and are not In), and the weeks at the cap, so the tab can say
*your games this week are booked*.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Clock, Instant, Sport, instant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.proposals.application.commands import ReadGroupDeckCommand
from app.modules.proposals.application.members import genders_of
from app.modules.proposals.application.rescues import RescueOffers
from app.modules.proposals.domain.deck import (
    CappedWeek,
    DeckCard,
    ReadersView,
    arrangements,
    capped_weeks,
    card_of,
    challenger_of,
    dealt_in_order,
    evenest,
    hour_taken,
    may_stand_on,
    named_on,
    standing_for,
    view_of,
    week_of,
    week_window,
    weeks_ahead,
)
from app.modules.proposals.domain.errors import PoolNotFound
from app.modules.proposals.domain.overlap import overlap_of
from app.modules.proposals.domain.rescues import card_of_a_rescue
from app.modules.proposals.domain.ports import (
    BalanceForecasts,
    BookedGames,
    ClubNames,
    ClubTerms,
    DeckPeople,
    DeckPerson,
    GamesAndMoneyRepository,
    PlayerFit,
    PlayersInPlay,
    Pools,
    ProposalDirectory,
    ProposalRepository,
    WantedKinds,
)
from app.modules.player_profile.domain.gender import Gender
from app.modules.proposals.domain.pool import Pool
from app.modules.proposals.domain.post import Who
from app.modules.proposals.domain.proposal import Proposal


@final
@dataclass(frozen=True, slots=True)
class DeckSegment:
    """One side of the *Competitive · N / For fun · N* switch."""

    kind: SearchMode
    count: int


@final
@dataclass(frozen=True, slots=True)
class GroupDeck:
    pool_id: UUID
    sport: Sport
    kind: SearchMode
    #: The segments the reader's intent shows, Competitive first — **none**
    #: while they have declared no intent for the sport.
    segments: tuple[DeckSegment, ...]
    #: Cards with somebody already In with the reader, across those segments —
    #: a rescue's players have paid, and are not In.
    games_badge: int
    games_per_week: int
    capped_weeks: tuple[CappedWeek, ...]
    #: The requested segment's cards, in the order they are dealt.
    cards: tuple[DeckCard, ...]
    #: Everybody those cards draw, the challengers included.
    people: Mapping[UUID, DeckPerson]
    club_names: Mapping[UUID, str]


@final
class ReadGroupDeck:
    def __init__(
        self,
        *,
        pools: Pools,
        directory: ProposalDirectory,
        proposals: ProposalRepository,
        settings: GamesAndMoneyRepository,
        wanted: WantedKinds,
        booked: BookedGames,
        terms: ClubTerms,
        fit: PlayerFit,
        forecasts: BalanceForecasts,
        people: DeckPeople,
        clubs: ClubNames,
        offers: RescueOffers,
        players: PlayersInPlay,
        clock: Clock,
    ) -> None:
        self._offers = offers
        self._players = players
        self._pools = pools
        self._directory = directory
        self._proposals = proposals
        self._settings = settings
        self._wanted = wanted
        self._booked = booked
        self._terms = terms
        self._fit = fit
        self._forecasts = forecasts
        self._people = people
        self._clubs = clubs
        self._clock = clock

    async def execute(self, command: ReadGroupDeckCommand) -> GroupDeck:
        now = instant(self._clock.now())
        reader, sport = command.player_id, command.sport
        pool = await self._pools.find(command.pool_id)
        # A stranger learns nothing about a group's games: one code for a pool
        # that does not exist and one they are not in.
        if pool is None or not await self._pools.members_among(pool, [reader]):
            raise PoolNotFound()

        wanted = await self._wanted.of(reader, sport=sport)
        shown = tuple(kind for kind in SearchMode if wanted and kind in wanted)
        limits = await self._settings.load(reader)
        weeks = weeks_ahead(now)
        start, end = week_window(weeks)
        booked = await self._booked.starts_of(reader, start=start, end=end)
        capped = capped_weeks(weeks, booked, games_per_week=limits.games_per_week)
        at_the_cap = {week.starts_on for week in capped}

        dealt = await self._dealt(reader, command, now)
        terms = await self._terms.of({p.club_id for p in dealt}, now=now)
        candidates = [
            proposal
            for proposal in dealt
            if proposal.kind in shown
            and limits.shows(share_grosze=proposal.share_grosze)
            and week_of(proposal.start) not in at_the_cap
            and not hour_taken(proposal.start, booked)
            and proposal.club_id in terms
        ]

        views, genders = await self._views(pool, reader, sport, candidates, now)
        options = [
            standing_for(
                arrangements(
                    reader,
                    (*view.in_, *view.others),
                    seats_per_side=proposal.seats_per_side,
                ),
                who=proposal.who,
                genders=genders,
            )
            for proposal, view in views
        ]
        forecasts = await self._forecasts.forecasts(
            [option for choices in options for option in choices], sport=sport
        )
        rescues = await self._offers.dealt_to(
            pool, reader, sport=sport, kinds=shown, now=now
        )
        people = await self._people.people(
            {
                *(player for _, view in views for player in view.people),
                *(
                    challenger
                    for proposal, _ in views
                    if (challenger := challenger_of(proposal)) is not None
                ),
                *(player for rescue in rescues for player in rescue.game.players),
                *([reader] if rescues else []),
            },
            sport=sport,
        )

        cards: list[DeckCard] = []
        read = 0
        for (proposal, view), choices in zip(views, options, strict=True):
            sides, forecast = evenest(choices, forecasts[read : read + len(choices)])
            read += len(choices)
            cards.append(
                card_of(
                    proposal,
                    view,
                    sides=sides,
                    forecast=forecast,
                    weeks=[people[player].week for player in view.people],
                    terms=terms[proposal.club_id],
                    now=now,
                )
            )

        for rescue in rescues:
            game = rescue.game
            cards.append(
                card_of_a_rescue(
                    game,
                    sides=rescue.sides,
                    forecast=rescue.forecast,
                    overlap=overlap_of(
                        [people[player].week for player in (reader, *game.players)],
                        start=game.start,
                        zone=CLUB_ZONE,
                    ),
                    now=now,
                )
            )

        segments = {
            kind: dealt_in_order(card for card in cards if card.kind is kind)
            for kind in shown
        }
        dealt_now = segments.get(command.kind, ())
        return GroupDeck(
            pool_id=pool.id,
            sport=sport,
            kind=command.kind,
            segments=tuple(
                DeckSegment(kind=kind, count=len(segments[kind])) for kind in shown
            ),
            games_badge=sum(1 for kind in shown for card in segments[kind] if card.in_),
            games_per_week=limits.games_per_week,
            capped_weeks=capped,
            cards=dealt_now,
            people={
                player: person
                for player, person in people.items()
                if any(
                    player in card.people or player == card.challenger_id
                    for card in dealt_now
                )
            },
            club_names=await self._clubs.names_of({card.club_id for card in dealt_now}),
        )

    async def _dealt(
        self, reader: UUID, command: ReadGroupDeckCommand, now: Instant
    ) -> list[Proposal]:
        dealt: list[Proposal] = []
        for proposal_id in await self._directory.dealt_to(
            reader, pool_id=command.pool_id, sport=command.sport, now=now
        ):
            proposal = await self._proposals.load(proposal_id)
            if proposal is not None:
                dealt.append(proposal)
        return dealt

    async def _views(
        self,
        pool: Pool,
        reader: UUID,
        sport: Sport,
        candidates: Sequence[Proposal],
        now: Instant,
    ) -> tuple[list[tuple[Proposal, ReadersView]], dict[UUID, Gender | None]]:
        """Each candidate as the reader would see it, with the live reads every
        card shares: who is still in the pool, which pairs fit — and, where a
        *Mixed pairs* post is among them, everybody's gender on it."""

        in_the_pool = await self._pools.members_among(
            pool, {player for proposal in candidates for player in named_on(proposal)}
        )
        unfit: dict[SearchMode, frozenset[frozenset[UUID]]] = {}
        # In the enum's order rather than a set's, so the reads run alike on
        # every process (docs/adr/0105).
        kinds = [kind for kind in SearchMode if any(p.kind is kind for p in candidates)]
        for kind in kinds:
            everybody = {
                reader,
                *(
                    player
                    for proposal in candidates
                    if proposal.kind is kind
                    for player in (*proposal.yeses, *named_on(proposal))
                ),
            }
            unfit[kind] = await self._fit.unfit_pairs(
                sorted(everybody), sport=sport, kind=kind, at=now
            )
        genders = await genders_of(
            self._players,
            {
                player
                for proposal in candidates
                if proposal.who is Who.MIXED_PAIRS
                for player in (reader, *proposal.yeses, *named_on(proposal))
            },
            sport=sport,
        )
        views: list[tuple[Proposal, ReadersView]] = []
        for proposal in candidates:
            view = view_of(
                proposal,
                reader,
                unfit=unfit[proposal.kind],
                in_the_pool=in_the_pool,
                now=now,
                may_stand=may_stand_on(proposal, genders),
            )
            if view is not None:
                views.append((proposal, view))
        return views, genders

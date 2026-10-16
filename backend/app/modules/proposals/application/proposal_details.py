"""A game still filling, for anybody it was dealt to (#542; the mechanics §14.2;
the screens A4.2).

**The deck's card, as a screen, for every reader the deck does not serve**: a
card's *i*, a You're In row — which the deck never deals, since the reader is
In — a payment to confirm, and a game the reader already answered. Who is drawn
follows who is reading (``domain/details.py``); the sides are the evenest
arrangement **the engine's own forecast** gives with the reader on their own
side, exactly as the deck draws them; the overlap grid is the people drawn; WHERE
is the club and its distance from the reader, never a court number, which is
given at booking; the money row is the share and the book-by. The status says
*filling*, or how it ended — a filled game's booking has its id — and the
actions are what the reader may do now. **Waiting for one payment, it says until
when** (#625, Q111), and to the payer that the payment is theirs.

**A read, recorded nowhere**, against one instant, with one read per provider.

**Refused with one code** — ``proposal_not_found`` — for a proposal that does
not exist, one that is nothing to the reader, one in a pool they are no longer
in, and one with somebody In they may not share a court with while they are not
In themselves: the deck withholds that card, and its details are the same card.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, instant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.proposals.application.members import genders_on
from app.modules.proposals.domain.deck import (
    CardForecast,
    CardType,
    Sides,
    arrangements,
    card_type,
    challenger_of,
    cut_off_passed,
    evenest,
    may_stand_on,
    named_on,
    standing_for,
)
from app.modules.proposals.domain.details import (
    DetailsView,
    ProposalStatus,
    ReaderAction,
    actions_for,
    details_view,
    status_of_proposal,
)
from app.modules.proposals.domain.errors import ProposalNotFound
from app.modules.proposals.domain.overlap import Overlap, overlap_of
from app.modules.proposals.domain.ports import (
    BalanceForecasts,
    ClubDistances,
    ClubNames,
    ClubTerms,
    CourtKinds,
    DeckPeople,
    DeckPerson,
    PlayerFit,
    PlayersInPlay,
    Pools,
    ProposalRepository,
)
from app.modules.proposals.domain.proposal import Paying, Proposal, Reopened, TimeTo


@final
@dataclass(frozen=True, slots=True)
class ProposalDetails:
    proposal: Proposal
    read_at: Instant
    type: CardType
    #: Who a challenge names; ``None`` on a pick and once the poster withdrew.
    challenger_id: UUID | None
    status: ProposalStatus
    actions: tuple[ReaderAction, ...]
    view: DetailsView
    sides: Sides
    forecast: CardForecast | None
    overlap: Overlap
    #: Why the reader's seat reopened, and the payment to confirm — ``None``
    #: unless the last yes reopened it.
    reopened: Reopened | None
    #: The reader's own refused share and their time to pay, while it runs —
    #: ``None`` for anybody else (#625, #626).
    paying: Paying | None
    #: When the payment the game waits for is due — *Waiting for one payment ·
    #: until 14:40* — while it waits for one; ``None`` otherwise (Q111).
    pay_by: Instant | None
    #: What that time is for — to fix the card, or to pay (#638) — with
    #: ``pay_by``.
    time_to: TimeTo | None
    #: The club's cut-off has already passed for this game. ``False`` for a
    #: club no longer selling.
    no_free_cancellation: bool
    #: The kind of court the card promises — *Indoor*, *Outdoor*, or ``None``
    #: when the free courts it could be booked on are of mixed kinds (Q122).
    indoor: bool | None
    club_name: str | None
    distance_km: float | None
    people: Mapping[UUID, DeckPerson]


@final
class ReadProposalDetails:
    def __init__(
        self,
        *,
        pools: Pools,
        proposals: ProposalRepository,
        fit: PlayerFit,
        forecasts: BalanceForecasts,
        people: DeckPeople,
        terms: ClubTerms,
        kinds: CourtKinds,
        clubs: ClubNames,
        distances: ClubDistances,
        players: PlayersInPlay,
        clock: Clock,
    ) -> None:
        self._players = players
        self._pools = pools
        self._proposals = proposals
        self._fit = fit
        self._forecasts = forecasts
        self._people = people
        self._terms = terms
        self._kinds = kinds
        self._clubs = clubs
        self._distances = distances
        self._clock = clock

    async def execute(self, proposal_id: UUID, reader: UUID) -> ProposalDetails:
        now = instant(self._clock.now())
        proposal = await self._proposals.load(proposal_id)
        if proposal is None or not proposal.is_on_it(reader):
            raise ProposalNotFound()
        pool = await self._pools.find(proposal.pool.id)
        if pool is None or not await self._pools.members_among(pool, [reader]):
            raise ProposalNotFound()

        named = named_on(proposal)
        in_the_pool = await self._pools.members_among(pool, named)
        unfit = await self._fit.unfit_pairs(
            sorted({reader, *proposal.yeses, *named}),
            sport=proposal.sport,
            kind=proposal.kind,
            at=now,
        )
        genders = await genders_on(
            self._players, proposal, {reader, *proposal.yeses, *named}
        )
        view = details_view(
            proposal,
            reader,
            unfit=unfit,
            in_the_pool=in_the_pool,
            now=now,
            may_stand=may_stand_on(proposal, genders),
        )
        if view is None:
            raise ProposalNotFound()

        options = standing_for(
            arrangements(
                reader, view.beside_the_reader, seats_per_side=proposal.seats_per_side
            ),
            who=proposal.who,
            genders=genders,
        )
        sides, forecast = evenest(
            options, await self._forecasts.forecasts(options, sport=proposal.sport)
        )
        challenger = challenger_of(proposal)
        people = await self._people.people(
            {*view.people, *(() if challenger is None else (challenger,))},
            sport=proposal.sport,
        )
        terms = (await self._terms.of([proposal.club_id], now=now)).get(
            proposal.club_id
        )
        names = await self._clubs.names_of([proposal.club_id])
        distances = await self._distances.from_player(reader, [proposal.club_id])
        status = status_of_proposal(proposal, now=now)
        # The kind a card promises is read off the free courts only while the
        # game still fills: once booked, its court and kind are the booking's
        # (``GET /bookings/{id}``), and the courts still free say nothing.
        hour = (proposal.club_id, proposal.sport, proposal.start)
        kinds = (
            await self._kinds.of([hour])
            if status in (ProposalStatus.FILLING, ProposalStatus.WAITING_FOR_A_PAYMENT)
            else {}
        )
        return ProposalDetails(
            proposal=proposal,
            read_at=now,
            type=card_type(proposal),
            challenger_id=challenger,
            status=status,
            actions=actions_for(proposal, reader, now=now),
            view=view,
            sides=sides,
            forecast=forecast,
            overlap=overlap_of(
                [people[player].week for player in view.people],
                start=proposal.start,
                zone=CLUB_ZONE,
            ),
            reopened=proposal.reopened.get(reader),
            paying=proposal.paying.get(reader),
            pay_by=(
                proposal.pay_by
                if status is ProposalStatus.WAITING_FOR_A_PAYMENT
                else None
            ),
            time_to=(
                proposal.time_to
                if status is ProposalStatus.WAITING_FOR_A_PAYMENT
                else None
            ),
            no_free_cancellation=terms is not None
            and cut_off_passed(
                proposal.start, cut_off_hours=terms.cut_off_hours, now=now
            ),
            indoor=kinds.get(hour),
            club_name=names.get(proposal.club_id),
            distance_km=distances.get(proposal.club_id),
            people=people,
        )
